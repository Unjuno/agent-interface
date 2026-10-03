"""Construction tests only: the allocation runner does not execute this suite."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


def case(**changes):
    value = {
        "case_id": "probe", "opportunity": {"onset_ms": 9, "expiry_ms": 20},
        "capture_schedule_ms": [10, 50], "observation_horizon_ms": 60,
        "clock_synchronized": True, "delivery_latency_ms": 1,
        "decision_latency_ms": 1, "effect_latency_ms": 0,
        "effect_enabled": True, "safe_stop": False,
    }
    value.update(changes)
    return value


class ContractTests(unittest.TestCase):
    def load(self, name):
        path = ROOT / (name + ".py")
        self.assertTrue(path.is_file(), "missing implementation: " + name)
        spec = importlib.util.spec_from_file_location("a05_" + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_onset_only_intervention_changes_acquisition(self):
        # Ignoring onset or accepting a supplied capture label breaks this contrast.
        model = self.load("candidate")
        hit = model.evaluate(case())
        miss = model.evaluate(case(opportunity={"onset_ms": 11, "expiry_ms": 20}))
        self.assertEqual(hit["sampled_capture_ms"], [10])
        self.assertEqual(hit["boundary"], "eligible_effect_in_model")
        self.assertEqual(miss["sampled_capture_ms"], [])
        self.assertEqual(miss["boundary"], "not_acquired")

    def test_closed_interval_zero_latency_at_expiry(self):
        row = self.load("candidate").evaluate(case(
            opportunity={"onset_ms": 10, "expiry_ms": 10},
            delivery_latency_ms=0, decision_latency_ms=0))
        self.assertEqual(row["sampled_capture_ms"], [10])
        self.assertEqual(row["stages_ms"], {"delivery": 10, "decision": 10,
                                          "effect": 10, "safe_stop": None})
        self.assertEqual(row["boundary"], "eligible_effect_in_model")

    def test_late_delivery_and_decision_are_distinct(self):
        model = self.load("candidate")
        self.assertEqual(model.evaluate(case(delivery_latency_ms=11))["boundary"],
                         "acquired_not_delivered")
        self.assertEqual(model.evaluate(case(decision_latency_ms=10))["boundary"],
                         "delivered_no_decision")

    def test_effect_may_arrive_after_expiry_but_not_after_horizon(self):
        model = self.load("candidate")
        late = model.evaluate(case(effect_latency_ms=10))
        self.assertEqual(late["stages_ms"]["effect"], 22)
        self.assertEqual(late["boundary"], "eligible_effect_in_model")
        censored = model.evaluate(case(effect_latency_ms=10, observation_horizon_ms=15))
        self.assertIsNone(censored["stages_ms"]["effect"])
        self.assertEqual(censored["boundary"], "UNKNOWN")

    def test_safe_stop_suppresses_effect(self):
        row = self.load("candidate").evaluate(case(safe_stop=True))
        self.assertEqual(row["stages_ms"]["safe_stop"], 12)
        self.assertIsNone(row["simulated_effect_token"])
        self.assertEqual(row["reason"], "safe_stop")

    def test_no_cue_and_unsynchronized_clock(self):
        model = self.load("candidate")
        self.assertEqual(model.evaluate(case(opportunity=None))["boundary"], "NOT_APPLICABLE")
        row = model.evaluate(case(clock_synchronized=False))
        self.assertEqual(row["boundary"], "UNKNOWN")
        self.assertIsNone(row["stages_ms"]["effect"])

    def test_integer_domain_and_input_custody(self):
        model = self.load("candidate")
        bad = [case(effect_latency_ms=True), case(delivery_latency_ms=1.0),
               case(capture_schedule_ms=[50, 10]), case(effect_latency_ms=-1),
               case(opportunity={"onset_ms": 21, "expiry_ms": 20}),
               case(captures=[{"at_ms": 10}]), case(expected_boundary="eligible_effect")]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.evaluate(value)

    def test_fixture_is_134_cells_plus_13_controls_without_labels(self):
        fixture = self.load("prepare").fixture()
        self.assertEqual(len(fixture["cases"]), 147)
        self.assertEqual(len({c["case_id"] for c in fixture["cases"]}), 147)
        cells = [c for c in fixture["cases"] if c["case_id"].startswith("grid-")]
        self.assertEqual(len(cells), 134)
        self.assertNotIn('"captures"', json.dumps(fixture))
        self.assertNotIn('"expected_boundary"', json.dumps(fixture))
        by_id = {c["case_id"]: c for c in fixture["cases"]}
        left, right = copy.deepcopy(by_id["grid-e20-o09"]), copy.deepcopy(by_id["grid-e20-o11"])
        for c in (left, right):
            c.pop("case_id")
            c["opportunity"].pop("onset_ms")
        self.assertEqual(left, right)

    def test_independent_oracle_handles_fixed_duration_pair(self):
        oracle = self.load("audit")
        for interval, boundary in [((9, 11), "eligible_effect_in_model"),
                                   ((11, 13), "not_acquired")]:
            row = oracle.expected_row(case(
                opportunity={"onset_ms": interval[0], "expiry_ms": interval[1]},
                delivery_latency_ms=0, decision_latency_ms=0))
            self.assertEqual(row["boundary"], boundary)

    def test_full_auditor_rejects_ten_copied_output_corruptions(self):
        fixture = self.load("prepare").fixture()
        raw = self.load("candidate").run(fixture)
        audit = self.load("audit")
        self.assertEqual(audit.errors(fixture, raw), [])
        mutants = audit.mutants(raw)
        self.assertEqual(len(mutants), 10)
        for name, mutated in mutants:
            with self.subTest(mutation=name):
                self.assertTrue(audit.errors(fixture, mutated))

    def test_auditor_rejects_fixture_changes_and_bool_time_alias(self):
        fixture = self.load("prepare").fixture()
        raw = self.load("candidate").run(fixture)
        audit = self.load("audit")
        changed = copy.deepcopy(fixture)
        changed["cases"][0]["effect_latency_ms"] = 1
        self.assertTrue(audit.errors(changed, raw))
        changed = copy.deepcopy(raw)
        changed["rows"][0]["stages_ms"]["delivery"] = True
        self.assertTrue(audit.errors(fixture, changed))

    def test_legacy_probe_validates_only_onset_changes(self):
        result = self.load("legacy_probe").probe()
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual([r["output"][0] for r in result["rows"]],
                         ["eligible_effect", "eligible_effect", "not_acquired", "not_acquired"])
        self.assertEqual(self.load("audit").legacy_errors(result), [])
        corrupted = copy.deepcopy(result)
        corrupted["rows"][1]["input"]["captures"][0]["opportunity_ids"] = []
        self.assertTrue(self.load("audit").legacy_errors(corrupted))


if __name__ == "__main__":
    unittest.main()
