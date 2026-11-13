import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from recon.data import prepare, stratify, validate
from recon.parsing import answer, parse_verdict, parse_generation
from recon.pipeline import adapt, run
from recon.providers import Client, Reply

PASS = json.dumps({'format_check': 'PASS', 'logical_equivalence_confirmed': True, 'feedback': ''})
FAIL = json.dumps({'format_check': 'FAIL', 'logical_equivalence_confirmed': False, 'feedback': 'CLUE 1: TYPE_CHANGED'})
# Artificial sentinel strings, no benchmark data.
GEN = '<target_domain>test-domain</target_domain><mapping>x - y</mapping><adapted_puzzle><context>test</context><clues>test</clues><question>test</question></adapted_puzzle>'
ROW = {'Puzzle_Number': 'test', 'Question_Number': 'Q1', 'Sample': '<context>test-only</context>', 'Answer': 'B'}


class Fake:
    model = 'test-model'
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []
    def call(self, system, user):
        self.calls.append((system, user))
        return Reply(next(self.values))


class Tests(unittest.TestCase):
    def test_answer(self):
        self.assertIsNone(answer('A could be possible, B could also work'))
        self.assertEqual(answer('Answer: B\nFinal Answer: D'), 'D')
        self.assertIsNone(answer('<think>Answer: C</think>unfinished'))
        self.assertIsNone(answer('<think>Answer: C'))
        self.assertEqual(answer('<format><answer>[C]</answer></format>'), 'C')

    def test_verdict(self):
        self.assertTrue(parse_verdict('```json\n' + PASS + '\n```')['logical_equivalence_confirmed'])
        for text in ['{"format_check":"PASS","logical_equivalence_confirmed":"true","feedback":""}', PASS + ' extra', PASS.replace('PASS', 'FAIL')]:
            with self.assertRaises(ValueError):
                parse_verdict(text)

    def test_refinement(self):
        gen, judge = Fake([GEN, GEN]), Fake([FAIL, PASS])
        result = adapt(ROW, gen, judge, {})
        self.assertEqual(result['final_outcome'], 'equivalent')
        self.assertEqual(result['iterations_used'], 2)
        self.assertIn('CLUE 1: TYPE_CHANGED', gen.calls[1][1])
        self.assertEqual(len(result['rounds']), 2)

    def test_parse_exhaustion(self):
        result = adapt(ROW, Fake([GEN]), Fake(['invalid'] * 3), {})
        self.assertEqual(result['final_outcome'], 'judge_failed')
        self.assertIsNone(result['final_equivalence'])
        self.assertEqual(result['iterations_used'], 1)

    def test_missing_generation(self):
        result = adapt(ROW, Fake(['missing'] * 3), Fake([PASS] * 3), {})
        self.assertEqual(result['final_outcome'], 'not_equivalent')

    def test_resume(self):
        config = {'generator': {'provider': 'ollama', 'model': 'test'}}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'run.jsonl'
            fake = Fake(['B'])
            frame = pd.DataFrame([ROW])
            run(frame, config, path, stage='solve', client_factory=lambda c: fake)
            records = run(frame, config, path, stage='solve', resume=True, client_factory=lambda c: fake)
            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(records[0]['Model_Answer'], 'B')
            with self.assertRaises(ValueError):
                run(frame.assign(Sample='changed'), config, path, stage='solve', resume=True)

    def test_prepare_and_strata(self):
        frame = prepare(pd.DataFrame([{'Puzzle_Number': 1, 'Context': 'test', 'Clues': 'test', 'Q1': 'test', 'Q2': ''}]))
        self.assertEqual(len(frame), 1)
        self.assertIn('<question>', frame.iloc[0].Sample)
        points = pd.DataFrame({'Solved_Percentile': [0, 29, 30, 59, 60, 100]})
        self.assertEqual(len(stratify(points, {'Hard': 1, 'Medium': 1, 'Easy': 1}, 42)), 3)
        variants = pd.DataFrame([{**ROW, 'adaptation_id': i} for i in range(2)])
        validate(variants)

    def test_pair_selection_cli(self):
        from recon.__main__ import main
        import sys
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            directory = Path(directory)
            original = pd.DataFrame([{**ROW, 'Solved_Percentile': 20}])
            pool = pd.DataFrame([{**ROW, 'Solved_Percentile': 20, 'final_outcome': 'equivalent', 'final_adapted_puzzle': GEN, 'generator_model': 'test'}])
            original.to_csv(directory / 'original.csv', index=False)
            pool.to_csv(directory / 'pool.csv', index=False)
            args = ['recon', 'select-pairs', '--input', str(directory / 'pool.csv'), '--originals', str(directory / 'original.csv'), '--seed', '42', '--counts', 'Hard:1', '--output', str(directory / 'pairs.csv')]
            with patch.object(sys, 'argv', args):
                main()
            with patch.object(sys, 'argv', ['recon', 'split-pairs', '--input', str(directory / 'pairs.csv'), '--output', str(directory / 'split')]):
                main()
            old = pd.read_csv(directory / 'split.original.csv')
            new = pd.read_csv(directory / 'split.adapted.csv')
            self.assertEqual(old.iloc[0].Sample, ROW['Sample'])
            self.assertEqual(new.iloc[0].Sample, GEN)
            self.assertEqual(old.iloc[0].adaptation_id, new.iloc[0].adaptation_id)

    def test_canonical_solver_prompts_across_providers(self):
        from recon.pipeline import ROOT, prompt
        self.assertEqual({p.stem for p in (ROOT / 'prompts').glob('*.txt')},
                         {'zero_shot', 'cot', 'generator', 'judge', 'answer_audit', 'judge_audit'})
        self.assertFalse((ROOT / 'prompts/archive').exists())
        for path in (ROOT / 'configs').rglob('*.json'):
            config = json.loads(path.read_text(encoding='utf-8'))
            self.assertNotIn('prompt_prefix', config)
            if 'solve' not in config:
                continue
            for mode, name in [('zs', 'zero_shot'), ('cot', 'cot')]:
                with self.subTest(config=path.name, mode=mode):
                    fake = Fake(['B'])
                    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                        run(pd.DataFrame([ROW]), config, Path(directory) / 'run.jsonl',
                            stage='solve', mode=mode, client_factory=lambda c: fake)
                    self.assertEqual(fake.calls[0][0], prompt(name))
        self.assertIn('formatting_only|equivalence_issue|mixed|inconclusive', prompt('judge_audit'))
        self.assertNotIn('"n/a"', prompt('judge_audit'))

    def test_ollama_wire_format(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"message":{"content":"B","thinking":"trace"},"done_reason":"stop"}'
        with patch('urllib.request.urlopen', return_value=Response()) as urlopen:
            client = Client({'provider': 'ollama', 'model': 'test', 'think': True, 'max_tokens': 10})
            reply = client.call('system', 'user')
            body = json.loads(urlopen.call_args.args[0].data)
            self.assertTrue(body['think'])
            self.assertNotIn('thinking', body['options'])
            self.assertEqual(reply.reasoning, 'trace')


if __name__ == '__main__':
    unittest.main()
