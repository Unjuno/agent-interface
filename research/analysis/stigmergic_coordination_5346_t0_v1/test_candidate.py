import unittest

from candidate import POLICIES, SCENARIOS, run_case


class StigmergicT0Tests(unittest.TestCase):
    def cell(self, scenario_name, policy):
        scenario = next(s for s in SCENARIOS if s.name == scenario_name)
        return run_case(scenario, policy)

    def test_matrix_is_complete_and_unique(self):
        self.assertEqual(len(SCENARIOS), 9)
        self.assertEqual(len({s.name for s in SCENARIOS}), 9)
        self.assertEqual(len(POLICIES), 3)

    def test_visible_local_trace_avoids_collision(self):
        baseline = self.cell("visible_contention", "NO_COORDINATION")
        local = self.cell("visible_contention", "LOCAL_MARKERS")
        self.assertEqual(baseline["collision_retries"], 1)
        self.assertEqual(local["collision_retries"], 0)
        self.assertEqual(local["completion_count"], 2)

    def test_delayed_or_lost_trace_never_replaces_lease(self):
        for name in ("delayed_observation", "marker_loss"):
            cell = self.cell(name, "LOCAL_MARKERS")
            self.assertEqual(cell["collision_retries"], 1)
            self.assertTrue(cell["all_effects_have_authoritative_gate"])

    def test_forged_and_stale_markers_are_ignored(self):
        for name in ("forged_marker", "stale_generation"):
            cell = self.cell(name, "LOCAL_MARKERS")
            self.assertEqual(cell["collision_retries"], 1)
            self.assertEqual(cell["unsafe_admissions"], 0)

    def test_duplicate_delivery_is_deduplicated(self):
        cell = self.cell("duplicate_delivery", "LOCAL_MARKERS")
        self.assertEqual(cell["collision_retries"], 0)
        self.assertEqual(cell["coordination_events"], 2)
        self.assertTrue(any(e["kind"] == "MARKER_DUPLICATE_IGNORED" for e in cell["events"]))

    def test_crash_recovers_after_lease_expiry_without_marker_authority(self):
        for policy in POLICIES:
            cell = self.cell("owner_crash", policy)
            self.assertEqual(cell["completion_count"], 2)
            self.assertGreaterEqual(cell["recovery_latency_ticks"], 0)
            self.assertTrue(cell["all_effects_have_authoritative_gate"])

    def test_external_mutation_requires_fresh_generation(self):
        for policy in POLICIES:
            cell = self.cell("external_mutation", policy)
            kinds = [e["kind"] for e in cell["events"]]
            self.assertIn("STALE_GENERATION_REFUSED", kinds)
            self.assertIn("FRESH_REOBSERVATION", kinds)
            self.assertEqual(cell["completion_count"], 2)

    def test_no_contention_does_not_gain_from_markers(self):
        for policy in POLICIES:
            cell = self.cell("no_contention", policy)
            self.assertEqual(cell["collision_retries"], 0)
            self.assertEqual(cell["completion_count"], 2)

    def test_every_admission_uses_authoritative_lease(self):
        for scenario in SCENARIOS:
            for policy in POLICIES:
                cell = run_case(scenario, policy)
                for event in cell["events"]:
                    if event["kind"] == "LEASE_GRANTED":
                        self.assertEqual(event["basis"], "authoritative_lease")


if __name__ == "__main__":
    unittest.main()
