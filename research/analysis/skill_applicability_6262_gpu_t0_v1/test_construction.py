import itertools
import json
import unittest
from pathlib import Path


FIXTURE = json.loads(Path(__file__).with_name("FIXTURE.json").read_text(encoding="utf-8"))


class FrozenFixtureTests(unittest.TestCase):
    def test_factor_count_within_preregistered_range(self):
        self.assertGreaterEqual(len(FIXTURE["factors"]), 3)
        self.assertLessEqual(len(FIXTURE["factors"]), 5)

    def test_structural_constraint_is_separate_from_missing_trials(self):
        names = list(FIXTURE["factors"])
        all_rows = [dict(zip(names, values)) for values in itertools.product(*(FIXTURE["factors"][n] for n in names))]
        feasible = [r for r in all_rows if not (r["mode"] == "dialog" and r["target"] == "alternate")]
        observed = [{n: t[n] for n in names} for t in FIXTURE["trials"]]
        self.assertEqual(len(feasible), 12)
        self.assertEqual(len(observed), len(feasible))
        self.assertNotIn({"backend":"chromium","mode":"dialog","evidence":"current","target":"alternate"}, observed)

    def test_every_feasible_full_cell_has_exactly_one_trial(self):
        names = list(FIXTURE["factors"])
        cells = [dict(zip(names, values)) for values in itertools.product(*(FIXTURE["factors"][n] for n in names))]
        cells = [r for r in cells if not (r["mode"] == "dialog" and r["target"] == "alternate")]
        for cell in cells:
            self.assertEqual(sum(all(t[n] == cell[n] for n in names) for t in FIXTURE["trials"]), 1)

    def test_authority_is_not_route_capability(self):
        row = next(t for t in FIXTURE["trials"] if t["id"] == "t11")
        self.assertTrue(row["authority_grant"])
        self.assertFalse(row["route_qualified"])

    def test_misleading_count_and_narrow_control_are_preregistered(self):
        rows = FIXTURE["trials"]
        passed = sum(t["effect"] == "PASS" and t["route_qualified"] for t in rows)
        self.assertEqual(passed, 10)
        self.assertGreaterEqual(passed / len(rows), FIXTURE["flat_success_threshold"])
        self.assertEqual(FIXTURE["narrow_claim_trial"], "t01")


if __name__ == "__main__":
    unittest.main()
