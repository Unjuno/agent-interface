import json,pathlib,hashlib
from saved_oracle import score_done
R=pathlib.Path('/data');O=pathlib.Path('/audit');P=json.loads((R/'PLAN.json').read_text());D=R/'runs/row1';r=json.loads((D/'raw.json').read_text());h=json.loads((D/'HOST_RECEIPT.json').read_text());errors=[];scores=[]
if r['source_hashes']!=P['source_hashes'] or r['errors'] or h['errors'] or h['exit_code']!=0:errors.append('source/infrastructure')
for p,v in P['source_hashes'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=v:errors.append('literal source '+p)
for task,expected in zip(r['tasks'],P['tasks']):
 score=score_done(D,task);errors.extend(score['errors']);scores.append(score)
 if (task['a'],task['b'])!=(expected['a'],expected['b']):errors.append('task input')
 ops=task['program']['ops'];ex=task['receipt']['execution']
 if ops[:3]!=[dict(op='focus',target='owned'),dict(op='key_chord',keys=['CTRL','Home']),dict(op='key_chord',keys=['Down'])] or any(o['op'].startswith('pointer') for o in ops):errors.append('standard keyboard route')
 if ex['completed_ops']!=list(range(len(ops))):errors.append('incomplete ops')
 if not ex.get('releases') or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in ex['releases']):errors.append('release verification')
if len(r['tasks'])!=6 or r.get('unattempted_tasks')!=[]:errors.append('incomplete sequence')
if r.get('relocation',{}).get('before')==r.get('relocation',{}).get('after'):errors.append('relocation missing')
if r['cleanup_physical']['keys'] or r['cleanup_physical']['buttons']:errors.append('cleanup input')
out=dict(allocation=P['allocation'],errors=errors,scores=scores,relocation=r.get('relocation'),cgroups=r['cgroups'],disposition='PASS_SCOPED_STANDARD_KEYBOARD_SEQUENCE' if not errors else 'HOLD_OR_FAIL',scope='Known Calc/historical source only; no causal efficiency, semantic invalidation, same-model comparison or global descendant certificate.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(errors=errors,disposition=out['disposition'],task_count=len(scores),relocation=r.get('relocation'),cgroups=r['cgroups'])));raise SystemExit(bool(errors))
