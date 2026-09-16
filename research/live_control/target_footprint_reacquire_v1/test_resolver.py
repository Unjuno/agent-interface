import unittest
import cv2,numpy as np
from resolver import resolve,center_gate

class Tests(unittest.TestCase):
    def setUp(self):
        self.ref=np.full((240,500,3),255,np.uint8);cv2.circle(self.ref,(180,120),18,(240,0,176),-1)
        self.tpl=self.ref[97:144,157:204].copy()
    def test_stable(self):self.assertEqual(resolve(self.ref,self.tpl,[180,120])['status'],'UNIQUE')
    def test_same_color_wrong_shape(self):
        cur=np.full_like(self.ref,255);cv2.rectangle(cur,(162,102),(198,138),(240,0,176),-1)
        self.assertTrue(center_gate(self.ref,cur,[180,120],[180,120])['eligible'])
        self.assertEqual(resolve(cur,self.tpl,[180,120])['status'],'MISSING')
    def test_moved_decoy(self):
        cur=np.full_like(self.ref,255);cv2.rectangle(cur,(162,102),(198,138),(240,0,176),-1);cv2.circle(cur,(280,120),18,(240,0,176),-1)
        r=resolve(cur,self.tpl,[180,120]);self.assertTrue(r['eligible']);self.assertEqual(r['point'],[280,120])
    def test_duplicate_refuses(self):
        cur=self.ref.copy();cv2.circle(cur,(280,120),18,(240,0,176),-1)
        self.assertEqual(resolve(cur,self.tpl,[180,120])['status'],'AMBIGUOUS')
    def test_missing(self):self.assertEqual(resolve(np.full_like(self.ref,255),self.tpl,[180,120])['status'],'MISSING')
    def test_bounded_search(self):
        cur=np.full_like(self.ref,255);cv2.circle(cur,(350,120),18,(240,0,176),-1)
        self.assertFalse(resolve(cur,self.tpl,[180,120])['eligible'])
    def test_nan(self):
        with self.assertRaises(ValueError):resolve(self.ref,self.tpl,[float('nan'),120])
    def test_dtype(self):
        with self.assertRaises(ValueError):resolve(self.ref.astype(float),self.tpl,[180,120])
if __name__=='__main__':unittest.main()
