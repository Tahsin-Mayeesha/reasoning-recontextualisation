"""Full CLI workflow using a real synthetic input and simulated Ollama HTTP responses."""
import importlib.util
import io
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from recon.__main__ import main
from recon.pipeline import ROOT, prompt

spec = importlib.util.spec_from_file_location('sample_example', ROOT / 'examples/create_sample.py')
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)

ADAPTED = '''<context>
Three books, Atlas, Brook, and Comet, occupy positions 1, 2, and 3 on a shelf.
Each book occupies exactly one position, and no position contains more than one book.
</context>
<clues>
1. Atlas is somewhere before Brook.
2. Comet is immediately after Atlas.
</clues>
<question>
Which of the following must be the order of the books, from position 1 to position 3?
(A) Atlas, Brook, Comet
(B) Brook, Atlas, Comet
(C) Comet, Atlas, Brook
(D) Atlas, Comet, Brook
(E) Brook, Comet, Atlas
</question>'''
GEN = ('<target_domain>name: Bookshelf arrangement\ncontainers: shelf positions\nitems: books\n'
       'identifiers: Atlas, Brook, Comet</target_domain>\n'
       '<mapping>Amber -> Atlas\nBirch -> Brook\nCedar -> Comet</mapping>\n'
       '<adapted_puzzle>' + ADAPTED + '</adapted_puzzle>')
FAIL = json.dumps({'format_check': 'FAIL', 'logical_equivalence_confirmed': False,
                   'feedback': 'CLUE 2: DIRECTION_FLIPPED -- immediately before must be immediately after'})
PASS = json.dumps({'format_check': 'PASS', 'logical_equivalence_confirmed': True, 'feedback': ''})


class SampleWorkflow(unittest.TestCase):
    def test_complete_sample_workflow(self):
        # Independently verify the synthetic puzzle, rather than trusting the gold label.
        orders = [p for p in itertools.permutations(['Amber', 'Birch', 'Cedar'])
                  if p.index('Amber') < p.index('Birch') and p.index('Cedar') == p.index('Amber') + 1]
        self.assertEqual(orders, [('Amber', 'Cedar', 'Birch')])
        requests = []
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            work = Path(directory)
            source = work / 'sample.csv'
            with patch.object(sys, 'argv', ['create_sample', '--single', '--output', str(source)]):
                sample.main()

            def cli(*args):
                with patch.object(sys, 'argv', ['recon', *map(str, args)]):
                    main()

            def responses(*texts):
                values = iter(texts)
                def respond(request, **kwargs):
                    body = json.loads(request.data)
                    self.assertEqual(request.full_url, 'http://localhost:11434/api/chat')
                    self.assertIn(body['messages'][0]['content'], [prompt(n) for n in ['generator', 'judge', 'zero_shot', 'cot']])
                    self.assertNotIn('Solved_Percentile', body['messages'][1]['content'])
                    requests.append(body)
                    return io.BytesIO(json.dumps({'message': {'content': next(values)}, 'done_reason': 'stop'}).encode())
                return patch('urllib.request.urlopen', side_effect=respond)

            config = ROOT / 'configs/ollama/qwen.json'
            with responses('<format>[D]</format>'):
                cli('solve', '--input', source, '--config', config, '--output', work / 'solve.jsonl')
            cli('summarize', '--input', work / 'solve.jsonl', '--output', work / 'summary.json')
            self.assertEqual(json.loads((work / 'summary.json').read_text())['accuracy'], 1.0)
            # Simulate an initial direction error, judge feedback, then a valid repair.
            with responses(GEN.replace('Comet is immediately after Atlas', 'Comet is immediately before Atlas'), FAIL, GEN, PASS):
                cli('adapt', '--input', source, '--config', config, '--output', work / 'adapt.jsonl')
            record = json.loads((work / 'adapt.jsonl').read_text())
            self.assertEqual(record['final_outcome'], 'equivalent')
            self.assertEqual(record['iterations_used'], 2)
            self.assertIn('DIRECTION_FLIPPED', requests[3]['messages'][1]['content'])
            cli('export', '--input', work / 'adapt.jsonl', '--output', work / 'adapt.csv')
            cli('select-pairs', '--input', work / 'adapt.csv', '--originals', source,
                '--seed', '42', '--size', '1', '--output', work / 'pairs.csv')
            cli('split-pairs', '--input', work / 'pairs.csv', '--output', work / 'paired')
            pair = pd.read_csv(work / 'paired.adapted.csv')
            self.assertEqual(pair.iloc[0].Sample, ADAPTED)
            with responses('<format><reasoning>Atlas, Comet, Brook.</reasoning><answer>D</answer></format>'):
                cli('solve', '--input', work / 'paired.adapted.csv', '--config', config,
                    '--mode', 'cot', '--output', work / 'adapted_solve.jsonl')
            cli('summarize', '--input', work / 'adapted_solve.jsonl', '--output', work / 'adapted_summary.json')
            self.assertEqual(json.loads((work / 'adapted_summary.json').read_text())['accuracy'], 1.0)
            # Resume must perform no further HTTP calls.
            with patch('urllib.request.urlopen', side_effect=AssertionError('Unexpected resume call')):
                cli('solve', '--input', source, '--config', config, '--output', work / 'solve.jsonl', '--resume')
            self.assertEqual(len(requests), 6)


if __name__ == '__main__':
    unittest.main()
