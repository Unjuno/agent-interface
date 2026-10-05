"""Post-run model-contract custody audit, no live action or provider calls."""
import json,hashlib,sys,collections
from pathlib import Path
root=Path(sys.argv[1]);source=Path(sys.argv[2]) if len(sys.argv)>2 else root/'source'
sys.path.insert(0,str(source));sys.path.insert(0,str(source/'research/live_control'));sys.path.insert(0,str(root))
from planner_contract_schema import compile_contract
out=root/'formal-output';errors=[];rows=[]
def require(ok,msg):
 if not ok:errors.append(msg)
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
models={thread:m for m in json.loads((out/'HOST_MODELS.json').read_text()) for thread in m['thread_ids']}
for file in sorted(out.glob('block-*/C/task-*.json')):
 row=json.loads(file.read_text());graph=row.get('graph')
 if not graph:
  rows.append({'file':str(file.relative_to(out)),'graph_present':False,'outcome':row['caller']['outcome']});continue
 target=row['caller']['selected_target'];thread=target['model_call_id'];provider=models.get(thread)
 require(provider is not None,'missing authored provider '+thread)
 if provider:
  authored=provider['output']['contract'];crop=provider['output']['value_crop']
  require(authored==graph['authored_contract']==target['grounding']['contract'],'authored contract mismatch '+str(file))
  require(canonical(authored)==graph['authored_contract_sha256'],'contract hash mismatch '+str(file))
  require(crop==graph['value_crop']==target['grounding']['value_crop'],'crop custody mismatch')
  expected=compile_contract(authored,target['aliases'],'surface-'+str(target['aliases']['field']))
  require(expected==graph['compiled_interface'],'model contract changed during compilation')
 interface=graph['compiled_interface'];receipt=graph['receipt'];transition_actions=receipt['transitions'] if 'transitions' in receipt else None
 events=graph['events'];selected=[x for x in events if x['event']=='branch_selected']
 operations=[]
 for event in selected:
  # Every branch selected must be a branch from the actual compiled model state.
  state=event.get('state');require(state in interface['method']['states'],'unknown selected state')
  branches=interface['method']['states'].get(state,{}).get('branches',[])
  matches=[b for b in branches if b['outcome']==event.get('outcome') and b['action']==event.get('action') and b['when']==event.get('matched_conditions')]
  require(len(matches)==1,'selected branch differs from authored graph')
  if event.get('action') in interface['actions']:operations.append(interface['actions'][event['action']]['operation'])
 require(receipt['interface_id']==interface['interface_id'] and receipt['method']==interface['method']['name'] and receipt['method_version']==interface['method']['version'],'receipt model-method mismatch')
 require(receipt['frontier_model_resumptions']==0,'model inside local graph')
 native={p['terminal']['id']:p for p in row['programs']}
 for transition in receipt['transitions']:
  action=interface['actions'][transition['action']]
  expected_label='compiled-enter' if action['operation']=='enter_token' else 'compiled-submit'
  actual=native.get(transition['action_id']);require(actual is not None and actual['label']==expected_label,'authored transition/native action mismatch')
  branches=interface['method']['states'][transition['from_state']]['branches']
  require(any(b['action']==transition['action'] and b['next_state']==transition['to_state'] and b['when']==transition['matched_conditions'] for b in branches),'transition changed planner state graph')
  require(any(o['normalized']['sequence']==transition['observation_sequence'] for o in graph['raw_observations']),'missing transition observation')
 task_id=row['task']['task_id'];history_path=file.parent/'client/runtime/submission-history.jsonl'
 history=[json.loads(s) for s in history_path.read_text().splitlines()] if history_path.exists() else []
 exact=[x for x in history if x['task_id']==task_id and x.get('exact') is True]
 rawprograms=[x['label'] for x in row['programs'] if x['label'].startswith('compiled-') and x['label']!='compiled-final-observation']
 rows.append({'file':str(file.relative_to(out)),'model_call_id':thread,'contract_digest':graph['authored_contract_sha256'],'interface_id':interface['interface_id'],'initial_state':interface['method']['initial_state'],'action_names':list(interface['actions']),'state_names':list(interface['method']['states']),'graph_outcome':receipt['outcome'],'graph_reason':receipt['reason'],'caller':row['caller']['outcome'],'native_compiled_programs':rawprograms,'independent_exact':len(exact),'model_crop':graph['value_crop']})
report={'scope':'post-run direct model output/contract/compiled graph/crop custody; no general compiler or authority proof','errors':errors,'rows':rows}
(root/'MODEL_CONTRACT_CUSTODY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
