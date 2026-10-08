import unittest
from predictor import predict_absolute_float_seconds, predict_origin_shifted_delta_seconds
class Tests(unittest.TestCase):
    def test_simple_line(self):
        ts=[1_000_000_000,2_000_000_000,3_000_000_000]
        xs=[1.0,3.0,5.0]
        self.assertAlmostEqual(predict_absolute_float_seconds(ts,xs,1_000_000_000),7.0,places=12)
        self.assertAlmostEqual(predict_origin_shifted_delta_seconds(ts,xs,1_000_000_000),7.0,places=12)
    def test_degenerate_rejects(self):
        with self.assertRaises(ValueError): predict_origin_shifted_delta_seconds([1,1],[1.0,2.0],1)
if __name__=='__main__': unittest.main()
