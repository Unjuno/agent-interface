import copy
import unittest

from experiment import build_result, frozen_cases
from auditor import audit_result
from oracle import independent_oracle


class CegarExperimentTests(unittest.TestCase):
    def test_heldout_false_admissions_drop_without_increasing_false_rejections(self):
        result = build_result(frozen_cases(), independent_oracle)
        comparison = result["comparison"]
        self.assertGreater(comparison["coarse"]["heldout_false_admissions"], 0)
        self.assertEqual(comparison["cegar"]["heldout_false_admissions"], 0)
        self.assertEqual(comparison["cegar"]["heldout_false_rejections"], 0)

    def test_malformed_and_ambiguous_holdouts_remain_unknown(self):
        result = build_result(frozen_cases(), independent_oracle)
        for row in result["rows"]:
            if row["split"] == "heldout" and row["oracle"] == "UNKNOWN":
                self.assertEqual(row["cegar"], "UNKNOWN")

    def test_full_fixed_ontology_matches_the_independent_oracle_on_every_case(self):
        result = build_result(frozen_cases(), independent_oracle)
        self.assertTrue(all(row["full_oracle"] == row["oracle"] for row in result["rows"]))

    def test_cegar_uses_fewer_checks_than_the_frozen_over_specific_control(self):
        result = build_result(frozen_cases(), independent_oracle)
        self.assertLess(result["check_counts"]["cegar_learned"], result["check_counts"]["over_specific_static"])
        self.assertEqual(result["comparison"]["cegar"]["heldout"]["false_rejections"], 0)
        self.assertGreater(result["comparison"]["over_specific"]["heldout"]["false_rejections"], 0)

    def test_candidate_is_deterministic_for_the_same_frozen_input(self):
        cases = frozen_cases()
        self.assertEqual(build_result(cases, independent_oracle), build_result(cases, independent_oracle))

    def test_every_learned_check_has_replayable_training_lineage(self):
        result = build_result(frozen_cases(), independent_oracle)
        self.assertEqual(set(result["learned_checks"]), {
            "target_current", "authority_current", "evidence_current", "effect_safe",
            "acyclic_dependencies",
        })
        self.assertEqual(audit_result(result, frozen_cases()), {"decision": "PASS", "errors": []})

    def test_audit_rejects_orphaned_refinement_lineage(self):
        result = build_result(frozen_cases(), independent_oracle)
        result["lineage"][0]["case_id"] = "not-a-frozen-case"
        self.assertIn("refinement_parent_missing", audit_result(result, frozen_cases())["errors"])

    def test_audit_rejects_decision_metric_lineage_authority_and_corpus_mutations(self):
        original_cases = frozen_cases()
        original = build_result(original_cases, independent_oracle)
        mutations = []
        candidate = copy.deepcopy(original)
        candidate["rows"][0]["cegar"] = "ADMIT" if candidate["rows"][0]["cegar"] != "ADMIT" else "REJECT"
        mutations.append((candidate, copy.deepcopy(original_cases), "cegar_mismatch"))
        candidate = copy.deepcopy(original)
        candidate["comparison"]["cegar"]["heldout"]["false_admissions"] += 1
        mutations.append((candidate, copy.deepcopy(original_cases), "comparison_metric_mismatch"))
        candidate = copy.deepcopy(original)
        candidate["rows"][0]["authority_granted"] = True
        mutations.append((candidate, copy.deepcopy(original_cases), "authority_claim"))
        candidate = copy.deepcopy(original)
        candidate["lineage"].pop()
        mutations.append((candidate, copy.deepcopy(original_cases), "refinement_sequence_mismatch"))
        changed_cases = copy.deepcopy(original_cases)
        changed_cases["heldout"][0]["target_current"] = False
        mutations.append((copy.deepcopy(original), changed_cases, "corpus_digest_mismatch"))
        for candidate, cases, expected_error in mutations:
            with self.subTest(expected_error=expected_error):
                self.assertTrue(any(expected_error in error for error in audit_result(candidate, cases)["errors"]))


if __name__ == "__main__":
    unittest.main()
