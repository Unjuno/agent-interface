import copy
import unittest
from .audit_v2 import validate
from .candidate import run_once


class AckObservationOrderAudit(unittest.TestCase):
    def setUp(self):
        self.result = run_once()
        self.raw = self.result["events"]

    def test_accepts_preregistered_order_difference(self):
        self.assertTrue(validate(self.result, self.raw))

    def test_rejects_typed_before_ack_monitor_call(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][0]["monitor_calls"] = 1
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_ack_before_typed_missed_invalidation(self):
        changed = copy.deepcopy(self.result)
        changed["cases"][1]["following_wait_event"] = "terminal"
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_row_order_mutation(self):
        changed = copy.deepcopy(self.result)
        changed["events"][1], changed["events"][2] = changed["events"][2], changed["events"][1]
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_added_authority_claim(self):
        changed = copy.deepcopy(self.result)
        changed["events"][0]["input_emission"] = "EXECUTED"
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])
