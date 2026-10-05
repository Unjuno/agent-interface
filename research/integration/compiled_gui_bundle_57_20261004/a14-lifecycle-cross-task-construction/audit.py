import hashlib,importlib,importlib.util,json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent; ROOT=HERE.parents[3]
MAN=json.loads((HERE/'manifest.json').read_text()); PKG=ROOT/'research/integration/planner_contract_56_4d74_20261004'; BASE=PKG/'r02/formal-output'; CAND=ROOT/'research/integration/compiled_gui_bundle_57_20261004/a12-predicate-lifecycle-guard/candidate.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok: raise ValueError(msg)
need(sha(HERE/'PLAN.md')==MAN['pins']['plan_sha256'],'plan pin mismatch')
need(sha(ROOT/'research/integration/compiled_gui_bundle_57_20261004/a13-predicate-lifecycle-prompt-check/PROMPT.txt')==MAN['pins']['template_prompt_sha256'],'template prompt pin mismatch')
need(sha(ROOT/'research/integration/compiled_gui_bundle_57_20261004/a13-predicate-lifecycle-prompt-check/schema.json')==MAN['pins']['schema_sha256'],'schema pin mismatch')
need(sha(CAND)==MAN['pins']['candidate_sha256'],'candidate pin mismatch')
need(len(MAN['tasks'])==5,'manifest must contain tasks 2-6')
sys.path.insert(0,str(PKG/'r02')); sys.path.insert(0,str(PKG/'source/research/live_control'))
baseline=importlib.import_module('planner_contract_schema')
spec=importlib.util.spec_from_file_location('candidate',CAND); candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
def verify_task(t,ans):
 idx=t['task_index']; d=HERE/f'task-{idx}'; rowp=ROOT/t['row_path']; imgp=ROOT/t['image_path']
 need(sha(rowp)==t['row_sha256'] and sha(imgp)==t['image_sha256'],f'task {idx} source hash mismatch')
 row=json.loads(rowp.read_text()); selected=row['caller']['selected_target']
 need(row['task']['task_id']==f'task-{idx}' and row['task']['token']==t['token'],f'task {idx} manifest token/id mismatch')
 need(selected['aliases']==t['aliases'] and selected['model_call_id']==t['call_id'],f'task {idx} manifest aliases/call mismatch')
 need(pathlib.Path(row['source']['image']).name==imgp.name,f'task {idx} manifest image mapping mismatch')
 need(sha(d/'PROMPT.txt')==t['prompt_sha256'] and sha(d/'schema.json')==t['schema_sha256'],f'task {idx} prompt/schema hash mismatch')
 prompt=(d/'PROMPT.txt').read_text(); need(t['token'] in prompt,f'task {idx} authorized token absent from prompt')
 need(struct.unpack('>II',imgp.read_bytes()[16:24])==(1280,800),f'task {idx} image dimension mismatch')
 raw=json.loads((d/'RAW.json').read_text()); need(raw.get('provider_attempts')==1,f'task {idx} must have exactly one provider attempt')
 need(raw.get('exit_code')==0 and raw.get('timed_out') is False,f'task {idx} call did not finish successfully')
 need(raw.get('answer_sha256')==sha(d/'answer.json'),f'task {idx} answer hash mismatch')
 need(raw.get('answer')==ans,f'task {idx} raw/answer mismatch')
 for k,path in [('prompt_sha256',d/'PROMPT.txt'),('schema_sha256',d/'schema.json'),('task_row_sha256',rowp),('image_sha256',imgp),('argv_sha256',d/'argv.json'),('stdout_sha256',d/'stdout.jsonl'),('stderr_sha256',d/'stderr.txt')]: need(raw.get(k)==sha(path),f'task {idx} raw {k} mismatch')
 need(raw.get('requested_model')==MAN['model'] and raw.get('requested_effort')==MAN['effort'],f'task {idx} model mismatch')
 need(set(ans)=={'field_point','submit_point','contract','value_crop'},f'task {idx} output shape mismatch')
 for k in ('field_point','submit_point'):
  p=ans[k]; need(type(p) is list and len(p)==2 and all(type(v) is int for v in p),f'task {idx} malformed {k}')
  need(0<=p[0]<1280 and 0<=p[1]<800,f'task {idx} {k} outside image')
 crop=ans['value_crop']; need(type(crop) is list and len(crop)==4 and all(type(v) is int for v in crop),f'task {idx} malformed crop')
 x1,y1,x2,y2=crop; need(0<=x1<x2<=1280 and 0<=y1<y2<=800,f'task {idx} crop outside image')
 c=ans['contract']; acts=c['actions']; need(len(acts)==2 and {a['operation'] for a in acts}=={'enter_token','submit_form'},f'task {idx} operations mismatch')
 need(all(all(e['predicate']!='target_valid' for e in a['expected_effect']) for a in acts),f'task {idx} target_valid leaks into postcondition')
 need(any(e['predicate']=='exact_token_visible' and e['value'] is True for a in acts if a['operation']=='enter_token' for e in a['expected_effect']),f'task {idx} exact entry effect missing')
 need(any(e['predicate']=='exact_saved_title' and e['value'] is True for a in acts if a['operation']=='submit_form' for e in a['expected_effect']),f'task {idx} exact save effect missing')
 states=c['method']['states']; branches=[b for s in states for b in s['branches']]
 ab=[b for b in branches if b['outcome']=='action']; need(len(ab)==2 and all(any(q['predicate']=='target_valid' and q['value'] is True for q in b['when']) for b in ab),f'task {idx} action guards missing')
 sb=[b for b in ab if next(a for a in acts if a['name']==b['action'])['operation']=='submit_form']; need(len(sb)==1 and any(q['predicate']=='exact_token_visible' and q['value'] is True for q in sb[0]['when']),f'task {idx} submit branch token guard missing')
 need(any(b['outcome']=='complete' and any(q['predicate']=='exact_saved_title' and q['value'] is True for q in b['when']) for b in branches),f'task {idx} completion gate missing')
 compiled=candidate.compile_contract_v2(c,t['aliases'],f'a14-task-{idx}-construction',compile_contract=baseline.compile_contract)
 need(len(compiled['actions'])==2,f'task {idx} candidate compile action count')
 # Targeted mutation tests verify that the independent gate rejects lifecycle leakage.
 forged=json.loads(json.dumps(c)); ent=next(a for a in forged['actions'] if a['operation']=='enter_token'); ent['expected_effect'].append({'predicate':'target_valid','value':True})
 try: candidate.compile_contract_v2(forged,t['aliases'],f'a14-task-{idx}-negative',compile_contract=baseline.compile_contract)
 except ValueError: pass
 else: raise ValueError(f'task {idx} corrupted transient postcondition was accepted')
 return {'task_index':idx,'accepted':True,'action_branches':len(ab),'target_valid_postconditions':0,'field_point':ans['field_point'],'submit_point':ans['submit_point'],'value_crop':crop,'answer_sha256':raw['answer_sha256'],'raw_sha256':sha(d/'RAW.json')}
results=[]
for t in MAN['tasks']:
 d=HERE/f"task-{t['task_index']}"; results.append(verify_task(t,json.loads((d/'answer.json').read_text())))
report={'pass':len(results)==5,'tasks':results,'corruption_controls':'each row independently rejects target_valid added to an action postcondition','formal_allocation_or_gui':False,'efficiency_claim':False,'limitations':['five model-only samples from one retained synthetic form family','screenshots and tokens are existing R02 data','no actual GUI input, effect scorer, or live observer validation','no prompt robustness estimate outside these five calls']}
need(report['pass'],'not all five rows passed')
(HERE/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,indent=2))
