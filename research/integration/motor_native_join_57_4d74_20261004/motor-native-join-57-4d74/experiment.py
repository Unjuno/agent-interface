import json,pathlib,copy
from motor_state_v1.native_result import from_dispatch_result
root=pathlib.Path(__file__).resolve().parent
native=json.loads((root/'native_raw.json').read_text())['tasks'][-1]['receipt']
context=dict(state_id='saved-fixture-state',owner_id='saved-fixture-owner',owner_revision=0,observation_id='explicit-fixture-observation',surface_id='explicit-fixture-surface',coordinate_frame='window',commanded_pointer={})
failed=copy.deepcopy(native);failed['status']='release_unverified';failed['recovery_required']=True
for r in failed['execution']['releases']:r['verified']=False
rows=[]
for name,receipt,ctx in [('missing_context',native,{}),('saved_completed',native,context),('controlled_release_failure',failed,context)]:
    rows.append(dict(case=name,result=from_dispatch_result(receipt,context=ctx)))
print(json.dumps(dict(rows=rows,native_input_calls=0,scope='explicit context is fixture-provided, not independently verified current native identity'),indent=2))
