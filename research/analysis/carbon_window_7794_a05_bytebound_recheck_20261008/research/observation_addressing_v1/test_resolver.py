import unittest
import numpy as np
from resolver import resolve, regions, center

class Tests(unittest.TestCase):
    def setUp(self):
        self.s=[[211,173,22,16]];self.a=[{'name':'Save','box':self.s[0]}]
    def r(self,arm,cur=None,ax=None,prev=None):
        return resolve(arm,self.s if prev is None else prev,self.s,self.s if cur is None else cur,self.a if ax is None else ax)
    def test_coordinate(self):self.assertEqual(self.r('coordinate')['point'],[222,181])
    def test_grid_is_quantization_not_target(self):self.assertEqual(self.r('grid_center')['point'],[192,192])
    def test_grid_local_shift(self):self.assertEqual(self.r('grid_candidates',[[243,173,22,16]])['point'],[254,181])
    def test_grid_jump_refusal(self):self.assertIsNone(self.r('grid_candidates',[[435,173,22,16]])['point'])
    def test_grid_duplicate_refusal(self):self.assertIsNone(self.r('grid_candidates',self.s+[[250,173,10,16]])['point'])
    def test_prediction(self):self.assertEqual(self.r('predict',prev=[[179,173,22,16]])['point'],[254,181])
    def test_native(self):self.assertEqual(self.r('ax')['point'],[222,181])
    def test_native_ambiguity(self):self.assertIsNone(self.r('ax',ax=self.a*2)['point'])
    def test_hybrid_native_duplicate_disambiguation(self):
        self.assertEqual(self.r('hybrid',ax=self.a+[{'name':'Save','box':[400,173,22,16]}])['point'],[222,181])
    def test_hybrid_conflict(self):
        self.assertEqual(self.r('hybrid',ax=[{'name':'Cancel','box':self.s[0]},{'name':'Save','box':[400,173,22,16]}])['status'],'CROSS_MODAL_CONFLICT')
    def test_hybrid_canvas(self):self.assertEqual(self.r('hybrid',ax=[])['status'],'PIXEL_FALLBACK_NATIVE_ABSENT')
    def test_hybrid_occlusion(self):self.assertIsNone(self.r('hybrid',cur=[])['point'])
    def test_hybrid_removed(self):self.assertIsNone(self.r('hybrid',cur=[],ax=[])['point'])
    def test_hybrid_duplicate_visual_native(self):
        self.assertIsNone(self.r('hybrid',cur=self.s+[[400,173,22,16]],ax=self.a+[{'name':'Save','box':[400,173,22,16]}])['point'])
    def test_source_ambiguous(self):self.assertEqual(self.r('predict',prev=self.s*2)['status'],'SOURCE_AMBIGUOUS')
    def test_unknown_arm(self):
        with self.assertRaises(ValueError):self.r('unknown')
    def test_exact_region(self):
        a=np.zeros((50,60,3),np.uint8);a[7:23,11:33]=[220,40,180]
        self.assertEqual(regions(a),[[11,7,22,16]])

if __name__=='__main__':unittest.main(verbosity=2)
