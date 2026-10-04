"""Mutation tests for the retained video-to-event time join."""
import copy
import unittest

from research.doom import audit_map01_astra_health_events_v1 as audit


class TransitionJoinAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.timeline, cls.report, cls.events, cls.hashes = audit.load_inputs()

    def test_saved_join_passes(self):
        audit.audit(self.result, self.timeline, self.report, self.events, self.hashes)

    def assert_mutation_rejected(self, change):
        result = copy.deepcopy(self.result)
        change(result)
        with self.assertRaises(AssertionError):
            audit.audit(result, self.timeline, self.report, self.events, self.hashes)

    def test_wrong_transition_delta_rejected(self):
        self.assert_mutation_rejected(lambda r: r["annotations"][0].__setitem__("health_delta_percent_points", -3))

    def test_wrong_input_key_rejected(self):
        self.assert_mutation_rejected(lambda r: r["annotations"][2]["input_admissions_inside_video_interval"][0].__setitem__("key", "space"))

    def test_wrong_input_time_rejected(self):
        self.assert_mutation_rejected(lambda r: r["annotations"][2]["input_admissions_inside_video_interval"][0].__setitem__("at_s", 0.0))

    def test_wrong_step_identity_rejected(self):
        self.assert_mutation_rejected(lambda r: r["annotations"][2]["key_ack_to_step_complete_overlaps"][0].__setitem__("step", 99))

    def test_wrong_overlap_endpoint_rejected(self):
        self.assert_mutation_rejected(lambda r: r["annotations"][2]["key_ack_to_step_complete_overlaps"][0].__setitem__("overlap_stop_s", 0.0))


if __name__ == "__main__":
    unittest.main()
