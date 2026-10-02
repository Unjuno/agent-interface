import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent


class RetrievalOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_path = ROOT / "fixture.json"
        cls.candidate_path = ROOT / "candidate.py"
        cls.fixture = json.loads(cls.fixture_path.read_text(encoding="utf-8"))
        cls.raw = candidate.run(cls.fixture)
        cls.raw["fixture_sha256"] = candidate.sha256(cls.fixture_path)
        cls.raw["candidate_sha256"] = candidate.sha256(cls.candidate_path)

    def row(self, case_id, method):
        return next(x for x in self.raw["cases"] if x["case_id"] == case_id)["methods"][method]

    def test_fixed_topk_starves_k_plus_one_but_never_claims_global_none(self):
        row = self.row("valid_rank_k_plus_1", "SEMANTIC_TOP_K_THEN_FILTER")
        self.assertEqual(row["selected"], [])
        self.assertEqual(row["status"], "UNKNOWN_NOT_FOUND_WITHIN_BUDGET")

    def test_exhaustive_filter_recovers_every_known_valid_skill(self):
        by_id = {r["case_id"]: r for r in self.raw["cases"]}
        for case in self.fixture["cases"]:
            expected = [x[0] for x in case["skills"] if x[1] == "ALLOW"][:2]
            self.assertEqual(by_id[case["case_id"]]["methods"]["FILTER_THEN_RANK"]["selected"], expected)

    def test_bounded_widening_edge_and_budget(self):
        self.assertEqual(self.row("valid_rank_budget_edge_6", "BOUNDED_WIDENING")["selected"], ["s6"])
        self.assertEqual(self.row("valid_beyond_budget_7", "BOUNDED_WIDENING")["status"], "UNKNOWN_NOT_FOUND_WITHIN_BUDGET")

    def test_unresolved_candidate_is_not_mislabeled_absent(self):
        self.assertEqual(self.row("unknown_only", "FILTER_THEN_RANK")["status"], "UNKNOWN_APPLICABILITY_UNRESOLVED")

    def test_full_registry_known_empty_is_distinguished(self):
        self.assertEqual(self.row("no_eligible_skill", "FILTER_THEN_RANK")["status"], "NONE_PROVEN_APPLICABLE")

    def test_independent_auditor_accepts_baseline_and_rejects_mutations(self):
        baseline = audit.audit(self.fixture, self.raw, self.fixture_path, self.candidate_path)
        self.assertEqual(baseline["status"], "METHOD_PASS_SCOPED")
        mutations = []
        for raw_mutant in [
            {**self.raw, "cases": self.raw["cases"][:-1]},
            {**self.raw, "retrieval_k": 999},
            {**self.raw, "fixture_sha256": "0" * 64},
        ]:
            mutations.append(raw_mutant)
        unsafe = json.loads(json.dumps(self.raw))
        unsafe["cases"][0]["methods"]["SEMANTIC_TOP_K_THEN_FILTER"]["selected"] = ["s2"]
        mutations.append(unsafe)
        false_absence = json.loads(json.dumps(self.raw))
        false_absence["cases"][2]["methods"]["BOUNDED_WIDENING"]["status"] = "NONE_PROVEN_APPLICABLE"
        mutations.append(false_absence)
        false_work = json.loads(json.dumps(self.raw))
        false_work["cases"][0]["methods"]["FILTER_THEN_RANK"]["metadata_checks"] = 1
        mutations.append(false_work)
        rejected = 0
        for mutant in mutations:
            result = audit.audit(self.fixture, mutant, self.fixture_path, self.candidate_path)
            rejected += result["status"] == "FAIL_AUDIT"
        self.assertEqual(rejected, len(mutations))


if __name__ == "__main__":
    unittest.main()


