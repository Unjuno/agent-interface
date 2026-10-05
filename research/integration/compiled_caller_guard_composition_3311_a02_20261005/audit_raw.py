import json
from pathlib import Path
raw=json.loads((Path(__file__).parent/'runs/a02/raw.json').read_text())
assert raw['experiment_id']=='compiled-caller-guard-3311-20261005-a02'
assert raw['actual_os_inputs']==0 and raw['model_requests']==0
v1,v2=raw['results']
assert v1['runtime']['outcome']=='TASK_SUCCEEDED'
assert v1['simulated_ops']==['enter_exact_token','activate_submit']
assert v1['outer']['outcome']=='TASK_NOT_VERIFIED'
assert v1['outer']['task_effect']=='failed' and v1['outer']['delivery']=='confirmed'
assert v1['scorer_calls']==['independent_effect_check']
assert v2['runtime']['outcome']=='SAFE_YIELD'
assert v2['simulated_ops']==['enter_exact_token']
assert v2['outer']['outcome']=='EXECUTION_INCOMPLETE'
assert v2['outer']['reason']=='effect_failed'
assert v2['outer']['delivery']=='confirmed_partial'
assert v2['outer']['execution_progress']['completed_actions']==1
assert v2['scorer_calls']==[]
for x,n in ((v1,2),(v2,1)):
    terminals=[e for e in x['runtime']['critical_events'] if e.get('event')=='action_terminal']
    assert len(terminals)==n and all(e.get('release_verified') is True for e in terminals)
    assert x['outer']['accounting']['attempted_calls']==0
print(json.dumps({'audit':'PASS_COMPOSED_RECEIPT_RECONSTRUCTION','experiment_id':raw['experiment_id'],'v1':{'inner':v1['runtime']['outcome'],'outer':v1['outer']['outcome'],'effect':v1['outer']['task_effect'],'operations':v1['simulated_ops']},'v2':{'inner':v2['runtime']['outcome'],'outer':v2['outer']['outcome'],'reason':v2['outer']['reason'],'delivery':v2['outer']['delivery'],'completed_actions':v2['outer']['execution_progress']['completed_actions'],'operations':v2['simulated_ops']},'os_inputs':0,'model_requests':0},sort_keys=True,indent=2))
