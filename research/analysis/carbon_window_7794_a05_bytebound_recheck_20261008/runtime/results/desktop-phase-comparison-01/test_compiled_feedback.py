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

 def test_completed_graph_opens_actual_inspection_session_before_feedback(self):
  from unittest.mock import patch
  from compiled_caller import run
  from runtime.cli_v1.mcp_session import MCPSessionOwner
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);bridge,selected=self.fixture(root)
   source=json.loads((root/'public-observation-one.json').read_text())
   execution={'result':{'status':'completed','recovery_required':False,'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}}
   (root/'effect.json').write_text(json.dumps(execution))
   bridge.sequence=1;bridge.mint_reference=lambda *a,**k:{'offset':[1,1]}
   receipt={'outcome':'SAFE_YIELD','reason':'association_changed','transitions':[{'action':'save','release_verified':True,'effect_ref':'effect'}],'observations':[]}
   owner=MCPSessionOwner.__new__(MCPSessionOwner)
   owner.state='new';owner.session=None;owner.target_review=None
   def open_session():
    owner.state='open';owner.session=SimpleNamespace(recovery_required=False);return owner.session
   owner.get=open_session
   def inspect(*a,**k):
    import copy
    raw=copy.deepcopy(source);directory=Path(k['capture_directory']);directory.mkdir(exist_ok=True)
    destination=directory/'post.png';destination.write_bytes(Path(source['observation']['artifact']['path']).read_bytes())
    raw['observation']['artifact']['path']=str(destination)
    return {'status':'needs_review','observation_report':raw}
   owner.inspect_target=inspect
   with patch('methods.run',return_value={'receipt':receipt}):
    row,raw,shown,native=run(bridge,owner,{'box':[0,0,2,2],'pixels':bytes(12)},{'A1':[0,0,1,1],'A2':[0,0,1,1]},root/'method')
   self.assertEqual(owner.state,'open');self.assertEqual(shown['image_status'],'image');self.assertEqual(native['artifact']['sha256'],selected['native']['artifact']['sha256'])

if __name__=='__main__':unittest.main()
