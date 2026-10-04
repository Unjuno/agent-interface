import copy
import hashlib
import json
import unittest

import auditor
import candidate


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_bytes = (candidate.HERE / "fixture.json").read_bytes()
        cls.fixture = json.loads(cls.fixture_bytes)
        cls.raw = candidate.pipeline(cls.fixture)
        cls.candidate_bytes = (candidate.HERE / "candidate.py").read_bytes()

    def test_independent_reconstruction_and_all_decision_rows(self):
        self.assertEqual(auditor.audit(self.raw, self.fixture, self.fixture_bytes,
                                       self.candidate_bytes), [])
        self.assertEqual(len(self.raw["rows"]), 51)

    def test_exception_preserving_scope_and_abstentions(self):
        rows = {(r["representation"], r["query_id"]): r for r in self.raw["rows"]}
        self.assertEqual(rows[("exception_preserving", "protected-heldout")]["decision"], "REJECT")
        self.assertEqual(rows[("exception_preserving", "contradictory")]["decision"], "UNKNOWN")
        self.assertEqual(rows[("exception_preserving", "unrepresented")]["decision"], "UNKNOWN")
        common = [r for r in self.raw["rows"] if r["representation"] == "exception_preserving"
                  and r["query_id"].startswith(("seen-", "heldout-"))]
        self.assertEqual(sum(r["decision"] == "ACCEPT" for r in common), 12)

    def test_unqualified_majority_false_accepts_protected_exception(self):
        rows = {(r["representation"], r["query_id"]): r for r in self.raw["rows"]}
        self.assertEqual(rows[("unqualified_consolidation", "protected-seen")]["decision"], "ACCEPT")

    def test_four_corruptions_are_rejected(self):
        mutations = []
        drop = copy.deepcopy(self.raw)
        drop["representations"]["exception_preserving"]["records"] = [
            r for r in drop["representations"]["exception_preserving"]["records"]
            if r["provenance_kind"] != "OBSERVED_EXCEPTION"]
        mutations.append(drop)
        invert = copy.deepcopy(self.raw)
        for r in invert["representations"]["exception_preserving"]["records"]:
            if r["provenance_kind"] == "OBSERVED_EXCEPTION":
                r["decision"] = "ACCEPT"
        mutations.append(invert)
        context = copy.deepcopy(self.raw)
        for r in context["representations"]["exception_preserving"]["records"]:
            if r["provenance_kind"] == "OBSERVED_EXCEPTION":
                r["conditions"].pop("mode")
        mutations.append(context)
        provenance = copy.deepcopy(self.raw)
        for r in provenance["representations"]["exception_preserving"]["records"]:
            if r["provenance_kind"] == "DERIVED_FROM_OBSERVED":
                r["provenance_kind"] = "OBSERVED_EXCEPTION"
                break
        mutations.append(provenance)
        for corrupted in mutations:
            with self.subTest(corrupted=corrupted):
                self.assertTrue(auditor.audit(corrupted, self.fixture, self.fixture_bytes,
                                              self.candidate_bytes))


if __name__ == "__main__":
    unittest.main()
