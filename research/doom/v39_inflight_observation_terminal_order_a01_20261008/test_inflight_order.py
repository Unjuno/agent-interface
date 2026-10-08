import unittest
from run_candidate import run_scenario

class InFlightObservationTests(unittest.TestCase):
    def test_observation_read_before_enqueue_is_seen_before_terminal(self):
        result=run_scenario()
        self.assertEqual(result['status'],'PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL')
        self.assertFalse(result['snapshot_saw_event'])
        self.assertTrue(result['monitor_saw_event_after_snapshot'])
        self.assertTrue(result['answer_discarded'])
        self.assertEqual(result['latest_sequence'],42)
        self.assertEqual(result['terminal_release'],{'verified':True,'keys_down':[],'buttons_down':[]})

if __name__=='__main__': unittest.main()
