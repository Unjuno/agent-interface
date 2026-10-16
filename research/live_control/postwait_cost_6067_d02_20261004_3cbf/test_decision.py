"""Hand-derived contrasts; dropping the pair gate must fail these tests."""
import unittest
from decision import contrast

def cells(full=1_000_000, minimal=100_000):
    return [{'pair': p, 'treatment': t, 'delays_ns': [value] * 8}
            for p in range(6) for t, value in [('full', full), ('minimal', minimal)]]

class DecisionTests(unittest.TestCase):
    def test_consistent_finite_reduction(self):
        result = contrast(cells())
        self.assertEqual(result['status'], 'SUPPORTED_FINITE_CONTRAST')
        self.assertEqual(result['paired_reductions_ns'], [900_000] * 6)
        self.assertEqual(result['pooled_reduction_ns'], 900_000)

    def test_three_large_pairs_cannot_replace_five_pair_gate(self):
        data = cells(full=100_000)
        for row in data:
            if row['pair'] < 3 and row['treatment'] == 'full':
                row['delays_ns'] = [10_000_000] * 8
        self.assertEqual(contrast(data)['status'], 'HOLD_NOT_REPRODUCED')

    def test_equal_delays_are_hold(self):
        self.assertEqual(contrast(cells(full=100_000))['status'], 'HOLD_NOT_REPRODUCED')

    def test_exact_half_millisecond_boundary_inclusive(self):
        self.assertEqual(contrast(cells(full=600_000))['status'],'SUPPORTED_FINITE_CONTRAST')

    def test_exactly_five_qualifying_pairs(self):
        data=cells(full=600_000)
        data[10]['delays_ns']=[599_999]*8
        self.assertEqual(contrast(data)['status'],'SUPPORTED_FINITE_CONTRAST')

    def test_five_pairs_still_require_pooled_threshold(self):
        data=cells()
        for row in data:
            p,t=row['pair'],row['treatment']
            value=(1_000_000 if t=='full' else 0) if p<3 else (
                (100_000_000 if t=='full' else 99_000_000) if p<5 else (0 if t=='full' else 100_000_000))
            row['delays_ns']=[value]*8
        self.assertEqual(contrast(data)['status'],'HOLD_NOT_REPRODUCED')

    def test_incomplete_pairs_rejected(self):
        with self.assertRaises(ValueError):
            contrast(cells()[:-1])

    def test_duplicate_pair_rejected(self):
        with self.assertRaises(ValueError):
            contrast(cells() + [cells()[0]])

    def test_boolean_delay_rejected(self):
        data = cells()
        data[0]['delays_ns'][0] = True
        with self.assertRaises(ValueError):
            contrast(data)

if __name__ == '__main__':
    unittest.main()
