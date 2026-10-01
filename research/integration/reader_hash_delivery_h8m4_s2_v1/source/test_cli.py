import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class HostBoundaryTests(unittest.TestCase):
    def test_explicit_cursor_and_error_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stream = root / 'events.jsonl'
            original = b'{"event":"ready","delivery_id":"delivery:1"}\n'
            stream.write_bytes(original)
            command = [sys.executable, '-m', 'research.integration.event_inbox_reader_v1',
                       '--stream', str(stream), '--stream-id', 'run-1']
            def invoke(extra=()):
                process = subprocess.run(command + list(extra), capture_output=True, timeout=5)
                self.assertEqual(process.stderr, b'')
                response = json.loads(process.stdout)
                self.assertEqual(response['authority'], 'none')
                self.assertFalse(response['acknowledged'])
                self.assertFalse(response['input_dispatched'])
                self.assertEqual(stream.read_bytes(), original)
                return process.returncode, response
            code, first = invoke()
            self.assertEqual(code, 0)
            self.assertEqual(len(first['records']), 1)
            self.assertEqual(invoke(), (code, first))
            cursor = root / 'cursor.json'
            cursor.write_text(json.dumps(first['next_cursor']))
            saved = cursor.read_bytes()
            code, second = invoke(['--cursor', str(cursor)])
            self.assertEqual(code, 0)
            self.assertEqual(second['records'], [])
            self.assertEqual(cursor.read_bytes(), saved)
            for content in ('null', '{', ' ' * 4097):
                cursor.write_text(content)
                code, failed = invoke(['--cursor', str(cursor)])
                self.assertEqual(code, 2)
                self.assertEqual(failed['status'], 'read_failed')
                self.assertNotIn('next_cursor', failed)


if __name__ == '__main__':
    unittest.main()
