"""CLI output must be complete when created; serialization refusal leaves no file."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class UsageOutputTests(unittest.TestCase):
    def invoke(self, amount):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            selection = [{'name': 'window', 'begin_call_id': 'begin', 'end_call_id': 'end'}]
            rows = [{'type': 'response_item', 'payload': {'type': 'custom_tool_call',
                    'call_id': 'begin', 'name': 'test', 'input': 'private'}}]
            for rid in ('one', 'two'):
                rows.append({'type': 'token_usage_record', 'payload': {
                    'response_id': rid, 'turn_id': 't', 'usage': {
                        'input_tokens': amount, 'cached_input_tokens': 0,
                        'cache_write_input_tokens': 0, 'output_tokens': 0,
                        'reasoning_output_tokens': 0, 'total_tokens': amount}}})
            rows.extend([
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
                    'call_id': 'begin', 'output': 'private'}},
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call',
                    'call_id': 'end', 'name': 'test', 'input': ''}},
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
                    'call_id': 'end', 'output': ''}}])
            (root / 'selection.json').write_text(json.dumps(selection), encoding='utf-8')
            (root / 'session.jsonl').write_text('\n'.join(map(json.dumps, rows)) + '\n', encoding='utf-8')
            output = root / 'output.json'
            completed = subprocess.run([sys.executable,
                str(Path(__file__).with_name('primary_usage_projection.py')),
                '--selection', str(root / 'selection.json'),
                '--session', str(root / 'session.jsonl'), '--output', str(output)],
                capture_output=True, timeout=15)
            return completed, output.read_bytes() if output.exists() else None

    def test_serialization_failure_leaves_no_output(self):
        if sys.get_int_max_str_digits() != 4300:
            self.skipTest('requires the default 4300-digit Python integer limit')
        completed, output = self.invoke(9 * 10 ** 4299)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(b'Exceeds the limit', completed.stderr)
        self.assertIsNone(output)

    def test_healthy_output_is_complete(self):
        completed, output = self.invoke(100)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(output)['windows'][0]['totals']['total_tokens'], 200)
        self.assertNotIn(b'private', output)


if __name__ == '__main__':
    unittest.main()
