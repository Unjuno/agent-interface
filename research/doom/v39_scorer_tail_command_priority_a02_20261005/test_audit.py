import copy
import json
import unittest

import audit


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((audit.ROOT / "RESULT_V3.json").read_text(encoding="utf-8"))

    def test_frozen_output_reproduces_and_candidate_label_bug_is_reported(self):
        report = audit.audit(self.result)
        self.assertEqual(report["disposition"], "PASS_AUDIT_FAIL_REPRODUCED_CANDIDATE_LABEL_MISMATCH")
        self.assertTrue(report["candidate_label_mismatch"])

    def test_ready_at_entry_payload_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["scenarios"][1]["command_bytes_still_unread"] = 0
        self.assertFalse(audit.audit(result)["checks"]["ready_at_entry_overrun_starves"])

    def test_during_callback_readiness_poll_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["scenarios"][2]["readiness_check_count"] = 1
        self.assertFalse(audit.audit(result)["checks"]["during_callback_overrun_starves"])

    def test_fast_control_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["scenarios"][0]["tail"]["termination"] = "deadline"
        self.assertFalse(audit.audit(result)["checks"]["fast_control_observes_ready_command"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
