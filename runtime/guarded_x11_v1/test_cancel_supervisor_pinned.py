"""Regression tests for preflight and pinned cancellation connection custody."""
import time
import unittest
from unittest.mock import Mock, patch

from runtime.guarded_x11_v1.cancel_supervisor import _serve_one


class PinnedSupervisorCustodyTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.receive = Mock()
        self.ready = Mock()
        self.result = Mock()
        self.worker = Mock(return_value={'status': 'unknown', 'operation_id': 'op',
                                         'session_id': 'session'})
        self.request = {'operation_id': 'op', 'session_id': 'session',
                        'display_name': ':7',
                        'deadline_monotonic_ns': time.monotonic_ns() + 5_000_000_000}
        self.receive.recv.return_value = {'op': 'run', 'request': self.request}
        self.identity = {'pid': 42, 'resource_base': 4096}

    def serve(self, observed_pid):
        with patch('runtime.backends.x11_v1.backend.X11Backend', return_value=self.backend), \
             patch('runtime.guarded_x11_v1.xres_client_fence.client_pid_at_base',
                   return_value=observed_pid) as lookup:
            _serve_one(self.receive, self.result, self.ready, self.worker,
                       pinned_display_name=':7', expected_owner=self.identity)
            return lookup

    def test_wrong_owner_never_reports_ready_or_runs_cleanup(self):
        with self.assertRaisesRegex(RuntimeError, 'owner identity mismatch'):
            self.serve(43)
        self.ready.send.assert_not_called()
        self.worker.assert_not_called()
        self.result.send.assert_not_called()
        self.backend.close.assert_called_once()

    def test_matching_owner_reuses_verified_backend_and_closes_it(self):
        lookup = self.serve(42)
        lookup.assert_called_once_with(self.backend.d, 4096)
        self.ready.send.assert_called_once()
        self.worker.assert_called_once_with(self.request, pinned_backend=self.backend)
        self.result.send.assert_called_once()
        self.backend.close.assert_called_once()

    def test_wrong_display_is_refused_without_cleanup(self):
        self.request['display_name'] = ':8'
        self.serve(42)
        self.worker.assert_not_called()
        envelope = self.result.send.call_args.args[0]
        self.assertEqual(envelope['result']['reason'], 'pinned_display_mismatch')
        self.assertEqual(envelope['result']['cleanup_status'], 'UNKNOWN')
        self.backend.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
