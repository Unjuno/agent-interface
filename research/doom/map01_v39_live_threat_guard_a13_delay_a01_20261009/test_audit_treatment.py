import unittest
from audit_treatment import event_timing


class TreatmentTimingTests(unittest.TestCase):
    def test_event_after_response_consumption_is_not_counted_as_overlap(self):
        decisions = [{"iteration": 9, "controller_model_started_ns": 100,
                      "controller_model_ended_ns": 200}]
        events = [{"kind": "KILL_COUNT_INCREASE", "useful": True,
                   "controller_visible": False, "observed_ns": 200_000_000}]
        timing = event_timing(decisions, events)
        self.assertFalse(timing["useful_events"][0]["inside_tenth_turn_interval"])
        self.assertEqual(timing["useful_events"][0]["milliseconds_after_interval_end"],
                         199.9998)

    def test_event_during_response_wait_is_counted_inside_interval(self):
        decisions = [{"iteration": 9, "controller_model_started_ns": 100,
                      "controller_model_ended_ns": 300}]
        events = [{"kind": "KILL_COUNT_INCREASE", "useful": True,
                   "controller_visible": False, "observed_ns": 250}]
        timing = event_timing(decisions, events)
        self.assertTrue(timing["useful_events"][0]["inside_tenth_turn_interval"])
        self.assertEqual(timing["useful_events"][0]["milliseconds_after_interval_end"], -0.00005)


if __name__ == "__main__":
    unittest.main()
