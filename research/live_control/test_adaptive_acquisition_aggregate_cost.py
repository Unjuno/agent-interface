import json,math,os,sys,unittest
from pathlib import Path
from adaptive_acquisition_caller_v3 import run
CASES={'positive_overflow':([1e308,1e308],None),'max_overflow':([sys.float_info.max,sys.float_info.max],None),'huge_mixed':([2**4096,0.5],None),'finite_sum':([0.125,0.375],0.5),'finite_credit':([sys.float_info.max,-sys.float_info.max],0.0),'unknown':([None,0.375],None),'zero_cost':([0.0,0.0],0.0),'individual_nan':([float('nan'),0.375],None),'individual_inf':([float('inf'),0.375],None),'individual_negative_inf':([-float('inf'),0.375],None)}
def wire(value):
    if type(value) is float and not math.isfinite(value):return {'$numeric':repr(value)}
    if type(value) is dict:return {k:wire(v) for k,v in value.items()}
    if type(value) is list:return [wire(v) for v in value]
    return value
class Aggregate(unittest.TestCase):
    def check_case(self,name):
        values,expected=CASES[name];events=[];target={'handle':'aggregate-i16'}
        def stage(label,out):
            def fn(payload):
                events.append({'stage':label,'payload':payload})
                return out
            return fn
        def model(label,index,out):
            return stage(label,dict(call_id=label,output=out,usage={'input_tokens':2,'output_tokens':1},requested_model='synthetic-no-provider',requested_effort='synthetic',cost=values[index],visible_images_submitted=0,wait_ns=2))
        spec={'target':'Save','route':'cold','coarse_origin':'model_produced','provided_coarse':None,'cached_target':None,'local_repair_on':[],'repair_on':[],'session_id':'synthetic-aggregate-i16'}
        adapters={'observe_source':stage('observe_source',{}),'coarse_model':model('coarse_model',0,{'status':'candidate'}),'acquire_anchor':stage('acquire_anchor',{}),'anchor_model':model('anchor_model',1,{'status':'target_reference','target':target}),'final_revalidate':stage('final_revalidate',{'status':'revalidated'}),'execute':stage('execute',{'status':'completed'}),'verify_effect':stage('verify_effect',{'status':'succeeded'})}
        ids=iter(['a1','a2']);receipt=None;error=None
        try:receipt=run(spec,adapters,clock=lambda:0,id_factory=lambda:next(ids))
        except Exception as e:error={'type':type(e).__name__,'message':str(e)}
        strict_error=None
        if receipt is not None:
            try:json.dumps(receipt,allow_nan=False)
            except Exception as e:strict_error=type(e).__name__
        row={'case':name,'inputs':values,'receipt':receipt,'exception':error,'events':events,'strict_json_error':strict_error}
        with Path(os.environ.get('ROWS', os.devnull)).open('a',encoding='utf-8') as f:f.write(json.dumps(wire(row),ensure_ascii=True,sort_keys=True)+'\n')
        self.assertIsNone(error);self.assertEqual(receipt['outcome'],'TASK_SUCCEEDED');self.assertEqual(receipt['accounting']['attempted_calls'],2);self.assertEqual(receipt['accounting']['completed_calls'],2)
        if expected is None:self.assertIsNone(receipt['accounting']['cost'])
        else:self.assertEqual(receipt['accounting']['cost'],expected)
        self.assertIsNone(strict_error)
        if name.startswith("individual_"):self.assertIsNone(receipt["model_call_ledger"][0]["cost"])
for name in CASES:
    def test(self,name=name):self.check_case(name)
    setattr(Aggregate,'test_'+name,test)
if __name__=='__main__':unittest.main(verbosity=2)
