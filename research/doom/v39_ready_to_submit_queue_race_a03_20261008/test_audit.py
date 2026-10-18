import copy
import unittest
from .audit import validate
from .candidate import run_once


class ReadySubmitWaitAudit(unittest.TestCase):
    def setUp(self):
        self.result = run_once()
        self.raw = self.result["events"]

    def test_accepts_production_wait_trace(self):
        self.assertTrue(validate(self.result, self.raw))

    def test_rejects_trace_that_retains_typed_row(self):
        changed = copy.deepcopy(self.result)
        changed["events"][7]["count"] = 1
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_ack_monitor_claim(self):
        changed = copy.deepcopy(self.result)
        changed["events"][6]["count"] = 1
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_input_claim(self):
        changed = copy.deepcopy(self.result)
        changed["events"][2]["input_emission"] = "EXECUTED"
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])

    def test_rejects_event_reordering(self):
        changed = copy.deepcopy(self.result)
        changed["events"][3], changed["events"][4] = changed["events"][4], changed["events"][3]
        with self.assertRaises(ValueError):
            validate(changed, changed["events"])
