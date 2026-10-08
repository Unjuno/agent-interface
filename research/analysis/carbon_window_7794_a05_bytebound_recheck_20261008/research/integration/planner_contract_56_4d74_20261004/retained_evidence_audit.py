"""Post-run retained-evidence audit; never changes frozen allocations or old grades."""
import json,hashlib,sys,collections
from pathlib import Path
root=Path(sys.argv[1]);out=root/'formal-output';read=lambda p:json.loads(p.read_text());errors=[]
def require(value,msg):
 if not value:errors.append(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read(root/'FREEZE.json')
for name,digest in freeze['files'].items():require(sha(root/name)==digest,'changed frozen '+name)
for name,digest in read(root/'SOURCE.json')['members'].items():require(sha((Path(sys.argv[2]) if len(sys.argv)>2 else root/'source')/name)==digest,'changed source '+name)
host=read(out/'HOST.json');models=read(out/'HOST_MODELS.json');plan=read(root/'PROTOCOL.json');usage=collections.Counter();threads=set();model_by_thread={};requests=sorted((out/'requests').glob('*.request.json'))
require(host['model_calls']==len(models)==len(requests),'provider count mismatch')
for request,m in zip(requests,models):
 q=read(request);response=read(request.with_suffix('.response.json'));require(response==m,'provider response mismatch '+request.name)
 require(m['requested_model']==plan['model'] and m['requested_effort']==plan['effort'],'model config mismatch')
 require(not m['tool_items'] and not m['parse_errors'],'unexpected provider tools/parse errors')
 for thread in m['thread_ids']:
  require(thread not in threads,'reused model context');threads.add(thread);model_by_thread[thread]=m
 if q['image_relative']:
  require(sha(out/q['image_relative'])==q['image_sha256']==m['image_sha256'],'image digest mismatch')
 require(sha(out/'model-calls'/q['call_id']/'schema.json')==m['schema_sha256'],'schema digest mismatch')
 u=m.get('usage')
 require(isinstance(u,dict),'missing provider usage')
 if u:
  require(u['cached_input_tokens']<=u['input_tokens'] and u['reasoning_output_tokens']<=u['output_tokens'],'invalid usage subsets');usage.update(u)
 require(m['visible_images_submitted']==(1 if q['image_relative'] else 0),'image count mismatch')
summary=[];full=True;all_correct=True;used=set();native_released=True
for bi,block in enumerate(plan['blocks'],1):
 for arm in block['order']:
  path=out/f'block-{bi}'/arm;files=sorted(path.glob('task-*.json'));rows=[read(p) for p in files];evaluation=read(path/'independent-evaluation.json') if (path/'independent-evaluation.json').exists() else None
  history_path=path/'client/runtime/submission-history.jsonl';history=[json.loads(s) for s in history_path.read_text().splitlines()] if history_path.exists() else []
  counts=collections.Counter(x['task_id'] for x in history if x.get('exact') is True);task_report=[]
  if evaluation:
   require(evaluation['record_count']==len(history),'history count mismatch')
   require(all(evaluation['exact_counts'][f'task-{n}']==counts[f'task-{n}'] for n in range(1,7)),'independent exact counts mismatch')
   expected_ids={f'task-{n}' for n in range(1,7)};unknown=[x for x in history if x['task_id'] not in expected_ids];duplicates={k:v for k,v in counts.items() if v>1};missing=[k for k in sorted(expected_ids) if counts[k]==0]
   require(evaluation['success']==(len(history)==6 and not unknown and not duplicates and not missing and all(x.get('exact') is True for x in history)),'independent success mismatch')
  for row in rows:
   task=row['task'];require(task['token']==f"t{block['seed']}-{task['task_id'].split('-')[-1]}",'task seed mismatch')
   for h in history:
    if h['task_id']==task['task_id']:require(h['expected_token']==task['token'] and h['layout']==task['layout'],'task oracle mismatch')
   ledger=row['caller'].get('model_call_ledger',[])
   for entry in ledger:
    thread=entry.get('call_id');require(thread in model_by_thread,'unjoined caller provider '+str(thread));require(thread not in used,'provider charged to multiple tasks');used.add(thread)
    if thread in model_by_thread:
     provider=model_by_thread[thread]
     require(entry.get('usage')==provider.get('usage') and entry.get('wait_ns')==provider.get('wait_ns') and entry.get('visible_images_submitted')==provider.get('visible_images_submitted'),'caller provider cost mismatch')
   for program in row['programs']:
    release=program['terminal'].get('release',{});ok=release.get('verified') is True and release.get('keys_down')==[] and release.get('buttons_down')==[];native_released=native_released and ok;require(ok,'native release unverified')
   task_report.append({'task':task['task_id'],'caller':row['caller']['outcome'],'repair_path':row['caller'].get('repair_path'),'exact_submissions':counts[task['task_id']],'models':len(ledger),'durable_calls':row['durable_calls'],'elapsed_ns':row['elapsed_ns'],'model_wait_ns':sum(e.get('wait_ns') or 0 for e in ledger),'usage':dict(sum((collections.Counter(e.get('usage') or {}) for e in ledger),collections.Counter())),'native_programs':len(row['programs']),'local_observation_records':sum(len(p['observations']) for p in row['programs']),'ocr_calls':len((row['graph'] or {}).get('raw_observations',[])),'ocr_ns':sum(o['ocr']['elapsed_ns'] for o in (row['graph'] or {}).get('raw_observations',[])),'graph_outcome':row['graph']['receipt']['outcome'] if row['graph'] else None})
  full=full and len(rows)==6 and evaluation is not None;all_correct=all_correct and evaluation is not None and evaluation['success'] is True
  summary.append({'block':bi,'arm':arm,'saved_tasks':len(rows),'independent':evaluation,'tasks':task_report,'totals':{'task_elapsed_ns':sum(t['elapsed_ns'] for t in task_report),'task_model_wait_ns':sum(t['model_wait_ns'] for t in task_report),'task_models':sum(t['models'] for t in task_report),'task_usage':dict(sum((collections.Counter(t['usage']) for t in task_report),collections.Counter())),'durable_calls':sum(t['durable_calls'] for t in task_report),'native_programs':sum(t['native_programs'] for t in task_report),'local_observation_records':sum(t['local_observation_records'] for t in task_report),'ocr_calls':sum(t['ocr_calls'] for t in task_report),'ocr_ns':sum(t['ocr_ns'] for t in task_report)}})
preflight=[]
# Image-free endpoint calls remain attributable even when semantic validation raised before dump.
for qpath in requests:
 q=read(qpath)
 if q['image_relative'] is None:preflight.extend(read(qpath.with_suffix('.response.json'))['thread_ids'])
for p in out.glob('block-*/*/schema-preflight.json'):
 m=read(p);require(set(m['thread_ids']).issubset(set(preflight)),'saved preflight not in endpoint attempts')
require(set(preflight).isdisjoint(used),'preflight counted as task')
require(used|set(preflight)==threads,'unattributed provider attempts')
report={'audit_scope':'post-run frozen identity/provider task joins/independent HTTP scoring/native release; not full authority proof or preregistered auditor','audit_errors':errors,'host':host,'all_attempt_usage':dict(usage),'full_48_tasks_retained':full,'all_arms_independent_exact':all_correct,'native_releases_verified':native_released,'scientific_efficiency_gate':False,'efficiency_gate_reason':'human setup cost unavailable; complete task correctness and broader coverage required','arms':summary}
(root/'RETAINED_EVIDENCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'errors':errors,'full':full,'all_correct':all_correct,'usage':dict(usage),'saved_task_counts':[(x['block'],x['arm'],x['saved_tasks']) for x in summary]},indent=2));raise SystemExit(bool(errors))
