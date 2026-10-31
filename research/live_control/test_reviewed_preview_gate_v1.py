from types import SimpleNamespace
import subprocess,unittest
from PIL import Image
from research.live_control.reviewed_preview_gate_v1 import ReviewedPreviewGate
from research.live_control.test_reviewed_modal_guard_v1 import Bridge

def tsv(text,conf='95'):
 return ('level\tconf\ttext\n5\t'+conf+'\t'+text+'\n').encode()
class PreviewGateTests(unittest.TestCase):
 def setUp(self):
  self.b=Bridge();self.img=Image.new('RGB',(16,16),'white');self.now=1010;self.calls=[]
 def runner(self,command,**kwargs):
  self.calls.append((command,kwargs));return SimpleNamespace(returncode=0,stdout=tsv(('641','283')[len(self.calls)-1]),stderr=b'')
 def gate(self,runner=None):
  return ReviewedPreviewGate(self.b,reference=self.img,static_regions=((0,0,1,1),),preview_regions=((2,2,8,8),(10,10,14,14)),title='Text Import',expected=('641','283'),deadline_ns=2000,max_age_ns=100,clock=lambda:self.now,runner=runner or self.runner)
 def test_matching_ocr_arms_guard_on_same_capture(self):
  g=self.gate();n=self.b.capture(self.img);r=g.arm(n,self.img);self.assertEqual(r['status'],'armed');self.assertIsNotNone(g.guard);self.assertEqual(len(self.calls),2)
  changed=self.img.copy();changed.putpixel((3,3),(0,0,0));fresh=self.b.capture(changed);self.assertFalse(g.guard.verify_capture(fresh,changed))
 def test_wrong_value_never_arms(self):
  def wrong(cmd,**kw):return SimpleNamespace(returncode=0,stdout=tsv('999'),stderr=b'')
  g=self.gate(wrong);n=self.b.capture(self.img);self.assertEqual(g.arm(n,self.img)['status'],'wrong');self.assertIsNone(g.guard)
 def test_low_confidence_and_timeout_are_unknown(self):
  for kind in ('low','timeout','badtype','toolarge'):
   with self.subTest(kind=kind):
    self.setUp()
    def bad(cmd,**kw):
     if kind=='timeout':raise subprocess.TimeoutExpired(cmd,kw['timeout'])
     return SimpleNamespace(returncode=0,stdout={'low':tsv('641','89'),'badtype':'bad','toolarge':b'x'*(1024*1024+1)}[kind],stderr=b'')
    g=self.gate(bad);n=self.b.capture(self.img);self.assertEqual(g.arm(n,self.img)['status'],'unknown');self.assertIsNone(g.guard)
 def test_capture_replaced_during_ocr_never_arms(self):
  def replaced(cmd,**kw):self.b.capture(self.img);return SimpleNamespace(returncode=0,stdout=tsv('641'),stderr=b'')
  g=self.gate(replaced);n=self.b.capture(self.img);self.assertEqual(g.arm(n,self.img)['status'],'unknown');self.assertIsNone(g.guard)
 def test_expiry_between_crops_never_arms(self):
  def delayed(cmd,**kw):self.now=1200;return SimpleNamespace(returncode=0,stdout=tsv('641'),stderr=b'')
  g=self.gate(delayed);n=self.b.capture(self.img);self.assertEqual(g.arm(n,self.img)['status'],'unknown');self.assertIsNone(g.guard)
 def test_mismatch_of_static_reference_never_calls_ocr(self):
  g=self.gate();changed=self.img.copy();changed.putpixel((0,0),(0,0,0));n=self.b.capture(changed);self.assertEqual(g.arm(n,changed)['status'],'unknown');self.assertEqual(self.calls,[])
 def test_bad_construction_fails_before_ocr(self):
  with self.assertRaises(ValueError):ReviewedPreviewGate(self.b,reference=self.img,static_regions=[],preview_regions=((2,2,8,8),(10,10,14,14)),title='Text Import',expected=('641','283'),deadline_ns=2000,clock=lambda:self.now,runner=self.runner)
  with self.assertRaises(ValueError):ReviewedPreviewGate(self.b,reference=self.img,static_regions=((0,0,1,1),),preview_regions=((2,2,8,8),(10,10,14,14)),title='Text Import',expected=('\u0036x','283'),deadline_ns=2000,clock=lambda:self.now,runner=self.runner)
  self.assertEqual(self.calls,[])
 def test_gate_is_single_use_after_failure(self):
  def bad(cmd,**kw):raise TimeoutError()
  g=self.gate(bad);n=self.b.capture(self.img);self.assertEqual(g.arm(n,self.img)['status'],'unknown')
  with self.assertRaises(ValueError):g.arm(n,self.img)
if __name__=='__main__':unittest.main()
