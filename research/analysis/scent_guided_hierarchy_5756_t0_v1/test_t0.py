"""Contract and independent-auditor mutation checks for Issue #5756 T0."""

import copy
import json
import unittest
from pathlib import Path

from audit import audit, audit_one
from runner import run


ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))


class T0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {"protocol": SPEC["protocol"], "result_count": 25,
                   "results": run(SPEC)}

    def test_all_five_arms_run_on_all_five_frozen_fixtures(self):
        report = audit(SPEC, self.raw)
        self.assertEqual("PASS_METHOD_SCOPED", report["status"])
        self.assertEqual(25, report["audited_rows"])
        self.assertTrue(report["all_forbidden_effects_zero"])

    def test_scent_and_exhaustive_find_target_and_refuse_unsafe_edge(self):
        for policy in ("scent_backtrack", "exhaustive"):
            row = next(r for r in self.raw["results"]
                       if r["fixture_id"] == "misleading_epoch_recovery" and r["policy"] == policy)
            self.assertTrue(row["claim"]["found"])
            self.assertTrue(any(e["kind"] == "REFUSE_UNSAFE" for e in row["trace"]))
            backs = [i for i, e in enumerate(row["trace"]) if e["kind"] == "BACKTRACK"]
            self.assertTrue(backs)
            self.assertEqual(1, row["trace"][backs[0] + 1]["observation"]["epoch"])

    def test_no_target_and_no_safe_path_are_not_false_successes(self):
        for fixture_id in ("no_target", "no_safe_path"):
            for row in (r for r in self.raw["results"] if r["fixture_id"] == fixture_id):
                self.assertFalse(row["claim"]["found"])
        no_safe = next(r for r in self.raw["results"]
                       if r["fixture_id"] == "no_safe_path" and r["policy"] == "scent_backtrack")
        self.assertEqual("NO_SAFE_PATH", no_safe["eligibility"])
        self.assertEqual(0, no_safe["cost"]["forbidden_effects"])

    def test_direct_search_is_marked_only_where_exposed_and_budget_is_bounded(self):
        direct = [r for r in self.raw["results"] if r["policy"] == "direct_search"]
        self.assertTrue(any(r["fixture_id"] == "direct_search_available" and r["claim"]["found"] for r in direct))
        self.assertTrue(any(r["eligibility"] == "NOT_APPLICABLE_DIRECT_SEARCH_UNAVAILABLE" for r in direct))
        exhausted = [r for r in self.raw["results"] if r["fixture_id"] == "budget_exhaustion"]
        self.assertTrue(any(not r["claim"]["found"] and r["budget_remaining"] == 0 for r in exhausted))

    def test_auditor_rejects_hidden_label_leak_mutation(self):
        row = next(r for r in self.raw["results"] if r["fixture_id"] == "misleading_epoch_recovery" and r["policy"] == "scent_backtrack")
        mutated = copy.deepcopy(row)
        observation = next(e["observation"] for e in mutated["trace"] if e["kind"] == "OBSERVE")
        observation["target_oracle"] = "export_screen"
        mutated["environment_events"] = copy.deepcopy(mutated["trace"])
        fixture = next(f for f in SPEC["fixtures"] if f["id"] == row["fixture_id"])
        with self.assertRaisesRegex(AssertionError, "schema leak"):
            audit_one(fixture, mutated, SPEC["budget"], SPEC["task"])

    def test_auditor_rejects_omitted_visited_branch_mutation(self):
        row = next(r for r in self.raw["results"] if r["fixture_id"] == "misleading_epoch_recovery" and r["policy"] == "scent_backtrack")
        mutated = copy.deepcopy(row)
        index = next(i for i, e in enumerate(mutated["trace"]) if e["kind"] == "NAVIGATE")
        mutated["trace"].pop(index)
        fixture = next(f for f in SPEC["fixtures"] if f["id"] == row["fixture_id"])
        with self.assertRaises(AssertionError):
            audit_one(fixture, mutated, SPEC["budget"], SPEC["task"])

    def test_auditor_rejects_altered_epoch_mutation(self):
        row = next(r for r in self.raw["results"] if r["fixture_id"] == "misleading_epoch_recovery" and r["policy"] == "exhaustive")
        mutated = copy.deepcopy(row)
        observation = next(e["observation"] for e in mutated["trace"] if e["kind"] == "OBSERVE" and e["observation"]["epoch"] == 1)
        observation["epoch"] = 7
        mutated["environment_events"] = copy.deepcopy(mutated["trace"])
        fixture = next(f for f in SPEC["fixtures"] if f["id"] == row["fixture_id"])
        with self.assertRaisesRegex(AssertionError, "visible node/epoch"):
            audit_one(fixture, mutated, SPEC["budget"], SPEC["task"])

    def test_auditor_rejects_wrong_target_counted_as_success_mutation(self):
        row = next(r for r in self.raw["results"] if r["fixture_id"] == "misleading_epoch_recovery" and r["policy"] == "strongest_cue")
        mutated = copy.deepcopy(row)
        mutated["trace"] = [copy.deepcopy(e) for e in row["trace"][:4]]
        mutated["environment_events"] = copy.deepcopy(mutated["trace"])
        mutated["claim"] = {"found": True, "screen_id": "decoy_screen"}
        mutated["final_screen"] = "decoy_screen"
        mutated["budget_remaining"] = 8
        mutated["cost"] = {"api_calls": 4, "observations": 2, "navigation": 1,
                            "backtracks": 0, "forbidden_effects": 0}
        fixture = next(f for f in SPEC["fixtures"] if f["id"] == row["fixture_id"])
        with self.assertRaisesRegex(AssertionError, "independent oracle"):
            audit_one(fixture, mutated, SPEC["budget"], SPEC["task"])


if __name__ == "__main__":
    unittest.main()

