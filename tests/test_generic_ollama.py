"""Arbitrary Ollama chat tags and independent roles through the real CLI/transport."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from recon.__main__ import main
from recon.config import thinking
from recon.pipeline import ROOT
from test_pipeline import ROW, GEN, PASS


class GenericOllamaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'tests')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.source = self.work / 'input.csv'
        pd.DataFrame([ROW]).to_csv(self.source, index=False)
        self.calls = []

    def cli(self, *args):
        with patch.object(sys, 'argv', ['recon', *map(str, args)]):
            main()

    def responses(self, *texts):
        values = iter(texts)
        def respond(request, **kwargs):
            body = json.loads(request.data)
            self.calls.append((request.full_url, body))
            return io.BytesIO(json.dumps({'message': {'content': next(values)}, 'done_reason': 'stop'}).encode())
        return patch('urllib.request.urlopen', side_effect=respond)

    def test_config_free_solver_and_resume_identity(self):
        output = self.work / 'solve.jsonl'
        with self.responses('B'):
            self.cli('solve', '--input', self.source, '--output', output, '--model', 'custom/solver:tag',
                     '--base-url', 'http://solver-host:11434/', '--max-tokens', '700', '--num-ctx', '4096')
        url, body = self.calls[0]
        self.assertEqual(url, 'http://solver-host:11434/api/chat')
        self.assertEqual(body['model'], 'custom/solver:tag')
        self.assertNotIn('think', body)
        self.assertEqual(body['options']['num_predict'], 700)
        with self.assertRaisesRegex(ValueError, 'Resume'):
            self.cli('solve', '--input', self.source, '--output', output, '--model', 'other:tag', '--resume')

    def test_independent_generator_and_judge(self):
        output = self.work / 'adapt.jsonl'
        with self.responses(GEN, PASS):
            self.cli('adapt', '--input', self.source, '--output', output,
                     '--generator-model', 'custom/generator:v1', '--judge-model', 'custom/judge:v2',
                     '--base-url', 'http://generator-host:11434', '--judge-base-url', 'http://judge-host:11434',
                     '--think', 'false', '--judge-think', 'careful', '--judge-max-tokens', '9000')
        self.assertEqual([c[1]['model'] for c in self.calls], ['custom/generator:v1', 'custom/judge:v2'])
        self.assertEqual(self.calls[1][0], 'http://judge-host:11434/api/chat')
        self.assertFalse(self.calls[0][1]['think'])
        self.assertEqual(self.calls[1][1]['think'], 'careful')
        record = json.loads(output.read_text())
        self.assertEqual(record['judge_model'], 'custom/judge:v2')
        self.assertEqual(record['final_outcome'], 'equivalent')

    def test_switch_model_does_not_inherit_qwen_thinking(self):
        with self.responses('B'):
            self.cli('solve', '--input', self.source, '--output', self.work / 'switch.jsonl', '--mode', 'cot',
                     '--config', ROOT / 'configs/ollama/qwen.json', '--model', 'nonthinking-custom:tag')
        self.assertNotIn('think', self.calls[0][1])
        self.assertEqual(self.calls[0][1]['model'], 'nonthinking-custom:tag')

    def test_explicit_solver_role_and_advanced_options(self):
        config = self.work / 'config.json'
        config.write_text(json.dumps({'solver': {'provider': 'ollama', 'model': 'custom:solver',
            'think': None, 'options': {'seed': 7, 'top_p': 0.85}, 'keep_alive': '2m'}}))
        with self.responses('B'):
            self.cli('solve', '--input', self.source, '--output', self.work / 'named.jsonl', '--config', config)
        self.assertEqual(self.calls[0][1]['options']['seed'], 7)
        self.assertEqual(self.calls[0][1]['keep_alive'], '2m')
        self.assertNotIn('think', self.calls[0][1])

    def test_missing_judge_is_explicit_and_thinking_values(self):
        with self.assertRaises(SystemExit) as exc:
            self.cli('adapt', '--input', self.source, '--output', self.work / 'bad.jsonl', '--generator-model', 'custom:tag')
        self.assertEqual(exc.exception.code, 2)
        self.assertIsNone(thinking('auto'))
        self.assertTrue(thinking('true'))
        self.assertFalse(thinking('false'))
        self.assertEqual(thinking('model-defined-level'), 'model-defined-level')
        with self.assertRaises(ValueError):
            thinking('123')


if __name__ == '__main__':
    unittest.main()
