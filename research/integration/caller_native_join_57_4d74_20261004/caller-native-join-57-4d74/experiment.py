"""Saved native receipt→full pending caller qualification, zero native execution."""
import pathlib,json,hashlib,copy
import adaptive_acquisition_caller_v3 as caller
root=pathlib.Path(__file__).resolve().parent
raw=json.loads((root/'native_raw.json').read_text(encoding='utf8'))
receipt=raw['tasks'][-1]['receipt'];rows=[]
for name,value in [('full_native_receipt',receipt),('status_projection',{'status':receipt['status']})]:
    events=[];calls=[]
    def execute(payload):calls.append('saved_execute_callback');return copy.deepcopy(value)
    def verify(payload):calls.append('saved_verify_callback');return {'status':'unavailable'}
    adapters=dict(reuse_revalidate=lambda p:{'status':'revalidated'},final_revalidate=lambda p:{'status':'revalidated'},execute=execute,verify_effect=verify,journal=lambda e:events.append(e))
    result=caller.run(raw['caller_spec'],adapters)
    rows.append(dict(case=name,input_sha256=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest(),result=result,callbacks=calls,events=events))
print(json.dumps(dict(rows=rows,native_input_calls=0,model_calls=0,scope='saved data through unchanged pending caller; callbacks not native actor replay'),indent=2))
