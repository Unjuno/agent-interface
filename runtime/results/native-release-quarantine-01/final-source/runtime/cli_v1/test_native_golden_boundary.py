"""Exercise the real admission/session/API/result chain with an inert backend."""
from __future__ import annotations

import importlib.util
import unittest
from unittest import mock

from runtime.cli_v1.golden_v3 import adapt_dispatch_result, dispatch_golden_v3
from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest
from runtime.core_v1.test_contract import program


@unittest.skipUnless(importlib.util.find_spec("Xlib"), "python-xlib required")
class NativeBoundaryTests(unittest.TestCase):
    def run_boundary(self, *, seq=7, released=True, close_error=False):
        from runtime.backends.x11_v1.session import X11RuntimeSession

        backend = mock.Mock()
        backend.monotonic_ns.return_value = 9000
        backend.manifest.return_value = capability_manifest(
            "inert-x11", "linux", "x11", OFFICE_FLOOR)
        backend.emissions = 0
        backend.execute.return_value = {
            "releases": [{"verified": released, "keys_down": [], "buttons_down": []}], "emissions": 2,
            "observations": [{"sequence": 8}],
        }
        if close_error:
            backend.close.side_effect = RuntimeError("close failed")
        with mock.patch("runtime.cli_v1.api.open_session",
                        return_value=X11RuntimeSession(backend)):
            row = dispatch_golden_v3(program(), {"window-1": 1},
                                    current_observation_seq=seq,
                                    current_binding_revision=3)
        backend.close.assert_called_once_with()
        return row, backend

    def test_completed_operation_is_not_an_application_score(self):
        row, backend = self.run_boundary()
        backend.execute.assert_called_once()
        self.assertTrue(row["program_completed"])
        self.assertIsNone(row["task_success"])
        self.assertEqual(row["status"], "partial")
        self.assertEqual(row["raw_dispatch"]["result"]["execution"],
                         backend.execute.return_value)

    def test_stale_source_refuses_without_execution(self):
        row, backend = self.run_boundary(seq=8)
        backend.execute.assert_not_called()
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["diagnostic"], "STALE_OBSERVATION")
        self.assertFalse(row["program_completed"])

    def test_unverified_release_keeps_execution_for_recovery(self):
        row, backend = self.run_boundary(released=False)
        self.assertEqual(row["native_status"], "release_unverified")
        self.assertFalse(row["program_completed"])
        self.assertEqual(row["raw_dispatch"]["result"]["execution"]["emissions"], 2)

    def test_close_failure_preserves_completed_operation(self):
        row, backend = self.run_boundary(close_error=True)
        self.assertEqual(row["status"], "cleanup_failed")
        self.assertTrue(row["program_completed"])
        self.assertFalse(row["task_success"])


class EvidenceRetentionTests(unittest.TestCase):
    def test_rejected_adapter_retains_unknown_raw_evidence(self):
        raw = {"status": "future_status", "result": {"effects": ["saved"]}}
        row = adapt_dispatch_result(raw)
        self.assertEqual(row["raw_dispatch"], raw)
        raw["result"]["effects"].append("later")
        self.assertEqual(row["raw_dispatch"]["result"]["effects"], ["saved"])

    def test_explicit_empty_usage_does_not_fall_back_to_other_usage(self):
        row = adapt_dispatch_result({"status": "returned", "usage": {"input": 3}}, usage={})
        self.assertEqual(row["usage"], {})


if __name__ == "__main__":
    unittest.main()
