import unittest
from profile import decompose, classify

class Profile(unittest.TestCase):
    def test_decomposition_preserves_signed_clear_compensation(self):
        event = {'onset_ns':0,'due_clear_ns':20_000_000,'draw_start_ns':5_900_000,
                 'draw_end_ns':6_000_000,'clear_start_ns':20_100_000,'clear_end_ns':20_200_000}
        trace = {'wait':{'return_ns':5_700_000},'paint_start_ns':5_900_000,'paint_end_ns':6_000_000}
        self.assertEqual(decompose(event,trace), {'exposure_ns':14_100_000,'shortfall_ns':5_900_000,
                         'draw_wait_lateness_ns':5_700_000,'post_wait_to_paint_ns':200_000,
                         'draw_xsync_ns':100_000,'clear_lateness_ns':100_000})
    def test_post_wait_counterexample_is_not_called_wait_dominant(self):
        self.assertEqual(classify([{'shortfall_ns':5_900_000,'draw_wait_lateness_ns':4_900_000}]),
                         'COUNTEREXAMPLE_WAIT_NECESSITY')
    def test_strict_five_ms_boundary_is_not_relaxed(self):
        self.assertEqual(classify([{'shortfall_ns':5_000_001,'draw_wait_lateness_ns':5_000_000}]),
                         'COUNTEREXAMPLE_WAIT_NECESSITY')
        self.assertEqual(classify([{'shortfall_ns':5_000_000,'draw_wait_lateness_ns':50_000_000}]),
                         'HOLD_NOT_REPRODUCED')
    def test_observed_association_is_not_root_cause_or_pass(self):
        self.assertEqual(classify([{'shortfall_ns':5_900_000,'draw_wait_lateness_ns':5_700_000}]),
                         'ASSOCIATION_ONLY_WAIT_LATE')
    def test_bool_is_not_a_timing_measurement(self):
        with self.assertRaises(ValueError):
            classify([{'shortfall_ns':True,'draw_wait_lateness_ns':9_000_000}])
    def test_missing_denominator_is_invalid(self):
        with self.assertRaises(ValueError): classify([])

if __name__ == '__main__': unittest.main()
