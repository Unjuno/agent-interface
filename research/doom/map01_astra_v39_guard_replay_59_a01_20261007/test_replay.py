import json
from pathlib import Path
import unittest

from audit import audit
from candidate import analyze


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class GuardReplayTests(unittest.TestCase):
    def test_emits_all_frozen_scenarios(self):
        result = analyze(FIXTURE)
        self.assertEqual(result["scenario_count"], 12)
        self.assertEqual(len(result["scenarios"]), 12)

    def test_strict_floor_equality_does_not_invalidate(self):
        result = analyze(FIXTURE)
        row = next(x for x in result["scenarios"]
                   if x["critical_health_minimum"] == 80 and x["maximum_health_loss"] == 5)
        self.assertEqual(row["hard_minimum"], 95)
        self.assertEqual(row["first_observed_below"], 54.8)
        self.assertEqual(row["health_at_sample"], 94)

    def test_crossing_at_90_is_only_seen_after_return_boundary(self):
        result = analyze(FIXTURE)
        row = next(x for x in result["scenarios"]
                   if x["critical_health_minimum"] == 90 and x["maximum_health_loss"] == 10)
        self.assertEqual(row["hard_minimum"], 90)
        self.assertEqual(row["first_observed_below"], 56.4)
        self.assertEqual(row["timing"], "SAMPLED_AT_OR_AFTER_RETURN_BOUNDARY")

    def test_high_floor_detects_first_sampled_change(self):
        result = analyze(FIXTURE)
        row = next(x for x in result["scenarios"]
                   if x["critical_health_minimum"] == 80 and x["maximum_health_loss"] == 0)
        self.assertEqual(row["first_observed_below"], 47.0)
        self.assertEqual(row["timing"], "SAMPLED_DURING_PENDING_INTERVAL")

    def test_sparse_ammo_is_not_claimed_as_joint_guard(self):
        self.assertEqual(analyze(FIXTURE)["ammo_guard_disposition"],
                         "NOT_REPLAYED_SPARSE_SELECTED_SAMPLES")

    def test_independent_audit_accepts_result(self):
        self.assertEqual(audit(FIXTURE, analyze(FIXTURE)), [])

    def test_audit_rejects_threshold_result_mutation(self):
        changed = json.loads(json.dumps(analyze(FIXTURE)))
        changed["scenarios"][0]["first_observed_below"] = 44.6
        self.assertIn("SCENARIO_RECOMPUTATION", audit(FIXTURE, changed))

    def test_audit_rejects_ammo_scope_overclaim(self):
        changed = json.loads(json.dumps(analyze(FIXTURE)))
        changed["ammo_guard_disposition"] = "PASS"
        self.assertIn("AMMO_SCOPE", audit(FIXTURE, changed))


if __name__ == "__main__":
    unittest.main()
