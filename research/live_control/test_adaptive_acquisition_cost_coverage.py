"""All-attempt cost coverage controls; synthetic inert adapters, no model/input."""
import json,os,unittest
from pathlib import Path
from adaptive_acquisition_caller_v3 import ModelFailure,run
TARGET={'handle':'cost-control'}
class Clock:
    def __init__(self):self.value=0
    def __call__(self):self.value+=10;return self.value
def result(output,cost,call_id):
    return {'call_id':call_id,'output':output,'usage':{'input_tokens':21,'output_tokens':3},'requested_model':'synthetic-no-provider','requested_effort':'synthetic','cost':cost,'visible_images_submitted':0,'wait_ns':23}
def failure(_):raise ModelFailure('synthetic upstream',call_id='failed-call',usage={'input_tokens':11,'output_tokens':2},visible_images_submitted=0,wait_ns=31)
class CostCoverage(unittest.TestCase):
    def route(self,name,*,coarse='provided',coarse_fn=None,anchor_fn=None,warm=False,missing=False):
        spec={'target':'Save','route':'reuse' if warm else 'cold','coarse_origin':'caller_provided' if warm or coarse=='provided' else 'model_produced','provided_coarse':None if warm or coarse!='provided' else {'status':'candidate'},'cached_target':TARGET if warm else None,'local_repair_on':[],'repair_on':[],'session_id':'synthetic-cost-i12'}
        adapters={'observe_source':lambda _: {},'acquire_anchor':lambda _: {},'reuse_revalidate':lambda _:{'status':'revalidated'},'final_revalidate':lambda _:{'status':'revalidated'},'execute':lambda _:{'status':'completed'},'verify_effect':lambda _:{'status':'succeeded'}}
        if not missing:adapters['coarse_model']=coarse_fn or (lambda _:result({'status':'candidate'},5,'coarse'))
        adapters['anchor_model']=anchor_fn or (lambda _:result({'status':'target_reference','target':TARGET},7,'anchor'))
        ids=iter(['attempt-1','attempt-2','attempt-3'])
        row=run(spec,adapters,clock=Clock(),id_factory=lambda:next(ids))
        path=Path(os.environ.get('TRACE_OUTPUT', os.devnull))
        with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps({'case':name,'result':row},sort_keys=True)+'\n')
        return row
    def test_zero_attempt_warm_cost_zero(self):
        r=self.route('zero_attempt_warm',warm=True);self.assertEqual(r['accounting']['attempted_calls'],0);self.assertEqual(r['accounting']['cost'],0)
    def test_one_known_success_exact_cost(self):
        r=self.route('one_known_success');self.assertEqual(r['accounting']['attempted_calls'],1);self.assertEqual(r['accounting']['cost'],7)
    def test_one_unknown_success_cost_unavailable(self):
        r=self.route('one_unknown_success',anchor_fn=lambda _:result({'status':'target_reference','target':TARGET},None,'anchor'));self.assertIsNone(r['accounting']['cost'])
    def test_first_upstream_failure_cost_unavailable(self):
        r=self.route('first_upstream_failure',coarse='model',coarse_fn=failure);self.assertEqual(r['outcome'],'CALLER_FAILED');self.assertEqual(r['accounting']['attempted_calls'],1);self.assertEqual(r['accounting']['completed_calls'],0);self.assertIsNone(r['accounting']['cost'])
    def test_success_then_failure_cost_unavailable(self):
        r=self.route('success_then_failure',coarse='model',anchor_fn=failure);self.assertEqual(r['outcome'],'CALLER_FAILED');self.assertEqual(r['accounting']['attempted_calls'],2);self.assertEqual(r['accounting']['completed_calls'],1);self.assertIsNone(r['accounting']['cost'])
    def test_malformed_result_cost_unavailable(self):
        r=self.route('malformed_result',coarse='model',coarse_fn=lambda _:{'cost':9});self.assertEqual(r['outcome'],'CALLER_FAILED');self.assertEqual(r['accounting']['attempted_calls'],1);self.assertIsNone(r['accounting']['cost'])
    def test_missing_adapter_cost_unavailable(self):
        r=self.route('missing_adapter',coarse='model',missing=True);self.assertEqual(r['outcome'],'CALLER_FAILED');self.assertEqual(r['accounting']['attempted_calls'],1);self.assertIsNone(r['accounting']['cost'])
    def test_two_known_successes_exact_total(self):
        r=self.route('two_known_successes',coarse='model');self.assertEqual(r['accounting']['attempted_calls'],2);self.assertEqual(r['accounting']['cost'],12)
    def test_zero_cost_safe_stop_is_preserved(self):
        r=self.route('zero_cost_safe_stop',coarse='model',coarse_fn=lambda _:result({'status':'no_match'},0,'coarse'));self.assertEqual(r['outcome'],'SAFE_STOP');self.assertEqual(r['accounting']['attempted_calls'],1);self.assertEqual(r['accounting']['cost'],0)
if __name__=='__main__':unittest.main()
