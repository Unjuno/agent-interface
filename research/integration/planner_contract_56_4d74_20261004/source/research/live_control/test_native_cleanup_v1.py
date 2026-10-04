import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from native_cleanup_v1 import finish_allocation
from native_exchange_v1 import publish


class CleanupTests(unittest.TestCase):
    def run_case(self, *, copy_failure=False, close_failure=False, alive=False,
                 poll_failure=False, persistence_failure=False, task_failure=False,
                 session_failure=False, action_failure=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            out = root / 'run'; out.mkdir()
            source = root / 'sheet.xlsx'; source.write_bytes(b'retained output')
            if copy_failure:
                source.unlink()
            events = []

            def bridge_close():
                self.assertFalse((out / 'reply-1.json').exists())
                events.append('bridge')
                if close_failure:
                    raise OSError('connection close failed')

            def session_close():
                self.assertFalse((out / 'reply-1.json').exists())
                events.append('session')
                if session_failure:
                    raise OSError('session close failed')

            def poll():
                events.append('poll')
                if poll_failure:
                    raise OSError('poll failed')
                return None if alive else -15

            def final_publish(path, data):
                self.assertEqual(events, ['bridge', 'session', 'poll'])
                self.assertTrue((out / 'cleanup.json').exists())
                if not persistence_failure:
                    self.assertTrue((out / 'cleanup-report.json').exists())
                return publish(path, data)

            if persistence_failure:
                (out / 'cleanup-report.json').mkdir()
            reply = {'status': 'finished', 'stage': 1, 'decision_sha256': 'fixed',
                     'evaluation': {'success': not task_failure}, 'authority_granted': False}
            if action_failure:
                reply.update(status='needs_review', error='original action failure', task_success=None)
            with patch('native_cleanup_v1.publish', final_publish):
                report = finish_allocation(out, {'calc': {'output': source}},
                    SimpleNamespace(close=bridge_close),
                    SimpleNamespace(close=session_close, procs=[SimpleNamespace(pid=123, poll=poll)]),
                    reply)
            returned = json.loads((out / 'reply-1.json').read_text())
            self.assertEqual(returned['cleanup'], report)
            self.assertEqual(returned['evaluation'], reply['evaluation'])
            self.assertFalse(report['owner_exit_verified'])
            self.assertFalse(report['descendants_verified'])
            self.assertEqual(returned['decision_sha256'], 'fixed')
            return returned

    def test_publication_follows_cleanup(self):
        result = self.run_case()
        self.assertEqual(result['status'], 'finished')
        self.assertTrue(result['cleanup']['tracked_processes_terminal'])

    def test_task_failure_is_not_cleanup_failure(self):
        self.assertEqual(self.run_case(task_failure=True)['status'], 'finished')

    def test_copy_and_close_failures_do_not_skip_session(self):
        result = self.run_case(copy_failure=True, close_failure=True)
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual([e['stage'] for e in result['cleanup']['errors']],
                         ['copy:calc', 'bridge.close'])

    def test_live_process_prevents_finished(self):
        self.assertEqual(self.run_case(alive=True)['status'], 'needs_review')

    def test_poll_failure_prevents_finished(self):
        self.assertEqual(self.run_case(poll_failure=True)['status'], 'needs_review')

    def test_persistence_failure_in_returned_reply(self):
        result = self.run_case(persistence_failure=True)
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['cleanup']['errors'][0]['stage'], 'cleanup-report.json')

    def test_session_failure_still_checks_processes(self):
        self.assertEqual(self.run_case(session_failure=True)['status'], 'needs_review')

    def test_cleanup_does_not_replace_original_action_error(self):
        result = self.run_case(action_failure=True, copy_failure=True)
        self.assertEqual(result['error'], 'original action failure')
        self.assertEqual(result['status'], 'needs_review')


if __name__ == '__main__':
    unittest.main()
