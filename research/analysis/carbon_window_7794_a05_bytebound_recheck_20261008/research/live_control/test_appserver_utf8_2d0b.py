"""Real owned pipe tests; no provider, GUI, or historical actor replay."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient


PEER = """import base64, sys
sys.stdin.buffer.readline()
sys.stdout.buffer.write(base64.b64decode(sys.argv[1]))
sys.stdout.buffer.flush()
"""


class Utf8PipeTests(unittest.TestCase):
    def exercise(self, wire, expected=None):
        # Reproduce a cp932-default host on any test runner. An explicit client
        # codec still takes precedence; the actual peer always writes raw bytes.
        def cp932_default(command, **kwargs):
            kwargs.setdefault('encoding', 'cp932')
            return subprocess.Popen(command, **kwargs)

        errors = []
        original_hook = threading.excepthook
        client = None
        record = {'method': self._testMethodName, 'started_ns': time.time_ns(),
                  'wire_b64': base64.b64encode(wire).decode('ascii'),
                  'wire_sha256': hashlib.sha256(wire).hexdigest(),
                  'peer_source_sha256': hashlib.sha256(PEER.encode()).hexdigest(),
                  'default_codec_fixture': 'cp932', 'first_outcome': {}}

        def hook(error):
            if client is not None and error.thread is client._reader:
                errors.append({'type': error.exc_type.__name__, 'message': str(error.exc_value)})
            else:
                original_hook(error)

        threading.excepthook = hook
        temporary = tempfile.TemporaryDirectory(prefix='utf8-owned-pipe-')
        try:
            client = CodexAppServerClient(
                [sys.executable, '-B', '-c', PEER, base64.b64encode(wire).decode('ascii')],
                process_factory=cp932_default,
                journal_path=Path(temporary.name)/'protocol.jsonl')
            record['owned_pid'] = client.process.pid
            if expected is None:
                with self.assertRaises(AppServerError) as caught:
                    client.request('owned_probe', {}, timeout=3)
                record['first_outcome']['error_type'] = type(caught.exception).__name__
                client._reader.join(timeout=3)
                self.assertEqual([e['type'] for e in errors], ['UnicodeDecodeError'])
            else:
                actual = client.request('owned_probe', {}, timeout=3)
                record['first_outcome']['returned_value'] = actual
                self.assertEqual(actual, expected)
                self.assertEqual(errors, [])
            self.assertEqual(client.process.wait(timeout=3), 0)
            record['first_outcome']['pass'] = True
        except BaseException as error:
            record['first_outcome']['pass'] = False
            record['first_outcome']['failure_type'] = type(error).__name__
            record['first_outcome']['failure_message'] = str(error)
            raise
        finally:
            try:
                if client is not None:
                    client.close(timeout=3)
                    record['actual_child_exit_code'] = client.process.poll()
                    record['stdout_reader_alive'] = client._reader.is_alive()
                    journal = getattr(client, '_journal', None)
                    record['journal_closed'] = journal is None or journal.closed
                    for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                        stream.close()
            finally:
                threading.excepthook = original_hook
                temporary.cleanup()
                record['reader_errors'] = errors
                record['ended_ns'] = time.time_ns()
                location = os.environ.get('APPSERVER_UTF8_EVIDENCE_DIR')
                if location:
                    path = Path(location)/(self._testMethodName+'.json')
                    with path.open('x', encoding='utf-8') as stream:
                        json.dump(record, stream, ensure_ascii=True, indent=2)
                        stream.write('\n')

    def test_utf8_meaning_survives_cp932_default(self):
        expected = {'text': '設計レビュー é🚀\n連絡済み', 'padding': 'x'*4097,
                    'date': '2026-11-10', 'time': '14:35'}
        wire = (json.dumps({'id': 1, 'result': expected}, ensure_ascii=False,
                           separators=(',', ':'))+'\n').encode('utf-8')
        self.exercise(wire, expected)

    def test_invalid_utf8_is_not_accepted_as_cp932(self):
        self.exercise(b'{"id":1,"result":{"text":"\x80"}}\n')


if __name__ == '__main__':
    unittest.main()
