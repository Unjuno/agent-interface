import base64,hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from compiled_caller import present_native

class CompiledFeedbackTests(unittest.TestCase):
 def fixture(self,root):
  path=root/'images/one.png';path.parent.mkdir();Image.new('RGB',(16,16),'white').save(path)
  native={'artifact':{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mime_type':'image/png','source_raw_sha256':'raw-fixture'},'sha256':'raw-fixture','capture_started_ns':17,'capture_ended_ns':18,'target':'app','native_window_id':123,'frame':'screen_physical_px','region':[0,0,16,16],'width':16,'height':16}
  selected={'observation_id':'one','native':native}
  raw={'schema':'agent-interface/runtime-observation-v1','status':'returned','observation_id':'one','observation':native}
  (root/'public-observation-one.json').write_text(json.dumps(raw))
  return SimpleNamespace(out=root),selected
 def test_original_raw_capture_presented(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);bridge,selected=self.fixture(root)
   for compact in [False,True]:
    raw,shown,native=present_native(bridge,selected,compact=compact)
    self.assertEqual(native,selected['native']);self.assertEqual(base64.b64decode(shown['image']['data']),Path(native['artifact']['path']).read_bytes())
 def test_source_mismatch_or_missing_withholds(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);bridge,selected=self.fixture(root)
   selected['native']['artifact']['sha256']='different'
   raw,shown,native=present_native(bridge,selected)
   self.assertIsNone(native);self.assertIsNone(shown['image'])
   (root/'public-observation-one.json').unlink()
   raw,shown,native=present_native(bridge,selected)
   self.assertIsNone(native);self.assertIsNone(shown['image'])
if __name__=='__main__':unittest.main()
