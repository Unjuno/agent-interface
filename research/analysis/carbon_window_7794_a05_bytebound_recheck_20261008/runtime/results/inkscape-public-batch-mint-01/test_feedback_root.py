import json,hashlib,unittest
from pathlib import Path
from runtime.cli_v1.review import present_result
ROOT=Path(__file__).resolve().parent
class FeedbackRootTests(unittest.TestCase):
 def test_previous_owner_root_refuses_and_actual_call_root_preserves_original(self):
  raw=json.loads((ROOT/'feedback-source.json').read_text());case=ROOT/'normal-ordinary';bridge=case/json.loads((case/'owner.json').read_text())['bridge_relative']
  parts=Path(raw['observation']['artifact']['path']).parts;raw['observation']['artifact']['path']=str(case/Path(*parts[parts.index('normal-ordinary')+1:]))
  wrong=present_result(raw,bridge,compact=True,report_refs=True)
  self.assertEqual(wrong['image_status'],'needs_review');self.assertEqual(wrong['image_error'],'image outside run directory');self.assertIsNone(wrong['image'])
  correct=present_result(raw,case/'public-calls/2',compact=True,report_refs=True)
  self.assertEqual(correct['image_status'],'image');self.assertEqual(correct['image_reference']['sha256'],raw['observation']['artifact']['sha256'])
  self.assertEqual(hashlib.sha256(Path(raw['observation']['artifact']['path']).read_bytes()).hexdigest(),correct['image_reference']['sha256'])
if __name__=='__main__':unittest.main()
