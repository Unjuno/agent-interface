"""Disjoint small construction examples, not the retained corpus."""
import copy
import unittest
from maxima import evaluate, rational
from audit import crossing_oracle


def case(a, b, e=None, domain=None):
    return {'id': 'construction', 'a': a, 'b': b,
            'e': e if e is not None else [0]*len(a),
            'domain': domain if domain is not None else [-3,3]}


class Tests(unittest.TestCase):
    def test_common_mode(self):
        out = evaluate(case([10,6,4], [12,12,12]))
        self.assertEqual(out['box'], [0,1,2]); self.assertEqual(out['joint'], [0])

    def test_incompatible_pairwise(self):
        out = evaluate(case([7,9,9], [0,2,-2]))
        self.assertEqual(out['pairwise'], [0,1,2]); self.assertEqual(out['joint'], [1,2])

    def test_singleton(self):
        self.assertEqual(evaluate(case([7,7,7], [0,2,-2]))['intervals'][0], ['0','0'])

    def test_independent(self):
        out = evaluate(case([7,10,12], [0,0,0], [3,0,2]))
        self.assertEqual(out['joint'], out['box'])

    def test_one(self):
        out = evaluate(case([14], [-8], [3]))
        self.assertEqual(out['joint'], [0]); self.assertEqual(out['intervals'], [['-3','3']])

    def test_closed_endpoint(self):
        self.assertEqual(evaluate(case([7,13], [0,2]))['intervals'][0], ['-3','-3'])

    def test_equal(self):
        self.assertEqual(evaluate(case([7,7], [4,4]))['joint'], [0,1])

    def test_exact_fractions(self):
        self.assertEqual(str(rational('6/8')), '3/4')
        c = case(['7/3','8/3'], [1,-1])
        self.assertEqual(evaluate(c), crossing_oracle(c))

    def test_common_slope_invariance(self):
        c = case([7,13,9], [2,-3,5], [0,1,3])
        moved = copy.deepcopy(c); moved['b'] = [b+77 for b in c['b']]
        self.assertEqual(evaluate(c)['intervals'], evaluate(moved)['intervals'])

    def test_point_domain(self):
        out = evaluate(case([7,9], [2,0], domain=[1,1]))
        self.assertEqual(out['joint'], [0,1])

    def test_invalid(self):
        original = case([7,9], [2,0])
        for key, value in [('a',[True,9]), ('b',[2.0,0]), ('e',[-1,0]),
                           ('b',[0]), ('domain',[3,-3]), ('a',[])]:
            with self.subTest(key=key, value=value):
                c = copy.deepcopy(original); c[key] = value
                with self.assertRaises(ValueError):
                    evaluate(c)

    def test_reference_on_disjoint_cases(self):
        for c in [case([17,21,15], [-3,2,1], [1,2,0]),
                  case([11,11,8], [2,-2,0], [0,1,3]),
                  case([13,14,15,16], [0,1,-1,3], [2,0,1,0])]:
            self.assertEqual(evaluate(c), crossing_oracle(c))


if __name__ == '__main__':
    unittest.main(verbosity=2)
