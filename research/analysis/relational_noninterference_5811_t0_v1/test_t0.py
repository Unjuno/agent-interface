"""Construction tests; formal candidate and auditor run only in frozen Docker allocations."""
import copy
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent
spec_c = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(candidate)
spec_a = importlib.util.spec_from_file_location("audit", ROOT / "audit.py")
auditor = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(auditor)
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class RelationalT0Tests(unittest.TestCase):
    def test_frozen_denominator_and_expected_outcomes(self):
        result = candidate.run(FIXTURE)
        report = auditor.audit(FIXTURE, result)
        self.assertEqual(report["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(len(result["cases"]), 10)

    def test_attacks_look_pass_in_isolation_and_final_state(self):
        for row in candidate.run(FIXTURE)["cases"]:
            if row["id"] in {"delayed_receipt_to_A", "B_cleanup_releases_A_input"}:
                self.assertTrue(row["single_run_pass"])
                self.assertTrue(row["final_state_equal"])
                self.assertEqual(row["outcome"], "CONFIRMED_CROSS_SESSION_EFFECT")

    def test_hidden_shared_global_is_not_independent_despite_label(self):
        row = next(x for x in candidate.run(FIXTURE)["cases"] if x["id"] == "hidden_global_focus")
        self.assertEqual(row["dependency_class"], "UNKNOWN_COVERAGE")

    def test_mutation_session_relabel_rejected(self):
        f = copy.deepcopy(FIXTURE)
        f["cases"][0]["resources"][0]["session"] = "B"
        self.assertNotEqual(candidate.run(f), candidate.run(FIXTURE))

    def test_mutation_source_generation_substitution_rejected(self):
        f = copy.deepcopy(FIXTURE)
        f["cases"][0]["paired"]["trace"][0]["generation"] = 8
        with self.assertRaises(AssertionError):
            auditor.audit(f, candidate.run(FIXTURE))

    def test_mutation_effect_row_omission_rejected(self):
        f = copy.deepcopy(FIXTURE)
        c = next(x for x in f["cases"] if x["id"] == "clean_disjoint")
        c["paired"]["trace"] = [x for x in c["paired"]["trace"] if x["kind"] != "EFFECT"]
        with self.assertRaises(AssertionError):
            auditor.audit(f, candidate.run(FIXTURE))

    def test_mutation_hidden_resource_omission_becomes_unknown(self):
        f = copy.deepcopy(FIXTURE)
        c = next(x for x in f["cases"] if x["id"] == "hidden_global_focus")
        c["resources"] = [x for x in c["resources"] if x["resource"] != "global:focus"]
        row = next(x for x in candidate.run(f)["cases"] if x["id"] == c["id"])
        self.assertEqual(row["dependency_class"], "UNKNOWN_COVERAGE")

    def test_mutation_trace_truncation_becomes_unknown(self):
        f = copy.deepcopy(FIXTURE)
        c = next(x for x in f["cases"] if x["id"] == "truncated_dependency_trace")
        c["coverage"]["B"]["expected"] += 1
        row = next(x for x in candidate.run(f)["cases"] if x["id"] == c["id"])
        self.assertEqual(row["dependency_class"], "UNKNOWN_COVERAGE")


if __name__ == "__main__":
    unittest.main()
