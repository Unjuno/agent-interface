"""Pure signal doubles: never pause a real process or open an X display."""
from contextlib import ExitStack
import signal
import unittest
from unittest.mock import call, patch

from runtime.cli_v1 import test_mcp_xvfb_blocked_release_integration as harness


class XvfbPauseCleanupTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(harness.os.environ,
            {"AGENT_INTERFACE_XVFB_PID": "12345"}))
        self.stack.enter_context(patch.object(signal, "SIGSTOP", 19, create=True))
        self.stack.enter_context(patch.object(signal, "SIGCONT", 18, create=True))
        self.legacy = self.stack.enter_context(patch.object(harness.os, "kill"))
        self.open = self.stack.enter_context(patch.object(harness.os, "pidfd_open",
                                                        return_value=901, create=True))
        self.send = self.stack.enter_context(patch.object(harness.signal, "pidfd_send_signal",
                                                        create=True))
        self.close = self.stack.enter_context(patch.object(harness.os, "close"))
        self.stack.enter_context(patch.object(harness.os, "readlink", return_value="/usr/bin/Xvfb"))
        self.argv = self.stack.enter_context(patch.object(harness.Path, "read_bytes",
            return_value=b"Xvfb\0:88\0-nolisten\0tcp\0"))
        self.status = self.stack.enter_context(patch.object(harness.Path, "read_text",
                                                          return_value="State:\tT (stopped)\n"))
        self.timer = self.stack.enter_context(patch.object(harness.threading, "Timer"))

    def test_status_read_error_after_stop_resumes_exact_handle_and_closes_it(self):
        self.status.side_effect = OSError("status read failed after stop")
        with self.assertRaises(OSError):
            harness._pause_owned_xvfb_for_test(10)
        self.assertEqual(self.send.call_args_list, [call(901, 19), call(901, 18)])
        self.close.assert_called_once_with(901)
        self.legacy.assert_not_called()

    def test_timer_start_failure_after_stop_resumes_exact_handle(self):
        self.timer.return_value.start.side_effect = RuntimeError("timer unavailable")
        with self.assertRaisesRegex(RuntimeError, "timer unavailable"):
            harness._pause_owned_xvfb_for_test(10)
        self.assertEqual(self.send.call_args_list, [call(901, 19), call(901, 18)])
        self.close.assert_called_once_with(901)
        self.legacy.assert_not_called()

    def test_stop_signal_error_still_attempts_exact_handle_resume(self):
        self.send.side_effect = [OSError("stop result unavailable"), None]
        with self.assertRaisesRegex(OSError, "stop result unavailable"):
            harness._pause_owned_xvfb_for_test(10)
        self.assertEqual(self.send.call_args_list, [call(901, 19), call(901, 18)])
        self.close.assert_called_once_with(901)
        self.legacy.assert_not_called()

    def test_resume_failure_is_retained_without_retrying_a_pid_number(self):
        self.send.side_effect = [None, OSError("pinned process exited")]
        row, _timer, resume = harness._pause_owned_xvfb_for_test(10)
        resume()
        resume()
        self.assertIsNone(row["resumed"]["monotonic_ns"])
        self.assertIn("pinned process exited", row["resumed"]["error"])
        self.assertEqual(self.send.call_args_list, [call(901, 19), call(901, 18)])
        self.close.assert_called_once_with(901)
        self.legacy.assert_not_called()

    def test_resume_is_idempotent_and_never_reopens_a_reused_pid(self):
        row, _timer, resume = harness._pause_owned_xvfb_for_test(10)
        resume()
        resume()
        self.open.assert_called_once_with(12345, 0)
        self.assertEqual(self.send.call_args_list, [call(901, 19), call(901, 18)])
        self.close.assert_called_once_with(901)
        self.assertIsInstance(row["resumed"]["monotonic_ns"], int)
        self.legacy.assert_not_called()

    def test_foreign_display_is_refused_without_any_signal(self):
        self.argv.return_value = b"Xvfb\0:99\0"
        with self.assertRaises(RuntimeError):
            harness._pause_owned_xvfb_for_test(10)
        self.send.assert_not_called()
        self.legacy.assert_not_called()

    def test_missing_pidfd_support_refuses_before_any_signal(self):
        with patch.object(harness.os, "pidfd_open", None, create=True):
            with self.assertRaises(RuntimeError):
                harness._pause_owned_xvfb_for_test(10)
        self.send.assert_not_called()
        self.legacy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
