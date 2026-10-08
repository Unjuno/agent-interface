import copy
import json
import unittest
from pathlib import Path

from experiment import candidate, static_trace_baseline

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"]


class FrozenCases(unittest.TestCase):
    def test_oracle_cases(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                result = candidate(case)
                if case["expected"] in ("PASS", "PASS_UNKNOWN"):
                    self.assertEqual("PASS", result["outcome"])
                else:
                    self.assertEqual("FAIL", result["outcome"])

    def test_omitted_forbidden_is_rejected(self):
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "omitted_prohibition"))
        self.assertIn("SOURCE_CLAUSE_OMITTED", candidate(case)["errors"])

    def test_forged_supersession_and_span_are_rejected(self):
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "authenticated_supersession"))
        case["source"][1]["turn"] = 1
        self.assertIn("INVALID_SUPERSESSION", candidate(case)["errors"])
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "source_span_mismatch"))
        self.assertIn("SOURCE_SPAN_MISMATCH", candidate(case)["errors"])

    def test_ambiguity_cannot_be_forced_and_addition_needs_support(self):
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "genuine_ambiguity"))
        case["derived"][0]["status"] = "preserved"
        self.assertIn("AMBIGUITY_FORCED", candidate(case)["errors"])
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "invented_permission"))
        self.assertIn("UNSUPPORTED_DERIVATION", candidate(case)["errors"])

    def test_static_baseline_does_not_resolve_turn_precedence(self):
        case = next(c for c in CASES if c["id"] == "authenticated_supersession")
        result = static_trace_baseline(case)
        self.assertEqual(["s1"], result["missing_source_ids"])


if __name__ == "__main__":
    unittest.main()
