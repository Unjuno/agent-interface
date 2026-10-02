import base64,copy,hashlib,unittest
from runtime.integration_checks.delivered_capture import DeliveredCapture

class DeliveredCaptureTests(unittest.TestCase):
    def fixture(self):
        data=b'\x89PNG\r\n\x1a\nfixture'
        digest=hashlib.sha256(data).hexdigest()
        native={'artifact':{'path':'/owned/source.png','sha256':digest},'capture_started_ns':10}
        report={'schema':'agent-interface/runtime-observation-v1','status':'returned','observation_id':'one','observation':native}
        shown={'image_status':'image','image':{'type':'image','mimeType':'image/png','data':base64.b64encode(data).decode()},'image_reference':{'observation_id':'one','path':'/owned/source.png','sha256':digest,'capture_ns':10}}
        return report,shown
    def test_positive_plain_and_compact_do_not_depend_on_receipt_representation(self):
        for receipt in ({'report':{}},{'report':{'report_ref':'/source/raw_report'}}):
            r,s=self.fixture();s['receipt']=receipt;state=DeliveredCapture()
            self.assertEqual(state.accept(r,s),r['observation'])
            r['observation']['artifact']['path']='changed'
            self.assertEqual(state.current['artifact']['path'],'/owned/source.png')
    def test_every_failed_or_omitted_delivery_clears_previous_image(self):
        for case in ['withheld','omitted','wrong_hash','wrong_id','wrong_bytes','wrong_path','capture_error']:
            with self.subTest(case=case):
                r,s=self.fixture();state=DeliveredCapture();state.accept(r,s)
                r,s=self.fixture()
                if case=='withheld':s.update(image_status='no_observation',image=None)
                if case=='omitted':s.update(image=None,image_delivery='omitted_by_request')
                if case=='wrong_hash':s['image_reference']['sha256']='0'*64
                if case=='wrong_id':s['image_reference']['observation_id']='other'
                if case=='wrong_bytes':s['image']['data']='YWJj'
                if case=='wrong_path':s['image_reference']['path']='/other.png'
                if case=='capture_error':r['status']='observation_failed'
                self.assertIsNone(state.accept(r,s));self.assertIsNone(state.current)
    def test_post_dispatch_failure_cannot_admit_nested_returned_capture(self):
        r,s=self.fixture();state=DeliveredCapture();state.accept(r,s)
        dispatch={'schema':'agent-interface/runtime-dispatch-result-v1','post_dispatch_inspection':{'error':'TARGET_CHANGED_DURING_CAPTURE','observation_report':r},'result':{'execution':{}}}
        s['image_reference']['post_dispatch_observation_id']='one';s['image_reference'].pop('observation_id')
        self.assertIsNone(state.accept(dispatch,s));self.assertIsNone(state.current)
    def test_selected_post_dispatch_and_execution_sources_are_distinct(self):
        r,s=self.fixture();native=r['observation']
        for mode in ['post','execution']:
            dispatch={'schema':'agent-interface/runtime-dispatch-result-v1','result':{'execution':{'observations':[native]}}}
            shown=copy.deepcopy(s);shown['image_reference'].pop('observation_id')
            if mode=='post':
                dispatch['post_dispatch_inspection']={'status':'needs_review','observation_report':r}
                shown['image_reference']['post_dispatch_observation_id']='one'
            else:shown['image_reference']['execution_observation_index']=0
            state=DeliveredCapture();self.assertEqual(state.accept(dispatch,shown),native)
            shown['image_reference'].update(execution_observation_index=True,post_dispatch_observation_id='one')
            self.assertIsNone(state.accept(dispatch,shown));self.assertIsNone(state.current)
    def test_malformed_reply_clears_previous_image_without_replay(self):
        r,s=self.fixture();state=DeliveredCapture();state.accept(r,s)
        for bad in [None,{},[],{'image_status':'image','image':[]}]:
            self.assertIsNone(state.accept(r,bad));self.assertIsNone(state.current)
if __name__=='__main__':unittest.main()
