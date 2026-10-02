"""Cheap construction and mutation checks, run before formal freeze."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

P = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate6021", P / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
PUBLIC = json.loads((P / "public.json").read_text())
TRUTH = json.loads((P / "truth.json").read_text())["expected"]


class Construction(unittest.TestCase):
    def test_finite_domain_cardinality(self):
        self.assertEqual(len(candidate.tuples(PUBLIC["domains"])), 256)

    def test_case_expectations(self):
        got = candidate.run(PUBLIC)["results"]
        for key, expected in TRUTH.items():
            for field, value in expected.items():
                self.assertEqual(got[key][field], value, (key, field))

    def test_scope_broadening_mutation_changes_findings(self):
        mutated = copy.deepcopy(PUBLIC)
        c = next(x for x in mutated["cases"] if x["id"] == "valid-disjoint-exceptions")
        c["exact_exceptions"][0]["scope"]["task"] = "T1"
        got = candidate.run(mutated)["results"]["valid-disjoint-exceptions"]
        self.assertEqual(got["cumulative_expansions"], 0)

    def test_expiry_boundary_is_exclusive(self):
        mutated = copy.deepcopy(PUBLIC)
        c = next(x for x in mutated["cases"] if x["id"] == "valid-disjoint-exceptions")
        c["exact_exceptions"][0]["expires_at"] = c["current_version"]
        got = candidate.run(mutated)["results"]["valid-disjoint-exceptions"]
        self.assertEqual(got["cumulative_expansions"], 0)

    def test_unauthenticated_issuer_has_no_authority(self):
        mutated = copy.deepcopy(PUBLIC)
        c = next(x for x in mutated["cases"] if x["id"] == "valid-disjoint-exceptions")
        c["exact_exceptions"][0]["issuer_authenticated"] = False
        got = candidate.run(mutated)["results"]["valid-disjoint-exceptions"]
        self.assertEqual(got["cumulative_expansions"], 0)

    def test_export_hard_invariant_survives_attempt(self):
        got = candidate.run(PUBLIC)["results"]["hard-invariant-waiver-attempt"]
        self.assertEqual(got["export_admissions"], 0)

    def test_evidence_negative_result_cannot_be_erased(self):
        mutated = copy.deepcopy(PUBLIC)
        c = next(x for x in mutated["cases"] if x["id"] == "post-outcome-evidence-relaxation")
        c["versions"][2]["outcome"] = "PASS"
        self.assertTrue(candidate.run(mutated)["results"][c["id"]]["relaxation_after_result"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
