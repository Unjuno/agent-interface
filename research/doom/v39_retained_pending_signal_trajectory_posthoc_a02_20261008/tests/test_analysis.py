import json
import unittest
from pathlib import Path

from analyze import reconstruct
from audit import audit


ROOT = Path(__file__).resolve().parents[1]


class RetainedTrajectoryTests(unittest.TestCase):
    def test_six_windows_reconstruct_and_audit(self):
        result = reconstruct(ROOT)
        self.assertEqual(result["observation_count"], 218)
        self.assertEqual(result["recorded_policy_invalidations"], 1)
        self.assertEqual(
            [(w["source_sequence"], w["source_health"], w["last_pending_sequence"]) for w in result["decision_windows"]],
            [(1, 97, 28), (36, 97, 70), (70, 85, 91), (91, 73, 113), (115, 65, 159), (166, 61, 218)],
        )
        self.assertEqual(
            [(x["decision"], x["sequence"], x["health"], x["hard_minimum"]) for x in result["authored_threshold_events"]],
            [(1, 62, 85, 85), (5, 200, 51, 51)],
        )
        self.assertEqual(
            [(x["decision"], x["sequence"], x["health"]) for x in result["authored_loss_guard_events"]],
            [(1, 62, 85), (5, 200, 51)],
        )
        self.assertEqual(audit_result(result)["status"], "PASS_RECONSTRUCTION")

    def test_corrupted_result_rejected(self):
        result = reconstruct(ROOT)
        result["decision_windows"][5]["pending_changes"][-1]["health"] = 49
        with self.assertRaisesRegex(ValueError, "independent reconstruction"):
            audit_result(result)

    def test_corrupted_raw_is_rejected_by_frozen_hash(self):
        with self.assertRaisesRegex(ValueError, "frozen input hash mismatch: events.jsonl"):
            reconstruct(ROOT, hash_override={"events.jsonl": "0" * 64})


def audit_result(actual):
    expected = reconstruct(ROOT)
    if actual != expected:
        raise ValueError("candidate result does not match independent reconstruction")
    return {"status": "PASS_RECONSTRUCTION"}


if __name__ == "__main__":
    unittest.main()
