import unittest

try:
    import analyze_map01_direct_retained_input_v2 as candidate
except ModuleNotFoundError:
    class Candidate:
        @staticmethod
        def analyze(events):
            return {}
    candidate = Candidate()


def admission(key, admitted_ns, ack_ns, *, token="t", owner="o", deadline=1000):
    return {
        "event": "input_admission", "key": key, "intent_token": token,
        "owner_id": owner, "valid_until_ns": deadline,
        "admitted_ns": admitted_ns, "input_ack_ns": ack_ns,
    }


def admission_receipt(row):
    receipt = dict(row)
    receipt["operation"] = "down"
    return receipt


def release(key, receipt, started_ns, returned_ns, *, token="t", owner="o",
            deadline=1000, admission_valid=True, verified=True, ordinary=True):
    return {
        "event": "input_release_transition", "operation": "up", "key": key,
        "intent_token": token, "owner_id": owner, "valid_until_ns": deadline,
        "admission_receipt": receipt,
        "admission_receipt_valid": admission_valid,
        "owner_transition_verified": verified,
        "ordinary_release_candidate": ordinary,
        "release_call_started_ns": started_ns,
        "release_call_returned_ns": returned_ns,
    }


class Tests(unittest.TestCase):
    def test_pairs_each_release_by_its_embedded_admission_receipt(self):
        first = admission("a", 100_000_000, 110_000_000, deadline=1_000_000_000)
        second = admission("b", 200_000_000, 210_000_000, deadline=1_000_000_000)
        result = candidate.analyze([
            first, second,
            release("b", admission_receipt(second), 300_000_000, 305_000_000,
                    deadline=1_000_000_000),
            release("a", admission_receipt(first), 400_000_000, 410_000_000,
                    deadline=1_000_000_000),
        ])
        self.assertIs(result.get("measurement_ready"), True)
        self.assertEqual(result.get("hold_count"), 2)
        holds = result.get("holds", [])
        if len(holds) != 2:
            self.fail("expected two receipt-linked holds")
        self.assertEqual(holds[0]["key"], "b")
        self.assertAlmostEqual(holds[0]["retained_lower_ms"], 90.0)
        self.assertAlmostEqual(holds[0]["retained_upper_ms"], 105.0)
        self.assertEqual(holds[1]["key"], "a")
        self.assertAlmostEqual(holds[1]["retained_lower_ms"], 290.0)
        self.assertAlmostEqual(holds[1]["retained_upper_ms"], 310.0)

    def test_matches_pointer_button_payload_to_pointer_admission(self):
        start = {
            "event": "pointer_admission", "operation": "button_down", "payload": 1,
            "intent_token": "t", "owner_id": "o", "valid_until_ns": 1000,
            "admitted_ns": 100, "input_ack_ns": 110,
        }
        end = {
            "event": "input_release_transition", "operation": "button_up", "key": 1,
            "intent_token": "t", "owner_id": "o", "valid_until_ns": 1000,
            "admission_receipt": start, "admission_receipt_valid": True,
            "owner_transition_verified": True, "ordinary_release_candidate": True,
            "release_call_started_ns": 200, "release_call_returned_ns": 205,
        }
        result = candidate.analyze([start, end])
        self.assertIs(result.get("measurement_ready"), True)
        holds = result.get("holds", [])
        if len(holds) != 1:
            self.fail("expected one pointer-button hold")
        self.assertEqual(holds[0]["input_kind"], "pointer_button")
        self.assertEqual(holds[0]["key"], 1)

    def test_rejects_reused_receipt_and_boolean_timestamp(self):
        start = admission("a", 100, 110)
        receipt = admission_receipt(start)
        first = release("a", receipt, 200, 205)
        duplicate = dict(first)
        bad_time = admission("b", 300, True)
        bad_transition = release("b", admission_receipt(bad_time), 400, 405)
        result = candidate.analyze([start, bad_time, first, duplicate, bad_transition])
        self.assertIs(result.get("measurement_ready"), False)
        self.assertEqual(result.get("hold_count"), 1)
        self.assertEqual(result.get("invalid_release_count"), 2)
        self.assertEqual(result.get("unmatched_admission_count"), 0)
        self.assertEqual(result.get("malformed_admission_count"), 1)

    def test_rejects_receipt_identity_mismatch(self):
        start = admission("a", 100, 110)
        result = candidate.analyze([
            start,
            release("b", admission_receipt(start), 200, 205),
        ])
        self.assertIs(result.get("measurement_ready"), False)
        self.assertEqual(result.get("invalid_release_count"), 1)
        self.assertEqual(result.get("unmatched_admission_count"), 1)


if __name__ == "__main__":
    unittest.main()
