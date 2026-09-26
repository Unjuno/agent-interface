import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_receipts import child, co_states, ordered_states
from run_controls import mutations


def event(ordinal, tick, label):
    return {"epoch": "e", "ordinal": ordinal, "server_ms": tick, "label": label}


class ReceiptVerifierTests(unittest.TestCase):
    def test_same_tick_policy_distinction(self):
        events = [event(1, 10, "A"), event(2, 10, "B")]
        self.assertEqual(co_states(events), ["PENDING", "SATISFIED"])
        self.assertEqual(ordered_states(events, strict=True), ["PENDING", "PENDING"])
        self.assertEqual(ordered_states(events, strict=False), ["PENDING", "SATISFIED"])

    def test_exact_80ms_deadline(self):
        events = [event(1, 10, "A"), event(2, 90, "B")]
        self.assertEqual(co_states(events), ["PENDING", "SATISFIED"])
        self.assertEqual(ordered_states(events, strict=True), ["PENDING", "SATISFIED"])
        self.assertEqual(ordered_states(events, strict=False), ["PENDING", "SATISFIED"])

    def test_child_return_code_is_required(self):
        parsed = {"status": "OK"}
        receipt = {"returncode": 9, "stdout": json.dumps(parsed), "parsed": parsed, "stderr": ""}
        errors = []
        child(receipt, "candidate", 0, errors, 7)
        self.assertIn("candidate returncode case 7", errors)

    def test_child_stdout_must_match_parsed(self):
        receipt = {"returncode": 0, "stdout": '{"status":"OK"}', "parsed": {"status": "REFUSE"}, "stderr": ""}
        errors = []
        child(receipt, "candidate", 0, errors, 8)
        self.assertIn("candidate stdout/parsed mismatch case 8", errors)

    def test_original_ten_plus_comparator_receipt_control(self):
        controls = mutations()
        self.assertEqual(len(controls), 11)
        self.assertIn("comparator_rc_zero_to_nine", {item[0] for item in controls})


if __name__ == "__main__":
    unittest.main()
