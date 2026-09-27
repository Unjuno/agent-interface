"""Disjoint construction examples only; no formal seeds or full corpus."""
import unittest
from policy import quantile95,calibrate,possible_max,predict
from audit import order_stat,reference_set

class ContractTests(unittest.TestCase):
    def test_rank(self):
        self.assertEqual(quantile95(list(range(19))),18)
        self.assertEqual(quantile95(list(range(999))),949)
    def test_histogram_parity(self):
        a=[0]*19+[10]
        self.assertEqual(quantile95(a),order_stat(a))
    def test_zero_residuals(self):
        self.assertEqual(calibrate([[0]*4 for _ in range(20)]),
                         {"MARGINAL95":[0]*4,"JOINT95":[0]*4})
    def test_ties(self):
        self.assertEqual(possible_max([2,2,0,0],[0]*4),[0,1])
    def test_singleton(self):
        self.assertEqual(possible_max([3,2,1,0],[0]*4),[0])
    def test_joint_wide(self):
        self.assertEqual(possible_max([3,12,1,0],[10]*4),[0,1,2,3])
    def test_marginal_counterexample(self):
        self.assertEqual(possible_max([3,12,1,0],[0]*4),[1])
    def test_shift_counterexample(self):
        self.assertEqual(possible_max([3,32,1,0],[10]*4),[1])
    def test_reference(self):
        for s,q in [([3,12,1,0],[10]*4),([2,2,0,0],[0]*4)]:
            self.assertEqual(possible_max(s,q),reference_set(s,q))
    def test_bool_rejected(self):
        with self.assertRaises(ValueError): possible_max([True,1,2,3],[0]*4)
    def test_negative_radius(self):
        with self.assertRaises(ValueError): possible_max([0]*4,[-1]*4)
    def test_prediction_keys(self):
        self.assertEqual(set(predict([0]*4,{"MARGINAL95":[0]*4,"JOINT95":[0]*4})),
                         {"TOP1_POINT","MARGINAL95","JOINT95"})

if __name__=="__main__": unittest.main()
