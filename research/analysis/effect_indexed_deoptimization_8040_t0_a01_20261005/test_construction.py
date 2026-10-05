"""Construction checks; these do not invoke formal command-line allocations."""
from __future__ import annotations

import copy
import unittest

from audit import audit_document
from build_fixture import build
from candidate import classify, run


class DeoptimizationConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.public, self.truth = build()
        self.output = run(self.public)
        self.audit = audit_document(self.public, self.truth, self.output)
        self.by_id = {row["case_id"]: row for row in self.output["rows"]}

    def test_every_frozen_case_matches_independent_reconstruction(self) -> None:
        self.assertEqual(len(self.public["cases"]), 12)
        self.assertEqual(self.audit["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(self.audit["independent_errors"], [])

    def test_verified_prefix_advances_cursor_without_authority(self) -> None:
        row = self.by_id["two_verified_prefix"]
        self.assertEqual(row["disposition"], "READY_AT_CURSOR")
        self.assertEqual(row["generic_cursor"], 2)
        self.assertEqual(row["verified_prefix"], ["prepare_record", "commit_record"])
        self.assertFalse(row["execution_authorized"])
        self.assertFalse(row["authority_extended"])

    def test_unknown_partial_and_stale_paths_yield(self) -> None:
        for case_id in ("unknown_first_effect", "unknown_after_verified_prefix", "stale_generation", "inside_one_to_many_lowering", "missing_map_entry", "misbound_receipt"):
            self.assertEqual(self.by_id[case_id]["disposition"], "YIELD_UNKNOWN", case_id)
        self.assertIsNone(self.by_id["unknown_after_verified_prefix"]["generic_cursor"])
        self.assertEqual(self.by_id["unknown_after_verified_prefix"]["verified_prefix"], ["prepare_record"])
        self.assertEqual(self.by_id["inside_one_to_many_lowering"]["verified_prefix"], ["prepare_record"])

    def test_known_no_effect_points_to_pending_semantic_operation(self) -> None:
        row = self.by_id["known_no_effect_pending"]
        self.assertEqual(row["disposition"], "RESOLUTION_REQUIRED_AT_CURSOR")
        self.assertEqual(row["generic_cursor"], 0)
        self.assertFalse(row["execution_authorized"])

    def test_end_of_macro_is_not_task_success(self) -> None:
        row = self.by_id["end_of_program_is_not_success"]
        self.assertEqual(row["disposition"], "CURSOR_AT_END_UNVERIFIED")
        self.assertEqual(row["generic_cursor"], 3)
        self.assertFalse(row["completion_claim"])

    def test_candidate_fails_closed_on_input_mutations(self) -> None:
        base = self.public["cases"][1]
        stale = copy.deepcopy(base)
        stale["observation_generation"] = "old"
        self.assertEqual(classify(self.public, stale)["disposition"], "YIELD_UNKNOWN")
        unknown_pc = copy.deepcopy(base)
        unknown_pc["specialized_pc"] = "not-a-map-entry"
        self.assertEqual(classify(self.public, unknown_pc)["disposition"], "YIELD_UNKNOWN")
        extra = copy.deepcopy(base)
        extra["effect_receipts"].append(copy.deepcopy(self.public["cases"][5]["effect_receipts"][1]))
        self.assertEqual(classify(self.public, extra)["disposition"], "YIELD_UNKNOWN")
        misbound = copy.deepcopy(base)
        misbound["effect_receipts"][0]["operation_id"] = "commit_record"
        self.assertEqual(classify(self.public, misbound)["disposition"], "YIELD_UNKNOWN")
        bad_state = copy.deepcopy(base)
        bad_state["effect_receipts"][0]["state"] = "SUCCESS"
        self.assertEqual(classify(self.public, bad_state)["disposition"], "YIELD_UNKNOWN")
        changed_map = copy.deepcopy(self.public)
        changed_map["mapping"]["safepoints"]["pc1"]["semantic_cursor"] = 0
        self.assertEqual(classify(changed_map, base)["disposition"], "YIELD_UNKNOWN")

    def test_auditor_rejects_all_frozen_output_mutations(self) -> None:
        self.assertEqual(len(self.audit["mutation_controls"]), 6)
        self.assertTrue(all(row["rejected"] for row in self.audit["mutation_controls"].values()))


if __name__ == "__main__":
    unittest.main()
