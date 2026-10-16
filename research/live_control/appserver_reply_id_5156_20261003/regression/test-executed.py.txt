"""Public stdio regression for Boolean IDs followed by a valid Number reply."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient

PEER = r'''
import json, sys
request = json.loads(sys.stdin.readline())
if request['method'] == 'fixture/error':
    messages = [{'id':request['id'],'error':{'code':-32000,'message':'fixture error'}}]
else:
    messages = [
        {'id':True,'result':{'payload':'Boolean true must not correlate'}},
        {'id':False,'result':{'payload':'Boolean false must not cache'}},
        {'method':'fixture/notice','params':{'ready':True}},
        {'id':float(request['id']),'result':{'payload':'valid Number'}},
    ]
for message in messages:
    sys.stdout.write(json.dumps(message,separators=(',',':'))+'\n')
sys.stdout.flush()
sys.stderr.write('fixture EOF\n')
sys.stderr.flush()
'''


class ReplyIdRegression(unittest.TestCase):
    def exercise(self, method):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'journal.jsonl'
            client = CodexAppServerClient([sys.executable, '-B', '-c', PEER], journal_path=str(journal))
            try:
                if method == 'fixture/error':
                    with self.assertRaisesRegex(AppServerError, 'fixture error'):
                        client.request(method, timeout=1)
                else:
                    self.assertEqual(client.request(method, timeout=1), {'payload':'valid Number'})
                    self.assertEqual(client.wait_notification(lambda row: row.get('method') == 'fixture/notice', timeout=1),
                                     {'method':'fixture/notice','params':{'ready':True}})
                self.assertEqual(client.process.wait(timeout=1), 0)
            finally:
                client.close(timeout=1)
                for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                    stream.close()
            self.assertFalse(client._reader.is_alive())
            self.assertEqual(client._responses, {})
            rows = [json.loads(line) for line in journal.read_text(encoding='utf8').splitlines()]
            self.assertIs(type(rows[0]['message']['id']), int)
            if method != 'fixture/error':
                self.assertEqual([row['message'].get('id') for row in rows[1:]], [True, False, None, 1.0])
                self.assertIs(type(rows[-1]['message']['id']), float)

    def test_boolean_noise_preserves_numeric_reply_and_notification(self):
        self.exercise('fixture/result')

    def test_matching_server_error_is_preserved(self):
        self.exercise('fixture/error')


if __name__ == '__main__':
    unittest.main()
