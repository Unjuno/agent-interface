import tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from Xlib import X
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from save_guard import SemanticSaveGuard

class NativeSaveGuardTests(unittest.TestCase):
 def test_changed_cell_after_control_stops_suffix_and_releases(self):
  fake=FakeX(self);events=[];original=fake.emit
  def emit(display,kind,code=0,**kwargs):
   events.append((kind,code));original(display,kind,code,**kwargs)
   if kind==X.KeyPress and code==1:
    image=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
    image.putpixel((31,31),(255,0,0));fake.raw=image.tobytes('raw','BGRX')
  with tempfile.TemporaryDirectory() as td, patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
   b=NativeHandleBridge(None,{'app':20},'app',Path(td)/'bridge',process_identity=True)
   try:
    source=b.observe();rgb=b.history[source['sequence']][1]
    offset=b.mint('sheet',source['sequence'],[8,8],region_size=[12,12])
    guard=SemanticSaveGuard(b,alias='sheet',offset=offset,regions=[[31,31,32,32]],deadline_ns=time.monotonic_ns()+5_000_000_000)
    guard.arm(source,rgb,cue_record={'cue':'filled','sequence':source['sequence'],'artifact_sha256':source['native']['artifact']['sha256']})
    def verify(stage,native,image):
     guard.validate(stage);return True
    tail=[{'op':'key_chord','keys':['CTRL','a']}]
    with b.input_guard('sheet',offset,tail=tail,verify=verify):
     result=b.keyboard('sheet',offset,tail=tail)
    self.assertNotEqual(result['status'],'completed')
    self.assertEqual(events,[(X.KeyPress,1),(X.KeyRelease,1)])
    self.assertTrue(result['execution']['releases'][-1]['verified'])
    self.assertEqual(fake.down,set())
    self.assertIsNone(b._input_guard)
   finally:b.close()
