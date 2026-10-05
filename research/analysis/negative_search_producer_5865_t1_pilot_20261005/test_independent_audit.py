import unittest

from oracle_audit import audit_rows


class IndependentAuditTests(unittest.TestCase):
    def test_consistent_scoped_negative_passes(self):
        rows = [{
            "case_id": "stable-empty",
            "candidate": {"status": "NO_MATCH_WITHIN_CERTIFIED_SCOPE",
                          "scope": {"surface_id": "s1", "epoch": 4}},
            "oracle": {"surface_id": "s1", "epoch": 4, "complete": True,
                       "matching_ids": []},
        }]
        audit = audit_rows(rows)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["certified_negative_count"], 1)

    def test_hidden_matching_identity_rejects_false_negative(self):
        rows = [{
            "case_id": "hidden-match",
            "candidate": {"status": "NO_MATCH_WITHIN_CERTIFIED_SCOPE",
                          "scope": {"surface_id": "s1", "epoch": 4}},
            "oracle": {"surface_id": "s1", "epoch": 4, "complete": True,
                       "matching_ids": ["hidden-17"]},
        }]
        audit = audit_rows(rows)
        self.assertEqual(len(audit["errors"]), 1)
        self.assertEqual(audit["errors"][0]["kind"], "false_negative")

    def test_partial_oracle_universe_rejects_negative(self):
        rows = [{
            "case_id": "partial",
            "candidate": {"status": "NO_MATCH_WITHIN_CERTIFIED_SCOPE",
                          "scope": {"surface_id": "s1", "epoch": 4}},
            "oracle": {"surface_id": "s1", "epoch": 4, "complete": False,
                       "matching_ids": []},
        }]
        audit = audit_rows(rows)
        self.assertEqual(audit["errors"][0]["kind"], "unsupported_negative")

    def test_unknown_on_complete_negative_does_not_count_as_coverage(self):
        rows = [{
            "case_id": "abstain",
            "candidate": {"status": "UNKNOWN_INCOMPLETE_COVERAGE"},
            "oracle": {"surface_id": "s1", "epoch": 4, "complete": True,
                       "matching_ids": []},
        }]
        audit = audit_rows(rows)
        self.assertEqual(audit["eligible_negative_count"], 1)
        self.assertEqual(audit["certified_negative_count"], 0)
        self.assertEqual(audit["useful_coverage"], 0.0)


if __name__ == "__main__":
    unittest.main()
