import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent
SCENARIOS = json.loads((ROOT / "scenarios.json").read_text())


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.run(SCENARIOS)

    def test_candidate_matrix_has_unique_rows(self):
        rows = self.raw["rows"]
        self.assertEqual(len(rows), 36)
        self.assertEqual(len({(r["scenario_id"], r["policy"]) for r in rows}), 36)

    def test_independent_reconstruction(self):
        result = auditor.audit(self.raw, SCENARIOS)
        self.assertEqual(result["errors"], [])

    def test_bounded_inheritance_improves_direct_inversion(self):
        rows = {(r["scenario_id"], r["policy"]): r for r in self.raw["rows"]}
        self.assertTrue(rows[("direct_cap_at_need", "DEADLINE_ONLY")]["verifier_deadline_miss"])
        self.assertFalse(rows[("direct_cap_at_need", "COMPOSED_BOUNDED_PI")]["verifier_deadline_miss"])
        cases = {c["id"]: c for c in SCENARIOS["scenarios"]}
        misses = {policy: sum(r["verifier_deadline_miss"] for r in self.raw["rows"]
                              if r["policy"] == policy and cases[r["scenario_id"]]["expected_inversion"])
                  for policy in candidate.POLICIES}
        self.assertEqual(misses["DEADLINE_ONLY"], 7)
        self.assertEqual(misses["COMPOSED_BOUNDED_PI"], 6)

    def test_composed_arm_never_admits_after_its_deadline(self):
        for row in self.raw["rows"]:
            if row["policy"] == "COMPOSED_BOUNDED_PI":
                self.assertFalse(row["verifier_status"] == "ADMITTED_FRESH" and row["verifier_deadline_miss"])

    def test_naive_negative_controls_expose_cycle_and_forgery(self):
        rows = {(r["scenario_id"], r["policy"]): r for r in self.raw["rows"]}
        self.assertTrue(rows[("cycle_attempt", "NAIVE_UNBOUNDED_PI")]["cycle_edge_admitted"])
        self.assertGreater(sum(rows[("forged_urgency", "NAIVE_UNBOUNDED_PI")]["boost_ticks"].values()), 0)

    def test_cycle_and_unauthenticated_claim_fail_closed(self):
        rows = {(r["scenario_id"], r["policy"]): r for r in self.raw["rows"]}
        self.assertFalse(rows[("cycle_attempt", "COMPOSED_BOUNDED_PI")]["cycle_edge_admitted"])
        forged = rows[("forged_urgency", "COMPOSED_BOUNDED_PI")]
        self.assertEqual(sum(forged["boost_ticks"].values()), 0)

    def test_cap_yields_to_eligible_medium_service(self):
        row = next(r for r in self.raw["rows"] if r["scenario_id"] == "cap_then_medium_service" and r["policy"] == "COMPOSED_BOUNDED_PI")
        self.assertIsNotNone(row["inheritance_cap_tick"])
        self.assertEqual(row["medium_first_service_delay_after_cap"], 0)

    def test_cancellation_releases_and_verifier_does_not_overclaim(self):
        row = next(r for r in self.raw["rows"] if r["scenario_id"] == "holder_cancel_releases" and r["policy"] == "COMPOSED_BOUNDED_PI")
        self.assertTrue(row["holder_cancelled_and_released"])
        self.assertEqual(row["verifier_status"], "ADMITTED_FRESH")

    def test_expiry_ends_inheritance_and_drains_resources(self):
        row = next(r for r in self.raw["rows"] if r["scenario_id"] == "claim_expires" and r["policy"] == "COMPOSED_BOUNDED_PI")
        self.assertFalse(row["resource_r1_held_at_end"])
        self.assertFalse(row["resource_r2_held_at_end"])
        self.assertFalse(any(e.get("kind") == "RUN" and e.get("inherited") and e["tick"] >= 0 for e in row["events"]))
        self.assertEqual(row["verifier_status"], "UNKNOWN_STALE")

    def test_nine_mutation_controls_are_rejected(self):
        mutations = []
        changed = copy.deepcopy(self.raw); changed["rows"][0]["verifier_finish_tick"] = 99; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"][0]["verifier_status"] = "ADMITTED_FRESH"; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"][2]["cycle_edge_admitted"] = True; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"][17]["boost_ticks"]["L"] = 1; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"][9]["holder_cancelled_and_released"] = False; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"][0]["events"] = []; mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"].append(copy.deepcopy(changed["rows"][0])); mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["rows"].pop(); mutations.append(changed)
        changed = copy.deepcopy(self.raw); changed["allocation_id"] = "other"; mutations.append(changed)
        for i, mutated in enumerate(mutations):
            with self.subTest(control=i):
                self.assertTrue(auditor.audit(mutated, SCENARIOS)["errors"])


if __name__ == "__main__":
    unittest.main()
