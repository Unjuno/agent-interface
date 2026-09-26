from __future__ import annotations

import json
import pathlib
import unittest

from model import Calibration, Decision, Invalidation, final_action_admission


ROOT = pathlib.Path(__file__).resolve().parents[1]
CALIBRATION_PATH = pathlib.Path(__import__("os").environ.get(
    "POLICY_CLOCK_CALIBRATION",
    ROOT / "map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-02/runtime/lease-clock-calibration.json",
))


class PolicyInvalidationClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        record = json.loads(CALIBRATION_PATH.read_text())
        cls.calibration = Calibration(
            session_id="v10-seed-990637",
            host_domain="host.perf_counter_ns",
            runtime_domain="container.perf_counter_ns",
            offset_lower_ns=record["offset_lower_ns"],
            offset_upper_ns=record["offset_upper_ns"],
        )

    def setUp(self):
        self.invalidation = Invalidation(
            "v10-seed-990637", "hard-health-invalidation-8", "health_below_floor",
            "host.perf_counter_ns", 8_494_950_000_000,
        )
        # The retained calibration is approximately runtime = host - 739 ms.
        self.decision = Decision(
            "v10-seed-990637", "decision-8", "container.perf_counter_ns",
            7_755_780_000_000, True,
        )

    def test_unadapted_mixed_domain_comparison_raises(self):
        with self.assertRaisesRegex(ValueError, "incomparable clock domains"):
            final_action_admission(self.invalidation, self.decision)

    def test_translated_invalidation_is_preserved_and_rejected_without_input(self):
        result = final_action_admission(self.invalidation, self.decision, self.calibration)
        self.assertEqual(result.status, "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(result.admitted)
        self.assertEqual(result.executor_input_calls, 0)
        self.assertEqual(result.receipt.outcome_evaluated_host_ns,
                         self.invalidation.outcome_evaluated_host_ns)
        self.assertEqual(result.receipt.runtime_domain, self.decision.runtime_domain)
        self.assertLessEqual(result.receipt.outcome_evaluated_runtime_ns,
                             self.decision.decided_runtime_ns)

    def test_wrong_or_stale_calibration_fails_closed(self):
        stale = Calibration("other-session", "host.perf_counter_ns",
                            "container.perf_counter_ns",
                            self.calibration.offset_lower_ns,
                            self.calibration.offset_upper_ns)
        with self.assertRaisesRegex(ValueError, "stale or wrong-session"):
            final_action_admission(self.invalidation, self.decision, stale)

    def test_overwide_calibration_fails_closed(self):
        wide = Calibration("v10-seed-990637", "host.perf_counter_ns",
                           "container.perf_counter_ns", -739_000_000,
                           -736_000_000)
        with self.assertRaisesRegex(ValueError, "over-wide"):
            final_action_admission(self.invalidation, self.decision, wide)

    def test_invalidation_after_decision_is_not_relabelled_as_rejection(self):
        late = Invalidation("v10-seed-990637", "late", "health_below_floor",
                            "host.perf_counter_ns", 8_500_000_000_000)
        with self.assertRaisesRegex(ValueError, "follows controller decision"):
            final_action_admission(late, self.decision, self.calibration)


if __name__ == "__main__":
    unittest.main(verbosity=2)
