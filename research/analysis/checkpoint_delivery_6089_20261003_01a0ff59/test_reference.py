"""Literal construction calibration; imports neither retained code nor producer."""
import copy
import json
import pathlib
import unittest
from audit import path_oracle, reference

CASES = json.loads((pathlib.Path(__file__).parent / 'CASES.json').read_bytes())['cases']

class ReferenceTests(unittest.TestCase):
    def test_path_prefix_and_release_boundary(self):
        case = next(x['case'] for x in CASES if x['context'] == 'k1_boundary')
        self.assertEqual(path_oracle(case, 6), {'safe': True, 'first_unsafe_step': None, 'worst_position': 12})
        self.assertEqual(path_oracle(case, 7), {'safe': False, 'first_unsafe_step': 7, 'worst_position': 14})

    def test_empty_is_not_delivered_fresh(self):
        case = CASES[0]['case']
        expected = reference(case)
        self.assertFalse(expected['policy_b_release_on_absence']['receipt_was_usable'])
        self.assertEqual(expected['policy_c_loss_robust']['actual_status'], 'BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE')

    def test_explicit_missing_has_identical_full_output(self):
        case = copy.deepcopy(CASES[0]['case'])
        missing = copy.deepcopy(case)
        missing['checkpoint_events'] = [{'kind': 'MISSING'}]
        self.assertEqual(reference(case), reference(missing))

    def test_valid_receipt_and_invalidation_are_distinct(self):
        fresh = reference(CASES[2]['case'])
        invalidated = reference(CASES[10]['case'])
        self.assertEqual(fresh['policy_c_loss_robust']['actual_status'], 'NO_LOSS_CONTROL')
        self.assertTrue(invalidated['policy_b_release_on_absence']['receipt_was_usable'])
        self.assertEqual(invalidated['policy_c_loss_robust']['selected_horizon'], 0)

    def test_hypothesized_fallback_hides_planted_optimism(self):
        case = next(x['case'] for x in CASES if x['context'] == 'k1_boundary' and x['encoding'] == 'empty')
        desired = reference(case)
        hypothetical = reference(case, legacy_empty=True)
        self.assertFalse(desired['policy_a_optimistic']['safe'])
        self.assertTrue(hypothetical['policy_a_optimistic']['safe'])
        self.assertEqual(desired['policy_c_loss_robust']['selected_horizon'], 4)

if __name__ == '__main__':
    unittest.main()
