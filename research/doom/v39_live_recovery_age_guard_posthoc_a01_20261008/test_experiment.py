import unittest

from audit_result import check
from run_experiment import run
from source.observable_signal_guard_v2 import ObservableSignalGuard


class AgeGuardPosthocTests(unittest.TestCase):
    def test_frozen_a14_cases_separate_expiry_from_hard_crossing(self):
        result = run()
        self.assertEqual(len(result["cases"]), 2)
        for row in result["cases"]:
            self.assertEqual(row["retained_outcomes"]["health"],
                             {"status": "UNKNOWN", "reason": "source_expired"})
            self.assertEqual(row["retained_outcomes"]["ammo"],
                             {"status": "UNKNOWN", "reason": "source_expired"})
            self.assertEqual(row["same_samples_age_cap_30000ms"]["health"]["status"],
                             "UNCHANGED")
            self.assertEqual(row["same_samples_age_cap_30000ms"]["ammo"]["status"],
                             "SOFT_CHANGED")
            self.assertEqual(row["health_below_hard_minimum_age_cap_30000ms"]["status"],
                             "HARD_INVALIDATED")
            self.assertEqual(row["health_below_hard_minimum_while_expired"],
                             {"status": "UNKNOWN", "reason": "source_expired",
                              "requires_new_decision": True,
                              "keep_existing_policy": False})

    def test_expiry_boundary_is_strictly_greater_than_cap(self):
        binding = {"surface": 1}
        source = {"status": "observed", "signal_id": "health", "value": 79,
                  "sequence": 1, "capture_ns": 1_000_000_000,
                  "binding": binding}
        spec = {"op": "observable_signal_guard", "guard_id": "boundary",
                "source_sequence": 1, "signal_id": "health", "source_value": 79,
                "hard_minimum": 69, "max_source_age_ms": 1500,
                "on_soft_change": "preserve_existing_policy",
                "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}
        guard = ObservableSignalGuard(spec, source, binding)
        exact = {"status": "observed", "signal_id": "health", "value": 79,
                 "sequence": 2, "capture_ns": 2_500_000_000,
                 "binding": binding}
        plus_one_ns = dict(exact, capture_ns=2_500_000_001)
        self.assertEqual(guard.evaluate(exact)["status"], "UNCHANGED")
        expired = guard.evaluate(plus_one_ns)
        self.assertEqual((expired["status"], expired["reason"]),
                         ("UNKNOWN", "source_expired"))

    def test_independent_result_audit(self):
        run()
        # Audit consumes the persisted result, so exercise it after writing it.
        from pathlib import Path
        import json
        (Path(__file__).parent / "RESULT.json").write_text(
            json.dumps(run(), indent=2) + "\n", encoding="utf-8")
        self.assertEqual(check()["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
