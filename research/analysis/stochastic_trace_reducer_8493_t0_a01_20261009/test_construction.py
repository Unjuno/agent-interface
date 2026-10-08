import json
import unittest
from pathlib import Path

import spec


HERE = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))

    def test_only_optional_warmup_is_removed_and_authority_remains(self):
        f = self.fixture
        removed = [event for event in f["base_trace"] if event not in f["reduced_trace"]]
        self.assertEqual(removed, ["warmup"])
        self.assertTrue(spec.legal(f["base_trace"], f))
        self.assertTrue(spec.legal(f["reduced_trace"], f))
        self.assertEqual(f["same_exit_code"], 17)
        self.assertNotEqual(f["target_fingerprint"], f["competing_fingerprint"])

    def test_preregistered_cases_cover_shift_and_required_controls(self):
        roles = [case["role"] for case in self.fixture["cases"]]
        self.assertEqual(roles.count("negative_control"), 1)
        self.assertEqual(roles.count("planted_harmful_regime"), 2)
        self.assertIn("insufficient_support_control", roles)
        self.assertIn("transition_ambiguity_control", roles)
        self.assertIn("fingerprint_identity_control", roles)
        self.assertEqual(sum(1 + len(c["windows"]) for c in self.fixture["cases"]),
                         self.fixture["familywise_contrasts"])

    def test_seed_schedules_are_disjoint_and_temporally_ordered(self):
        seeds, slots = [], []
        for case in self.fixture["cases"]:
            previous_end = -1
            for window in case["windows"]:
                self.assertGreaterEqual(window["start"], previous_end)
                previous_end = window["start"] + window["n"]
                seeds.extend(range(window["seed_start"], window["seed_start"] + window["n"]))
                slots.extend(range(window["start"], window["start"] + window["n"]))
        self.assertEqual(len(seeds), len(set(seeds)))
        for case in self.fixture["cases"]:
            case_slots = [s for w in case["windows"] for s in range(w["start"], w["start"]+w["n"])]
            self.assertEqual(case_slots, sorted(case_slots))

    def test_fixed_design_has_enough_competitor_identity_controls(self):
        case = next(c for c in self.fixture["cases"] if c["role"] == "fingerprint_identity_control")
        rows = []
        for window in case["windows"]:
            for seed in range(window["seed_start"], window["seed_start"]+window["n"]):
                rows.append(spec.response(self.fixture["base_trace"], seed, window, self.fixture)["fingerprint"])
        self.assertGreater(sum(x == self.fixture["competing_fingerprint"] for x in rows), 0)

    def test_paired_interval_and_decision_boundaries(self):
        alpha = spec.alpha_tail(self.fixture)
        null = {"n": 512, "base_target": 400, "reduced_target": 400,
                "gains": 0, "losses": 0, "competitor_rows": 0}
        interval = spec.risk_difference_interval(null, alpha)
        self.assertLessEqual(interval["lower"], 0)
        self.assertGreaterEqual(interval["upper"], 0)
        self.assertEqual(spec.decision(interval, self.fixture["noninferiority_margin"]), "PASS_NONINFERIOR")
        harmful = {"n": 256, "base_target": 200, "reduced_target": 40,
                   "gains": 0, "losses": 160, "competitor_rows": 0}
        self.assertEqual(spec.decision(spec.risk_difference_interval(harmful, alpha),
                                       self.fixture["noninferiority_margin"]), "FAIL_NONINFERIORITY")


if __name__ == "__main__":
    unittest.main()
