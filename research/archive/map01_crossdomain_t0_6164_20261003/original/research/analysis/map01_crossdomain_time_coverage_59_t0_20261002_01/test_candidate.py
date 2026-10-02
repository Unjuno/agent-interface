import unittest

from candidate import classify_domain


class CrossDomainCoverageTests(unittest.TestCase):
    def test_terminal_neutral_receipt_does_not_stand_in_for_per_press_up(self):
        events = [
            {"event": "input_admission", "id": "p1", "admitted_ns": 10,
             "input_ack_ns": 11, "key": "space"},
            {"event": "input_released", "id": "p1", "owner_release": {
                "event": "owner_release", "verified": True,
                "keys_down": [], "verified_ns": 30}},
        ]
        result = classify_domain("doom", events, [], [])
        self.assertFalse(result["per_actuation_occupancy_identified"])

    def test_observer_state_index_without_host_time_is_not_effect_latency(self):
        events = [{"event": "input_admission", "id": "a", "admitted_ns": 5,
                   "input_ack_ns": 6, "key": "button"}]
        observer = [{"record_index": 91, "state": "A_TO_B", "scoreable": True}]
        result = classify_domain("openttd", events, observer, [])
        self.assertTrue(result["independent_effect_observed"])
        self.assertFalse(result["effect_clock_join_identified"])

    def test_complete_identity_bound_edges_and_effect_enable_time_coverage(self):
        events = [
            {"event": "input_admission", "id": "a", "actuation_id": "a", "admitted_ns": 10,
             "clock_domain_id": "host-monotonic",
             "input_ack_ns": 11, "key": "button"},
            {"event": "physical_down", "actuation_id": "a", "host_ns": 12,
             "clock_domain_id": "host-monotonic"},
            {"event": "physical_up", "actuation_id": "a", "host_ns": 20,
             "clock_domain_id": "host-monotonic"},
            {"event": "independent_effect", "actuation_id": "a", "host_ns": 18,
             "clock_domain_id": "host-monotonic", "verified": True},
        ]
        result = classify_domain("fixture", events, [], ["a"])
        self.assertTrue(result["per_actuation_occupancy_identified"])
        self.assertTrue(result["effect_clock_join_identified"])
        self.assertEqual(8, result["identified_occupancy_ns"])

    def test_missing_matching_up_edge_keeps_coverage_unknown(self):
        events = [
            {"event": "input_admission", "id": "a", "actuation_id": "a", "admitted_ns": 10,
             "input_ack_ns": 11, "key": "button"},
            {"event": "physical_down", "actuation_id": "a", "host_ns": 12},
            {"event": "independent_effect", "actuation_id": "a", "host_ns": 18,
             "verified": True},
        ]
        result = classify_domain("fixture", events, [], ["a"])
        self.assertFalse(result["per_actuation_occupancy_identified"])
        self.assertIsNone(result["identified_occupancy_ns"])

    def test_different_clock_domains_do_not_form_an_interval(self):
        events = [
            {"event": "input_admission", "actuation_id": "a",
             "admitted_ns": 10, "input_ack_ns": 11,
             "clock_domain_id": "owner-clock"},
            {"event": "physical_down", "actuation_id": "a", "host_ns": 12,
             "clock_domain_id": "server-clock"},
            {"event": "physical_up", "actuation_id": "a", "host_ns": 20,
             "clock_domain_id": "server-clock"},
            {"event": "independent_effect", "actuation_id": "a", "host_ns": 18,
             "clock_domain_id": "observer-clock", "verified": True},
        ]
        result = classify_domain("fixture", events, [], ["a"])
        self.assertFalse(result["per_actuation_occupancy_identified"])
        self.assertFalse(result["effect_clock_join_identified"])


if __name__ == "__main__":
    unittest.main()
