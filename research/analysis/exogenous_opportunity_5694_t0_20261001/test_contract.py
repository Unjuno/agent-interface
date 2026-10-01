import unittest


class OpportunityLedgerContractTest(unittest.TestCase):
    def test_busy_period_stays_in_denominator_when_completed_cycle_p95_improves(self):
        try:
            import audit
            import runner
        except ImportError as exc:
            self.fail(f"RED: opportunity-ledger implementation is missing: {exc}")

        raw = runner.build_raw()
        report = audit.audit_raw(raw)
        inversion = report["results"]["inversion"]
        dense = inversion["arms"]["dense"]
        sparse = inversion["arms"]["sparse"]

        self.assertEqual(dense["completed_cycle_p95_ms"], 30)
        self.assertEqual(sparse["completed_cycle_p95_ms"], 5)
        self.assertEqual(dense["opportunity_outcomes"], {"O1": "MET", "O2": "MET", "O3": "MET"})
        self.assertEqual(sparse["opportunity_outcomes"], {"O1": "MET", "O2": "MISS", "O3": "MET"})
        self.assertEqual(dense["useful_effects"], {"met": 3, "total": 3})
        self.assertEqual(sparse["useful_effects"], {"met": 2, "total": 3})
        self.assertNotIn("opportunity_outcomes", raw["scenarios"][0]["arms"]["sparse"])

    def test_no_stall_control_does_not_create_a_coverage_inversion(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("no_stall", report["results"])
        control = report["results"]["no_stall"]["arms"]

        self.assertEqual(control["fast"]["completed_cycle_p95_ms"], 5)
        self.assertEqual(control["dense"]["completed_cycle_p95_ms"], 30)
        self.assertEqual(control["fast"]["useful_effects"], {"met": 3, "total": 3})
        self.assertEqual(control["dense"]["useful_effects"], {"met": 3, "total": 3})

    def test_safe_stop_is_counted_but_not_as_a_useful_effect(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("safe_stop", report["results"])
        arm = report["results"]["safe_stop"]["arms"]["guarded"]

        self.assertEqual(arm["opportunity_outcomes"], {"S1": "SAFE_STOP"})
        self.assertEqual(arm["useful_effects"], {"met": 0, "total": 1})

    def test_completed_observation_of_expiry_is_miss_but_right_censor_is_unknown(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("expiry", report["results"])
        self.assertIn("censored", report["results"])
        expired = report["results"]["expiry"]["arms"]["idle"]
        censored = report["results"]["censored"]["arms"]["idle"]

        self.assertEqual(expired["opportunity_outcomes"], {"E1": "MISS"})
        self.assertEqual(censored["opportunity_outcomes"], {"C1": "UNKNOWN"})

    def test_overlap_uses_effect_regions_not_controller_labels(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("overlap", report["results"])
        arms = report["results"]["overlap"]["arms"]

        self.assertEqual(arms["both"]["opportunity_outcomes"], {"A": "MET", "B": "MET"})
        self.assertEqual(arms["b_only"]["opportunity_outcomes"], {"A": "MISS", "B": "MET"})
        self.assertEqual(arms["both"]["useful_effects"], {"met": 2, "total": 2})

    def test_unsynchronized_clock_keeps_cycle_latency_but_holds_opportunity_outcome(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("unsynced", report["results"])
        arm = report["results"]["unsynced"]["arms"]["local"]

        self.assertEqual(arm["completed_cycle_p95_ms"], 5)
        self.assertEqual(arm["opportunity_outcomes"], {"U1": "UNKNOWN"})

    def test_outcome_preserving_expiry_mutation_is_rejected_by_frozen_fixture_identity(self):
        import audit
        import runner

        raw = runner.build_raw()
        raw["scenarios"][0]["opportunities"][1]["expiry_ms"] = 179

        report = audit.audit_raw(raw)
        self.assertIn("fixture_identity", report["errors"])

    def test_no_exogenous_opportunities_are_not_manufactured(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        self.assertIn("no_exogenous", report["results"])
        arm = report["results"]["no_exogenous"]["arms"]["idle"]

        self.assertEqual(arm["opportunity_applicability"], "NOT_APPLICABLE")
        self.assertEqual(arm["useful_effects"], {"met": 0, "total": 0})

    def test_malformed_effect_timestamp_is_rejected_without_auditor_exception(self):
        import audit
        import runner

        raw = runner.build_raw()
        raw["scenarios"][0]["arms"]["dense"]["effects"][0]["time_ms"] = "soon"

        try:
            report = audit.audit_raw(raw)
        except Exception as exc:
            self.fail(f"auditor raised instead of returning a rejection: {type(exc).__name__}: {exc}")
        self.assertTrue(any(error.endswith(":invalid_event_time") for error in report["errors"]))

    def test_first_useful_effect_latency_and_longest_uncovered_opportunity_gap(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        inversion = report["results"]["inversion"]["arms"]
        self.assertIn("first_useful_effect_latency_ms", inversion["dense"])

        self.assertEqual(inversion["dense"]["first_useful_effect_latency_ms"], {"O1": 35, "O2": 35, "O3": 35})
        self.assertEqual(inversion["sparse"]["first_useful_effect_latency_ms"], {"O1": 10, "O2": None, "O3": 20})
        self.assertEqual(inversion["dense"]["longest_uncovered_opportunity_gap_ms"], 35)
        self.assertEqual(inversion["sparse"]["longest_uncovered_opportunity_gap_ms"], 80)

    def test_sparse_arm_retains_the_opportunity_fully_expired_during_its_busy_interval(self):
        import audit
        import runner

        report = audit.audit_raw(runner.build_raw())
        inversion = report["results"]["inversion"]["arms"]
        self.assertIn("busy_expired_opportunity_ids", inversion["sparse"])

        self.assertEqual(inversion["sparse"]["busy_expired_opportunity_ids"], ["O2"])
        self.assertEqual(inversion["dense"]["busy_expired_opportunity_ids"], [])

    def test_non_object_raw_root_is_rejected_without_auditor_exception(self):
        import audit

        try:
            report = audit.audit_raw([])
        except Exception as exc:
            self.fail(f"auditor raised instead of returning a rejection: {type(exc).__name__}: {exc}")
        self.assertIn("root_not_object", report["errors"])


if __name__ == "__main__":
    unittest.main()
