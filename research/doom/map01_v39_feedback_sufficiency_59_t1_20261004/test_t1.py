import unittest
from run_t1 import analyze, load_inputs

class RetainedTraceSufficiencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report,cls.events,cls.owners,cls.occupancy=load_inputs()
    def test_actual_trace_holds_for_independent_feedback(self):
        r=analyze(self.report,self.events,self.owners,self.occupancy)
        self.assertEqual(r['disposition'],'HOLD_NO_INDEPENDENT_FEEDBACK_STREAM')
        self.assertEqual(r['qualifying_data']['independent_scorer_samples'],0)
        self.assertEqual(r['qualifying_data']['independent_scorer_events'],0)
    def test_pixels_and_controller_visible_health_do_not_become_scorer_events(self):
        r=analyze(self.report,self.events,self.owners,self.occupancy)
        self.assertEqual(r['observed_gaps']['pixel_only_receipts_excluded'],4)
        self.assertEqual(r['observed_gaps']['controller_visible_typed_observations_excluded'],218)
    def test_coarse_or_partial_admission_does_not_become_per_key_release_interval(self):
        r=analyze(self.report,self.events,self.owners,self.occupancy)
        self.assertEqual(r['per_key_disposition'],'HOLD_NO_COMPLETE_EXPLICIT_PER_KEY_RELEASE_INTERVALS')
        self.assertEqual(r['qualifying_data']['complete_explicit_per_key_intervals'],0)
        self.assertEqual(r['input_counts']['occupancy_hold_rows'],29)
    def test_post_control_outcome_is_not_recast_as_timed_positive_event(self):
        r=analyze(self.report,self.events,self.owners,self.occupancy)
        self.assertEqual(r['input_counts']['post_control_score_rows'],1)
        self.assertEqual(r['observed_gaps']['terminal_score_has_timestamped_progress_sample'],0)
        self.assertEqual(r['terminal_score'][0]['kill_count'],1)
        self.assertFalse(r['terminal_score'][0]['map_exit'])

if __name__=='__main__': unittest.main(verbosity=2)
