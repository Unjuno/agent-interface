import copy
import json
import unittest
from pathlib import Path

from audit import audit_payload
from candidate import run


ROOT = Path(__file__).parent


def packet():
    visible = json.loads((ROOT / "visible.json").read_text(encoding="utf-8"))
    truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
    return visible, truth, run(visible)


class IndependentRegretAuditTests(unittest.TestCase):
    def test_equal_age_but_different_truth_yields_distinct_integrals(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        self.assertEqual([], report["errors"])
        stable = report["cases"]["age_tie_stable"]
        changed = report["cases"]["age_tie_changed"]
        self.assertEqual([3, 4, 5], stable["age_sequence"])
        self.assertEqual(stable["age_sequence"], changed["age_sequence"])
        self.assertEqual(0, stable["integrated_regret_units"])
        self.assertEqual(3, changed["integrated_regret_units"])
        self.assertEqual(report["comparator_cards"]["age_tie_stable"], report["comparator_cards"]["age_tie_changed"])
        self.assertEqual("PASS_METHOD_SCOPED", report["disposition"])

    def test_fresh_misleading_feedback_has_positive_regret(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        self.assertEqual([0], report["cases"]["fresh_misleading"]["age_sequence"])
        self.assertEqual(1, report["cases"]["fresh_misleading"]["integrated_regret_units"])

    def test_no_open_opportunity_is_not_scored_as_zero_evidence(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        case = report["cases"]["no_open_opportunity"]
        self.assertEqual("NOT_APPLICABLE", case["status"])
        self.assertIsNone(case["integrated_regret_units"])
        self.assertIsNone(report["comparator_cards"]["no_open_opportunity"]["age_only_sum"])

    def test_action_set_change_limits_regret_to_available_choices(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        self.assertEqual(2, report["cases"]["action_set_change"]["integrated_regret_units"])

    def test_unidentified_observation_causality_is_not_attributed(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        case = report["cases"]["causal_use_unidentified"]
        self.assertEqual("NOT_IDENTIFIED", case["causal_attribution"])
        self.assertEqual(0, case["integrated_regret_units"])

    def test_unknown_truth_or_clock_returns_unknown_without_scalar(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        case = report["cases"]["unknown_truth_clock"]
        self.assertEqual("UNKNOWN", case["status"])
        self.assertIsNone(case["integrated_regret_units"])

    def test_hard_safety_failure_remains_separate_from_regret(self):
        visible, truth, raw = packet()
        report = audit_payload(visible, truth, raw)
        case = report["cases"]["hard_safety_control"]
        self.assertEqual("FAIL_HARD_SAFETY", case["status"])
        self.assertIsNone(case["integrated_regret_units"])
        self.assertEqual(1, report["hard_safety_violations"])

    def test_mutations_are_rejected(self):
        visible, truth, raw = packet()
        cases = []

        changed = copy.deepcopy(truth)
        changed["cases"]["age_tie_changed"]["state_by_tick"]["3"] = "A"
        cases.append((visible, changed, raw))

        changed = copy.deepcopy(visible)
        next(x for x in changed["cases"] if x["case_id"] == "age_tie_changed")["ticks"][3]["opportunity_open"] = False
        cases.append((changed, truth, copy.deepcopy(raw)))

        changed = copy.deepcopy(visible)
        next(x for x in changed["cases"] if x["case_id"] == "action_set_change")["ticks"][0]["admissible_actions"] = ["A"]
        cases.append((changed, truth, copy.deepcopy(raw)))

        changed = copy.deepcopy(visible)
        next(x for x in changed["cases"] if x["case_id"] == "age_tie_changed")["ticks"][3]["clock_comparable"] = False
        cases.append((changed, truth, run(changed)))

        changed = copy.deepcopy(truth)
        changed["cases"]["hard_safety_control"]["hard_safety_event_ticks"] = []
        cases.append((visible, changed, raw))

        changed = copy.deepcopy(truth)
        changed["loss_table"]["A"]["B"] = 0
        cases.append((visible, changed, raw))

        changed = copy.deepcopy(visible)
        next(x for x in changed["cases"] if x["case_id"] == "causal_use_unidentified")["ticks"][0]["causal_use_identifiable"] = True
        cases.append((changed, truth, copy.deepcopy(raw)))

        names = ["truth_flip", "opportunity_close", "action_set_change", "clock_unknown", "safety_event_removed", "loss_mutation", "lineage_mutation"]
        for name, (mutated_visible, mutated_truth, mutated_raw) in zip(names, cases):
            with self.subTest(mutation=name):
                self.assertTrue(audit_payload(mutated_visible, mutated_truth, mutated_raw)["errors"])


if __name__ == "__main__":
    unittest.main()
