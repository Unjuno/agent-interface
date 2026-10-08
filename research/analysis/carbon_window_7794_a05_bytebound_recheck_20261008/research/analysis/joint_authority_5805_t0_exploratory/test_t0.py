import unittest

from candidate import evaluate_trace
from fixtures import TRACES, MODES


class JointAuthorityContractTests(unittest.TestCase):
    def test_disjoint_private_effect_needs_no_unrelated_owner_grant(self):
        rows = {row["mode"]: row for row in evaluate_trace(TRACES["private_a_write"], MODES)}
        self.assertTrue(rows["all_owner_conjunction"]["admitted"])
        self.assertTrue(rows["scoped_delegation"]["admitted"])

    def test_coowned_effect_with_only_requester_grant_exposes_baseline_gap(self):
        rows = {row["mode"]: row for row in evaluate_trace(TRACES["shared_a_only"], MODES)}
        self.assertTrue(rows["requester_only"]["admitted"])
        self.assertFalse(rows["all_owner_conjunction"]["admitted"])
        self.assertFalse(rows["scoped_delegation"]["admitted"])

    def test_exact_scoped_delegation_preserves_progress_without_broadening_scope(self):
        allowed = {row["mode"]: row for row in evaluate_trace(TRACES["shared_delegated_write"], MODES)}
        wrong = {row["mode"]: row for row in evaluate_trace(TRACES["delegation_wrong_recipient"], MODES)}
        self.assertTrue(allowed["scoped_delegation"]["admitted"])
        self.assertFalse(wrong["scoped_delegation"]["admitted"])

    def test_revoked_forged_conflicting_and_unknown_authority_fail_closed(self):
        for trace_id in ("shared_revoked", "shared_forged", "shared_conflict", "unknown_owners", "delegation_revoked"):
            with self.subTest(trace_id=trace_id):
                rows = {row["mode"]: row for row in evaluate_trace(TRACES[trace_id], MODES)}
                self.assertFalse(rows["all_owner_conjunction"]["admitted"])
                self.assertFalse(rows["scoped_delegation"]["admitted"])
                self.assertFalse(rows["all_owner_conjunction"]["effect_applied"])
                self.assertFalse(rows["scoped_delegation"]["effect_applied"])

    def test_disclosure_grants_bind_recipient_and_layout_has_independent_scope(self):
        disclose = {row["mode"]: row for row in evaluate_trace(TRACES["disclose_wrong_recipient"], MODES)}
        layout = {row["mode"]: row for row in evaluate_trace(TRACES["shared_layout_both"], MODES)}
        self.assertFalse(disclose["all_owner_conjunction"]["admitted"])
        self.assertTrue(layout["all_owner_conjunction"]["admitted"])

    def test_safety_release_and_cancel_remain_admissible_without_content_grants(self):
        for trace_id in ("emergency_release", "cancel"):
            rows = {row["mode"]: row for row in evaluate_trace(TRACES[trace_id], MODES)}
            for mode in MODES:
                self.assertTrue(rows[mode]["admitted"], (trace_id, mode))
                self.assertFalse(rows[mode]["effect_applied"])

    def test_effect_oracle_never_upgrades_permission_to_success(self):
        rows = evaluate_trace(TRACES["shared_both_grant"], MODES)
        by_mode = {row["mode"]: row for row in rows}
        for mode in ("requester_only", "all_owner_conjunction", "scoped_delegation"):
            self.assertTrue(by_mode[mode]["admitted"])
            self.assertTrue(by_mode[mode]["attempted"])
        self.assertFalse(by_mode["deny_all"]["admitted"])
        self.assertFalse(any(row["effect_verified"] for row in rows))


if __name__ == "__main__":
    unittest.main()
