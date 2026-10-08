import hashlib,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from runtime.cli_v1.review import present_result
from runtime.integration_checks.delivered_capture import DeliveredCapture

class FeedbackRootTests(unittest.TestCase):
    def fixture(self,root):
        path=root/'images'/'capture.png';path.parent.mkdir();Image.new('RGB',(20,20),'white').save(path)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        native={'sha256':'raw','capture_started_ns':10,'artifact':{'mime_type':'image/png','path':str(path),'sha256':sha,'source_raw_sha256':'raw'}}
        raw={'schema':'agent-interface/runtime-dispatch-result-v1','status':'returned','result':{'status':'completed','recovery_required':False,'execution':{'ended_ns':1,'releases':[{'verified':True,'keys_down':[],'buttons_down':[],'monotonic_ns':2}],'observations':[]}},'post_dispatch_inspection':{'status':'needs_review','input_dispatched':False,'authority_granted':False,'review_request':{'tool':'interface_review_target'},'observation_report':{'status':'returned','input_dispatched':False,'side_effect_authority':False,'observation_id':'selected','observation':native}}}
        return raw,native
    def test_original_sibling_root_refuses_and_method_root_delivers_same_raw(self):
        for compact in [False,True]:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);method=root/'public-method-2';method.mkdir();public=root/'public';public.mkdir()
                raw,native=self.fixture(method);original=json.dumps(raw,sort_keys=True)
                refused=present_result(raw,public,compact=compact,report_refs=compact)
                self.assertEqual(refused['image_error'],'image outside run directory')
                self.assertIsNone(DeliveredCapture().accept(raw,refused))
                shown=present_result(raw,method,compact=compact,report_refs=compact)
                self.assertEqual(shown['image_status'],'image')
                self.assertEqual(DeliveredCapture().accept(raw,shown),native)
                self.assertEqual(json.dumps(raw,sort_keys=True),original)
    def test_correct_method_root_still_refuses_outside_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);method=root/'public-method-2';method.mkdir();outside=root/'outside';outside.mkdir()
            raw,_=self.fixture(outside);shown=present_result(raw,method)
            self.assertEqual(shown['image_status'],'needs_review')
            self.assertIsNone(shown['image']);self.assertIsNone(DeliveredCapture().accept(raw,shown))
if __name__=='__main__':unittest.main()
