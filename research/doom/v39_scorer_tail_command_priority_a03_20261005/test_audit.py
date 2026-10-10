import copy
import json
import unittest

import audit


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(
            (audit.ROOT / "results" / "a03" / "RESULT.json")
            .read_text(encoding="utf-8"))

    def test_frozen_result_reconstructs(self):
        report = audit.audit(self.result)
        self.assertEqual(report["disposition"],
                         "PASS_COMMAND_PRIORITY_REPAIR_CONSTRUCTION")
        self.assertFalse(report["errors"])

    def test_extra_tail_sample_is_rejected(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][1]["tail_samples"] = 2
        self.assertFalse(audit.audit(changed)["case_checks"]["slow_callback"]["tail_samples"])

    def test_consumed_command_bytes_are_rejected(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][0]["unread_command_after_tail"] = ""
        self.assertFalse(audit.audit(changed)["case_checks"]["ready_at_entry"]["unread_after_tail"])

    def test_command_delivery_loss_is_rejected(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][2]["commands_delivered"] = 0
        self.assertFalse(audit.audit(changed)["case_checks"]["normal_wait"]["delivered_once"])

    def test_wrong_termination_is_rejected(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][0]["termination"] = "deadline"
        self.assertFalse(audit.audit(changed)["case_checks"]["ready_at_entry"]["termination"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
