"""Construction-only regression checks for Issue #7678 A03."""
import json
import unittest
from pathlib import Path

import auditor
import candidate

HERE = Path(__file__).resolve().parent


class CacheContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text())
        cls.certificate = candidate.load_frozen(
            cls.fixture["candidate_path"], cls.fixture["candidate_sha256"],
            cls.fixture["source_commit"])
        cls.report = candidate.encode(cls.fixture["truth_orders"][0])
        cls.base = candidate.make_case(cls.fixture, (0, 1), reporter=0, report=cls.report)
        cls.revoked = candidate.make_case(
            cls.fixture, (0, 1), reporter=0, report=cls.report,
            grants={"principal_0": sorted(cls.fixture["routes"]),
                    "principal_1": ["a", "b", "c"]})
        cls.protected = candidate.make_case(
            cls.fixture, (0, 1), reporter=0, report=cls.report,
            protected={"c": ["principal_0:protected-record"]})
        cls.no_right = candidate.make_case(cls.fixture, (0, 1), decision_maker=None)

    def test_frozen_canonical_source_hashes(self):
        self.assertEqual(candidate.hashlib.sha256((HERE / self.fixture["candidate_path"]).read_bytes()).hexdigest(),
                         self.fixture["candidate_sha256"])
        self.assertEqual(candidate.hashlib.sha256((HERE / self.fixture["auditor_path"]).read_bytes()).hexdigest(),
                         self.fixture["auditor_sha256"])

    def test_context_changes_are_part_of_cache_identity(self):
        self.assertEqual(candidate.case_cache_key(self.base), candidate.case_cache_key(self.base))
        self.assertNotEqual(candidate.case_cache_key(self.base), candidate.case_cache_key(self.revoked))
        self.assertNotEqual(candidate.case_cache_key(self.base), candidate.case_cache_key(self.protected))
        self.assertNotEqual(candidate.case_cache_key(self.base), candidate.case_cache_key(self.no_right))
        # The defective A02 key ignored exactly these context fields.
        old_key = lambda case: candidate.pref_key(case["preferences"])
        self.assertEqual(old_key(self.base), old_key(self.revoked))
        self.assertEqual(old_key(self.base), old_key(self.protected))
        self.assertEqual(old_key(self.base), old_key(self.no_right))

    def test_canonical_evaluator_applies_changed_grants_and_constraints(self):
        base = candidate.evaluate_case(self.certificate, self.fixture, self.base, {})
        revoked = candidate.evaluate_case(self.certificate, self.fixture, self.revoked, {})
        protected = candidate.evaluate_case(self.certificate, self.fixture, self.protected, {})
        no_right = candidate.evaluate_case(self.certificate, self.fixture, self.no_right, {})
        self.assertIn("d", base["eligible"])
        self.assertNotIn("d", revoked["eligible"])
        self.assertNotIn("c", protected["eligible"])
        self.assertIsNone(no_right["delegated_choice"])

    def test_candidate_and_rank_vector_auditor_agree_on_report_domain(self):
        _, reports = candidate.report_domain(self.certificate, self.fixture)
        self.assertEqual(reports, auditor.independent_report_domain(self.fixture))
        self.assertEqual(len(reports), 92)
        self.assertEqual(6 * 6 * 2 * len(reports), 6624)


if __name__ == "__main__":
    unittest.main()
