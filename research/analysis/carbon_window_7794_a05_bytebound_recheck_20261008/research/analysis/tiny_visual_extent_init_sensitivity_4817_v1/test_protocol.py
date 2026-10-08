import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import run_cuda
class ProtocolTests(unittest.TestCase):
 def test_frozen_constants(self):
  self.assertEqual(run_cuda.DATA_SEED,89100471); self.assertEqual(run_cuda.INIT_SEED,58100472)
  self.assertEqual(run_cuda.STEPS,1000); self.assertEqual(run_cuda.LR,.2); self.assertEqual(run_cuda.THRESHOLD,.75)
 def test_generated_rows_and_labels(self):
  train,base,held=run_cuda.dataset(run_cuda.DATA_SEED)
  self.assertEqual(train[0].shape,(160,1,30,40)); self.assertEqual(base[0].shape,(80,1,30,40))
  self.assertEqual(len(held),8); self.assertEqual(int(train[1].sum()),80); self.assertEqual(int(base[1].sum()),40)
  for x,y in held.values(): self.assertEqual(x.shape,(80,1,30,40)); self.assertEqual(int(y.sum()),40)
 def test_paired_initialization(self):
  a=run_cuda.init_np(run_cuda.INIT_SEED,False); b=run_cuda.init_np(run_cuda.INIT_SEED,True)
  for i in (0,1,3): np.testing.assert_array_equal(a[i],b[i])
  np.testing.assert_array_equal(a[2],b[2][:4]); self.assertTrue(np.all(b[2][4:]==0))
 def test_new_initialization_is_distinct(self):
  old=run_cuda.init_np(89100472,True); new=run_cuda.init_np(run_cuda.INIT_SEED,True)
  self.assertTrue(any(not np.array_equal(a,b) for a,b in zip(old,new)))
if __name__=="__main__": unittest.main()
