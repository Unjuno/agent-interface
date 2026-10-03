"""Real owned child, injected kill failure, and bridge occupancy regression."""
import json
import pathlib
import subprocess
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from runtime.guarded_win32_v1 import supervisor
import runtime.guarded_win32_v1.test_late_state as fixtures


class KillFailureCase(unittest.TestCase):
    def test_failed_kill_retains_live_handle_and_blocks_new_input(self):
        backend, observer, bridge, raw, events = fixtures.Cases(
            'test_exact_expiry_consumes_without_capture').fixture()
        permit = bridge.prepare('button', [1, 1])
        children = []
        launch = subprocess.Popen
        kill = subprocess.Popen.kill

        class Verifier:
            receipt = None

            def __call__(self, *args):
                self.receipt = supervisor.run(
                    [sys.executable, '-B', '-c', 'import time; time.sleep(60)'],
                    b'', time.monotonic_ns() + 100_000_000)
                return None

        def tracked_launch(*args, **kwargs):
            child = launch(*args, **kwargs)
            children.append(child)
            return child

        verifier = Verifier()
        try:
            # Track creation without replacing the Popen class identity used by
            # the effect boundary's ownership check.
            with patch.object(subprocess.Popen, 'kill', side_effect=OSError('injected kill refusal')):
                wrapped = SimpleNamespace(Popen=tracked_launch, PIPE=subprocess.PIPE,
                                          TimeoutExpired=subprocess.TimeoutExpired)
                with patch.object(supervisor, 'subprocess', wrapped):
                    result = bridge.execute(
                        permit['authorization'], verify_effect=verifier,
                        effect_deadline_ns=time.monotonic_ns() + 3_000_000_000)
            child = children[0]
            self.assertIsNone(result['task_success'])
            self.assertEqual(verifier.receipt['reason'], 'termination_unconfirmed')
            self.assertIs(verifier.receipt['process'], child)
            self.assertIs(bridge.pending_verifier, child)
            self.assertIsNone(child.poll())
            count = backend._capture_hdc.call_count
            with self.assertRaisesRegex(ValueError, 'verifier still active'):
                bridge.prepare('button', [1, 1])
            bridge.recover_input()
            with self.assertRaisesRegex(ValueError, 'verifier still active'):
                bridge.prepare('button', [1, 1])
            self.assertEqual(backend._capture_hdc.call_count, count)
            self.assertEqual(bridge.execute(permit['authorization'])['error'],
                             'AUTHORIZATION_CONSUMED_OR_UNKNOWN')
            kill(child)
            child.communicate(timeout=3)
            self.assertTrue(bridge.verifier_idle())
            self.assertIsNone(bridge.pending_verifier)
            self.assertEqual(events, [['move', 'fixture', 3, 3], ['release']])
            pathlib.Path('kill-failure-raw.json').write_text(json.dumps({
                'pid': child.pid, 'actual_terminal_exit': child.returncode,
                'termination_error': verifier.receipt['termination_error'],
                'unknown_effect': result['task_success'] is None,
                'live_handle_blocked_preparation': True,
                'recovery_did_not_clear_occupancy': True,
                'last_verifier_exit': bridge.last_verifier_exit}, indent=2), encoding='utf-8')
        finally:
            for child in children:
                if child.poll() is None:
                    kill(child)
                child.communicate(timeout=3)


if __name__ == '__main__':
    unittest.main()
