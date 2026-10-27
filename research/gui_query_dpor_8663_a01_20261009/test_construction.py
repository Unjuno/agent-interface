import json
import unittest
from pathlib import Path

import candidate
import audit


ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "MODEL.json").read_text())
CASES = {case["id"]: case for case in MODEL["cases"]}


class CandidateConstructionTests(unittest.TestCase):
    def test_predicate_dpor_preserves_exhaustive_outcomes(self):
        for case in MODEL["cases"]:
            full = candidate.exhaustive(case)
            reduced, _ = candidate.sleep_set(case, "predicate")
            self.assertEqual({candidate.canonical(x["outcome"]) for x in full},
                             {candidate.canonical(x["outcome"]) for x in reduced}, case["id"])

    def test_commuting_control_reduction_exceeds_threshold(self):
        case = CASES["commuting_control"]
        full = candidate.exhaustive(case)
        reduced, _ = candidate.sleep_set(case, "predicate")
        self.assertLessEqual(len(reduced), len(full) * 0.8)

    def test_node_only_omits_matching_insert_witness(self):
        case = CASES["matching_insert"]
        full = candidate.exhaustive(case)
        reduced, _ = candidate.sleep_set(case, "node_only")
        sig = lambda r: candidate.canonical(r["outcome"]["admission"]["node_only"])
        self.assertNotEqual({sig(x) for x in full}, {sig(x) for x in reduced})

    def test_predicate_dependency_retains_insertion_and_unknown_orders(self):
        for cid, event_id in (("matching_insert", "a-insert"),
                              ("unknown_transition", "a-unknown")):
            case = CASES[cid]
            rows, _ = candidate.sleep_set(case, "predicate")
            schedules = {tuple(row["schedule"]) for row in rows}
            self.assertTrue(any(s.index("query") < s.index(event_id) for s in schedules), cid)
            self.assertTrue(any(s.index(event_id) < s.index("query") for s in schedules), cid)

    def test_interacting_selector_field_writes_are_not_commuted(self):
        case = CASES["combined_property_updates"]
        rows, _ = candidate.sleep_set(case, "predicate")
        schedules = {tuple(row["schedule"]) for row in rows}
        both_before_query = [s for s in schedules
                             if s.index("a-rename-b") < s.index("query")
                             and s.index("b-disable-b") < s.index("query")]
        self.assertTrue(any(s.index("a-rename-b") < s.index("b-disable-b") for s in both_before_query))
        self.assertTrue(any(s.index("b-disable-b") < s.index("a-rename-b") for s in both_before_query))

    def test_aba_generation_change_is_visible_to_certificate(self):
        case = CASES["aba_membership"]
        rows = candidate.exhaustive(case)
        relevant = [r for r in rows
                    if r["schedule"].index("query") < r["schedule"].index("a-aba")
                    < r["schedule"].index("admit")]
        self.assertTrue(relevant)
        for row in relevant:
            admission = row["outcome"]["admission"]
            self.assertTrue(admission["node_only"]["unsafe"])
            self.assertFalse(admission["predicate_cert"]["accepted"])

    def test_mutation_controls_lose_their_planted_histories(self):
        checks = (("modal_scope_change", "mutant_cross_scope"),
                  ("unknown_transition", "mutant_unknown_independent"),
                  ("matching_insert", "mutant_missing_predicate"))
        for cid, key in checks:
            case = CASES[cid]
            exhaustive = candidate.exhaustive(case)
            mode = {"mutant_cross_scope": "mutant_cross_scope",
                    "mutant_unknown_independent": "mutant_unknown_independent",
                    "mutant_missing_predicate": "node_only"}[key]
            reduced, _ = candidate.sleep_set(case, mode)
            full = {candidate.canonical(r["outcome"]) for r in exhaustive}
            kept = {candidate.canonical(r["outcome"]) for r in reduced}
            self.assertTrue(full - kept, cid)

    def test_model_bounds_and_unknown_is_dependent(self):
        for case in MODEL["cases"]:
            self.assertLessEqual(len(case["initial"]["nodes"]), 3, case["id"])
            transitions = [e for e in case["events"]
                           if e["kind"] not in {"query", "validate", "admit"}]
            self.assertLessEqual(len(transitions), 4, case["id"])
        case = CASES["unknown_transition"]
        state = candidate.initial_state(case)
        self.assertFalse(candidate.independent(state, "a-unknown", "query", "predicate", case))

    def test_auditor_is_separate_and_matches_only_the_frozen_semantics(self):
        source = (ROOT / "audit.py").read_text()
        self.assertNotIn("import candidate", source)
        self.assertNotIn("from candidate", source)
        for case in MODEL["cases"]:
            c_full = candidate.exhaustive(case)
            a_full = audit.all_orders(case)
            self.assertEqual({tuple(x["schedule"]) for x in c_full},
                             {tuple(x["schedule"]) for x in a_full}, case["id"])
            self.assertEqual({candidate.canonical(x["outcome"]) for x in c_full},
                             {audit.packed(x["outcome"]) for x in a_full}, case["id"])
            for c_mode, a_mode in (("predicate", "predicate"),
                                   ("node_only", "node_only"),
                                   ("mutant_cross_scope", "mutant_cross_scope"),
                                   ("mutant_unknown_independent", "mutant_unknown_independent")):
                c_rows, _ = candidate.sleep_set(case, c_mode)
                a_rows, _ = audit.reduced_orders(case, a_mode)
                self.assertEqual({tuple(x["schedule"]) for x in c_rows},
                                 {tuple(x["schedule"]) for x in a_rows},
                                 f"{case['id']} {c_mode}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
