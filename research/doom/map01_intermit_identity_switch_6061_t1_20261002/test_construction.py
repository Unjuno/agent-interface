import unittest
import audit
import candidate
import make_fixture


class IdentitySwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible, cls.truth = make_fixture.build()
        cls.raw = [candidate.run_case(c, p) for c in cls.visible["cases"] for p in candidate.POLICIES]

    def row(self, case_id, policy):
        return next(r for r in self.raw if (r["case_id"], r["policy"]) == (case_id, policy))

    def test_silent_switch_is_observationally_equal_to_control(self):
        by = {c["case_id"]: c for c in self.visible["cases"]}
        self.assertEqual(by["same_identity_control"]["observations"], by["silent_identity_switch"]["observations"])

    def test_epoch_gate_releases_at_tick_five_for_observable_or_unknown_changes(self):
        for cid in ("visible_identity_switch", "epoch_only_switch", "unknown_epoch_switch"):
            row = self.row(cid, "identity_epoch_gate")
            self.assertEqual(row["release_tick"], 5)
            self.assertEqual(row["commanded_occupancy_ticks"], 5)

    def test_identity_only_gate_misses_stale_label_epoch_change(self):
        self.assertIsNone(self.row("epoch_only_switch", "identity_only_gate")["release_tick"])

    def test_kinematic_only_misses_all_observable_switches(self):
        for cid in ("visible_identity_switch", "epoch_only_switch", "unknown_epoch_switch"):
            self.assertIsNone(self.row(cid, "kinematic_only")["release_tick"])

    def test_silent_switch_is_held_as_unknown_not_credited(self):
        result = audit.audit_data(self.visible, self.truth, self.raw)
        self.assertEqual(result["decision"], "HOLD_SILENT_IDENTITY_SWITCH_UNOBSERVABLE")
        self.assertEqual(result["silent_switch_disposition"], "UNKNOWN_NOT_CREDITED")

    def test_oracle_is_not_in_planner_visible_input(self):
        self.assertFalse(any("target_identity" in o for c in self.visible["cases"] for o in c["observations"]))

    def test_independent_audit_and_five_corruption_controls(self):
        result = audit.audit_data(self.visible, self.truth, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_HOLD")
        checks = audit.mutations(self.visible, self.truth, self.raw)
        self.assertEqual(len(checks), 5)
        self.assertTrue(all(x["rejected"] for x in checks))

    def test_row_loss_rejected(self):
        self.assertTrue(audit.audit_data(self.visible, self.truth, self.raw[:-1])["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
