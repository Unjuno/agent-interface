import importlib
import sys
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


class PendingPumpProbeTests(unittest.TestCase):
    def load_modules(self):
        self.assertTrue((PACKAGE / "probe.py").is_file(), "probe.py must exist")
        self.assertTrue((PACKAGE / "audit.py").is_file(), "audit.py must exist")
        sys.path.insert(0, str(PACKAGE))
        try:
            return importlib.import_module("probe"), importlib.import_module("audit")
        finally:
            sys.path.pop(0)

    def test_candidate_executes_current_pending_pump_and_neutral_cancel_path(self):
        probe, _ = self.load_modules()
        result = probe.run_probe()
        self.assertEqual(result["status"], "PASS_SYNTHETIC_PENDING_PUMP_RELEASE_ORDER")
        self.assertTrue(result["observation_processed_while_planner_pending"])
        self.assertEqual(result["cancel_command"], {"op": "cancel", "id": "cover-0"})
        self.assertEqual(result["terminal_status"], "cancelled")
        self.assertEqual(result["release"], {
            "verified": True, "keys_down": [], "buttons_down": []})
        self.assertEqual(result["cover_renewals"], 0)

    def test_independent_audit_reconstructs_candidate_result(self):
        probe, auditor = self.load_modules()
        result = probe.run_probe()
        audit = auditor.audit_result(result)
        self.assertEqual(audit["status"], "PASS_SOURCE_COMPOSITION")
        self.assertEqual(audit["checks_passed"], audit["checks_total"])

    def test_independent_audit_rejects_mutated_terminal_result(self):
        probe, auditor = self.load_modules()
        result = probe.run_probe()
        result["release"]["keys_down"] = ["space"]
        audit = auditor.audit_result(result)
        self.assertEqual(audit["status"], "FAIL_SOURCE_COMPOSITION")
        self.assertIn("result_matches_reconstruction", audit["failed_checks"])

    def test_independent_audit_rejects_unrecognized_claim(self):
        probe, auditor = self.load_modules()
        result = probe.run_probe()
        result["task_success"] = True
        audit = auditor.audit_result(result)
        self.assertEqual(audit["status"], "FAIL_SOURCE_COMPOSITION")
        self.assertIn("result_matches_reconstruction", audit["failed_checks"])


if __name__ == "__main__":
    unittest.main()
