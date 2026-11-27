import copy
from types import SimpleNamespace
import unittest
from PIL import Image
from research.live_control.reviewed_modal_guard_v1 import ReviewedModalGuard

class Bridge:
 def __init__(self):
  self.scope='s';self.binding_revision=0;self.sequence=0;self.target='app';self.backend=SimpleNamespace(targets={'app':SimpleNamespace(id=42)});self.history={};self.focus=True;self.title='Text Import';self.binding={'focus':42,'surface':42,'geometry':[0,0,16,16]};self.review_required=False;self.session=SimpleNamespace(recovery_required=False)
 def _binding(self):return copy.deepcopy(self.binding)
 def _focus_within_target(self):return self.focus
 def _window_title(self):return self.title
 def capture(self,img,ns=1000):
  self.sequence+=1;n={'sequence':self.sequence,'binding_revision':self.binding_revision,'capture_ns':ns,'pointer_binding':self._binding(),'native':{'native_window_id':42,'artifact':{'sha256':'x'}}};self.history[self.sequence]=(copy.deepcopy(n),img.copy());return n

class ReviewedModalGuardTests(unittest.TestCase):
 def setUp(self):
  self.b=Bridge();self.img=Image.new('RGB',(16,16),'white');self.regions=((2,2,8,8),(10,10,14,14));self.now=1010
 def guard(self,reference=None):
  return ReviewedModalGuard(self.b,reference=reference or self.img,regions=self.regions,title='Text Import',deadline_ns=2000,max_age_ns=100,clock=lambda:self.now)
 def test_exact_fresh_and_reference_snapshot_immutable(self):
  reference=self.img.copy();g=self.guard(reference);n=self.b.capture(self.img);g.arm(n,self.img);reference.putpixel((3,3),(0,0,0));fresh=self.b.capture(self.img);self.assertTrue(g.verify_capture(fresh,self.img))
 def test_changed_checked_region_is_refused(self):
  g=self.guard();n=self.b.capture(self.img);g.arm(n,self.img);changed=self.img.copy();changed.putpixel((3,3),(0,0,0));fresh=self.b.capture(changed);self.assertFalse(g.verify_capture(fresh,changed))
 def test_changed_outside_reviewed_regions_is_not_a_claim(self):
  g=self.guard();n=self.b.capture(self.img);g.arm(n,self.img);changed=self.img.copy();changed.putpixel((0,0),(0,0,0));fresh=self.b.capture(changed);self.assertTrue(g.verify_capture(fresh,changed))
 def test_focus_title_binding_sequence_and_deadline_fail_closed(self):
  for change in ('focus','title','binding','sequence','deadline','stale'):
   with self.subTest(change=change):
    self.setUp();g=self.guard();n=self.b.capture(self.img);g.arm(n,self.img);fresh=self.b.capture(self.img)
    if change=='focus':self.b.focus=False
    if change=='title':self.b.title='Other'
    if change=='binding':self.b.binding['surface']=43
    if change=='sequence':self.b.sequence+=1
    if change=='deadline':self.now=2000
    if change=='stale':self.now=1200
    self.assertFalse(g.verify_capture(fresh,self.img))
 def test_arm_rejects_mismatch_and_duplicate_arm(self):
  g=self.guard();changed=self.img.copy();changed.putpixel((3,3),(0,0,0));n=self.b.capture(changed)
  with self.assertRaises(ValueError):g.arm(n,changed)
  n=self.b.capture(self.img);g.arm(n,self.img)
  with self.assertRaises(ValueError):g.arm(n,self.img)
 def test_boolean_revision_does_not_alias_integer_zero(self):
  g=self.guard();n=self.b.capture(self.img);g.arm(n,self.img);fresh=self.b.capture(self.img);fresh['binding_revision']=False;self.b.history[fresh['sequence']]=(copy.deepcopy(fresh),self.img.copy());self.assertFalse(g.verify_capture(fresh,self.img))
 def test_binding_boolean_does_not_alias_integer_zero(self):
  g=self.guard();n=self.b.capture(self.img);g.arm(n,self.img);fresh=self.b.capture(self.img);fresh['pointer_binding']['geometry'][0]=False;self.b.history[fresh['sequence']]=(copy.deepcopy(fresh),self.img.copy());self.assertFalse(g.verify_capture(fresh,self.img))
 def test_bad_region_and_unknown_capture_rejected(self):
  for regions in [(),((0,0,17,2),),((1,1,1,2),),((True,1,2,2),)]:
   with self.subTest(regions=regions):
    with self.assertRaises(ValueError):ReviewedModalGuard(self.b,reference=self.img,regions=regions,title='Text Import',deadline_ns=2000,clock=lambda:self.now)
  g=self.guard();self.assertFalse(g.verify_capture({},self.img))
if __name__=='__main__':unittest.main()
