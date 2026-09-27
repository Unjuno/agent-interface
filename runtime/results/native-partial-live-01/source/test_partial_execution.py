"""Failure after an effect must not erase the prefix or masquerade as success."""
import unittest
from unittest import mock

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest
from runtime.core_v1.test_contract import program


class PartialExecutionTests(unittest.TestCase):
    def test_partial_operation_and_observation_survive_failure_and_close(self):
        for release_fails, close_fails in ((False, False), (True, False), (False, True)):
            with self.subTest(release=release_fails, close=close_fails):
                backend = object.__new__(X11Backend)
                backend.emissions = 0
                backend.preflight = mock.Mock()
                backend.focus = mock.Mock()
                backend.capture = mock.Mock(return_value={"sha256": "earlier-observation"})
                backend.monotonic_ns = lambda: 9000
                backend.manifest = lambda: capability_manifest("inert", "linux", "x11", OFFICE_FLOOR)
                calls = []

                def text(value):
                    calls.append(value)
                    backend.emissions += 1
                    if value == "fault":
                        raise OSError("after partial emission")

                backend.text = text
                backend.close = mock.Mock(side_effect=OSError("close failed") if close_fails else None)
                backend.release_all = mock.Mock(return_value={"verified": True, "keys_down": [], "buttons_down": []},
                                               side_effect=OSError("release failed") if release_fails else None)
                p = program()
                p["ops"] = [
                    {"op": "focus", "target": "window-1"},
                    {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 10, "h": 10},
                    {"op": "text", "text": "done"}, {"op": "text", "text": "fault"},
                    {"op": "text", "text": "mustnotrun"}, {"op": "release_all"},
                ]
                with mock.patch("runtime.cli_v1.api.open_session", return_value=X11RuntimeSession(backend)):
                    row = dispatch_golden_v3(p, {"window-1": 1}, current_observation_seq=7,
                                             current_binding_revision=3)
                self.assertEqual(calls, ["done", "fault"])
                self.assertFalse(row["program_completed"])
                self.assertEqual(row["status"], "cleanup_failed" if close_fails else "partial")
                evidence = row["raw_dispatch"]["result"]["execution"]
                self.assertEqual(evidence["completed_ops"], [0, 1, 2])
                self.assertEqual(evidence["failed_op"], 3)
                self.assertEqual(evidence["program_emissions"], 2)
                self.assertIn("unknown", evidence["failed_op_effect"])
                self.assertIn("partial emission", evidence["error"])
                self.assertEqual(evidence["observations"], [{"sha256": "earlier-observation"}])
                self.assertEqual(evidence["releases"][-1]["verified"], not release_fails)
                if release_fails:
                    self.assertIn("release failed", evidence["releases"][-1]["error"])
                backend.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
