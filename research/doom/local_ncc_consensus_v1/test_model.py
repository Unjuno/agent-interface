import unittest, numpy as np
from model import estimate_global, estimate_band_consensus
from cases import scene
class T(unittest.TestCase):
    def test_rigid_sign(self):
        r,c=scene(990901,90,90); self.assertEqual(estimate_global(r,c)['shift_px'],90); self.assertEqual(estimate_band_consensus(r,c)['shift_px'],90)
    def test_parallax_construction(self):
        r,c=scene(990902,60,175); self.assertEqual(estimate_global(r,c)['shift_px'],175); self.assertEqual(estimate_band_consensus(r,c)['shift_px'],60)
    def test_negative(self):
        r,c=scene(990903,-85,-185); self.assertEqual(estimate_band_consensus(r,c)['shift_px'],-85)
    def test_flat_unknown(self):
        a=np.full((140,320),128.0); self.assertNotEqual(estimate_band_consensus(a,a)['status'],'IDENTIFIED')
    def test_shape_reject(self):
        with self.assertRaises(ValueError): estimate_band_consensus(np.zeros((2,2)),np.zeros((2,2)))
if __name__=='__main__': unittest.main()
