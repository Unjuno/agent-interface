import hashlib,tempfile,unittest
from pathlib import Path
from PIL import Image
import numpy as np
from metric import horizontal_shift,decide
EXPECTED='04f8ea8c42f950b5e8df9e45cf5a19cc7cc0ab38558b3f7568aabdcb298f93c9'
class T(unittest.TestCase):
 def img(self,a):
  p=Path(tempfile.mktemp(suffix='.png'));Image.fromarray(a.astype('uint8'),'RGB').save(p);self.addCleanup(lambda:p.unlink(missing_ok=True));return p
 def test_metric_identity(self): self.assertEqual(hashlib.sha256((Path(__file__).parent/'metric.py').read_bytes()).hexdigest(),EXPECTED)
 def test_missing(self): self.assertEqual(decide('HORIZONTAL_SHIFT_STOP',None,Path('x'))['status'],'UNKNOWN_MISSING_REFERENCE')
 def test_identical(self):
  a=np.zeros((480,640,3),dtype=np.uint8);a[120:260,200:400]=np.arange(200,dtype=np.uint8)[None,:,None];p=self.img(a);r=horizontal_shift(p,p);self.assertEqual(r['status'],'MATCHED');self.assertEqual(r['shift_px'],0)
 def test_bad_shape(self):
  p=self.img(np.zeros((10,10,3),dtype=np.uint8));
  with self.assertRaises(ValueError): horizontal_shift(p,p)
 def test_stop_gate(self):
  self.assertEqual(__import__('metric').SHIFT_STOP_PX,34);self.assertEqual(__import__('metric').SEARCH_PX,160)
if __name__=='__main__':unittest.main()
