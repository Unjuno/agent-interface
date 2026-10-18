import unittest
from interval_ttc import interval_ttc,classify
from candidate import estimate
from generate import build, PROFILES
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(interval_ttc(10,0,12,1,0),(6.,6.))
 def test_contains_nominal(self):
  x=interval_ttc(10,0,12,1,.25); self.assertIsNotNone(x); self.assertLessEqual(x[0],6); self.assertGreaterEqual(x[1],6)
 def test_zero_or_nonexpansion(self): self.assertIsNone(interval_ttc(10,0,10.5,1,.5)); self.assertIsNone(interval_ttc(10,0,9,1,0))
 def test_invalid(self): self.assertIsNone(interval_ttc(1,2,2,1,0)); self.assertIsNone(interval_ttc(float('nan'),0,2,1,0))
 def test_classification(self):
  self.assertEqual(classify((1,2)),"YIELD"); self.assertEqual(classify((2.01,3)),"CLEAR"); self.assertEqual(classify((1.9,2.1)),"UNKNOWN"); self.assertEqual(classify(None),"UNKNOWN")
 def test_candidate_multiframe_containment(self):
  h=[{"t_s":i/30,"radius_px":10+i,"bound_px":0.1,"track_id":"a"} for i in range(12)]
  point, interval=estimate(h)
  truth=21.0/30.0
  self.assertAlmostEqual(point, truth)
  self.assertLessEqual(interval[0], truth)
  self.assertGreaterEqual(interval[1], truth)
 def test_candidate_rejects_unsupported_track_and_contiguous_occlusion(self):
  base=[{"t_s":i/30,"radius_px":10+i,"bound_px":0.1,"track_id":"a"} for i in range(6)]
  swapped=[dict(x) for x in base]; swapped[-1]["track_id"]="b"
  occluded=[dict(x) for x in base]; occluded[3]["radius_px"]=None; occluded[4]["radius_px"]=None
  self.assertIsNone(estimate(swapped)[1])
  self.assertIsNone(estimate(occluded)[1])
 def test_corpus_construction_shape_only(self):
  public, oracle=build()
  self.assertEqual((len(public),len(oracle)),(200,200))
  self.assertEqual({x["profile"] for x in oracle},set(PROFILES))
  self.assertNotIn("hazard",public[0])
  self.assertEqual(sum(x["split"]=="calibration" for x in oracle),100)
if __name__=='__main__': unittest.main()
