from __future__ import annotations

import json
import pathlib
import unittest
import sys

from model import Calibration, Decision, Invalidation, final_action_admission


ROOT = pathlib.Path(__file__).resolve().parents[1]
CALIBRATION_PATH = pathlib.Path(__import__("os").environ.get(
    "POLICY_CLOCK_CALIBRATION",
    ROOT / "map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-02/runtime/lease-clock-calibration.json",
))
LIVE_CONTROL = pathlib.Path(__import__("os").environ.get(
    "POLICY_CLOCK_LIVE_CONTROL", "/evidence/live_control"))
sys.path.insert(0, str(LIVE_CONTROL))
from final_action_admission_v1 import decide_final_admission  # noqa: E402


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

    def test_actual_final_admission_v1_reproduces_predecessor_exception(self):
        terminal = {"turn_id": "turn-8", "status": "interrupted",
                    "answer_eligible": False, "terminal_observed_ns": 7_755_779_900_000}
        # Host timestamp is roughly 739 ms ahead of runtime time; the unchanged
        # production path compares it directly with the runtime decision value.
        host_invalidation = {
            "outcome_evaluated_ns": self.invalidation.outcome_evaluated_host_ns,
            "outcome": {"status": "INVALIDATED", "requires_new_decision": True,
                        "grants_input_authority": False, "reason": "hard_health"},
        }
        with self.assertRaisesRegex(ValueError, "controller decision precedes observed boundary"):
            decide_final_admission(terminal, host_invalidation,
                                   self.decision.decided_runtime_ns)

    def test_actual_final_admission_v1_rejects_translated_invalidation_no_authority(self):
        terminal = {"turn_id": "turn-8", "status": "interrupted",
                    "answer_eligible": False, "terminal_observed_ns": 7_755_779_900_000}
        translated = self.calibration.host_to_runtime(
            self.invalidation.outcome_evaluated_host_ns, self.decision.session_id)
        receipt = {"outcome_evaluated_ns": translated,
                   "outcome_evaluated_host_ns": self.invalidation.outcome_evaluated_host_ns,
                   "outcome_evaluated_runtime_ns": translated,
                   "outcome": {"status": "INVALIDATED", "requires_new_decision": True,
                               "grants_input_authority": False, "reason": "hard_health"}}
        result = decide_final_admission(terminal, receipt,
                                       self.decision.decided_runtime_ns)
        self.assertEqual(result["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertIs(result["input_authority_admitted"], False)
        self.assertIsNone(result["executor_admission"])
        self.assertEqual(result["policy_invalidation"]["outcome_evaluated_host_ns"],
                         self.invalidation.outcome_evaluated_host_ns)
        self.assertEqual(result["policy_invalidation"]["outcome_evaluated_runtime_ns"],
                         translated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
