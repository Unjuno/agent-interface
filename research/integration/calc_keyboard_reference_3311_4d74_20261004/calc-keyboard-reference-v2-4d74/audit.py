import json,pathlib,hashlib
from saved_oracle import score_done
R=pathlib.Path('/data');O=pathlib.Path('/audit');P=json.loads((R/'PLAN.json').read_text());rows=[];errors=[];counts={'direct':0,'keyboard':0}
for spec in P['rows']:
 D=R/'runs'/('row'+str(spec['index']+1));r=json.loads((D/'raw.json').read_text());h=json.loads((D/'HOST_RECEIPT.json').read_text());bad=[];scores=[]
 if r['source_hashes']!=P['source_hashes'] or r['spec']!=spec or r['errors'] or h['errors'] or h['exit_code']!=0:bad.append('identity or infrastructure')
 if [t['label'] for t in r['tasks']]!=['prime','trial']:bad.append('program count')
 for task in r['tasks']:
  score=score_done(D,task);bad.extend(x for x in score['errors'] if x!='saved effect or collateral cell content');scores.append({'label':task['label'],'score':score,'dispatch_ns':task['end_ns']-task['start_ns']})
  execution=task['receipt']['execution'];rel=execution.get('releases',[])
  if not rel or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in rel):bad.append('release')
  if execution['completed_ops']!=list(range(len(task['program']['ops']))):bad.append('operations')
  if task['label']=='trial':
   ops=task['program']['ops'];keyprefix=[{'op':'focus','target':'owned'},{'op':'key_chord','keys':['CTRL','Home']},{'op':'key_chord','keys':['Down']}]
   if spec['route']=='keyboard' and ops[:3]!=keyprefix:bad.append('keyboard prefix')
   if spec['route']=='direct' and [x['op'] for x in ops[:4]]!=['focus','pointer_move','pointer_button','pointer_button']:bad.append('direct prefix')
   if (task['a'],task['b'])!=(31,37):bad.append('task inputs')
 if not scores[0]['score']['effect']['pass_effect']:bad.append('prime effect')
 if r['cleanup_physical']['keys'] or r['cleanup_physical']['buttons']:bad.append('cleanup')
 counts[spec['route']]+=int(scores[-1]['score']['effect']['pass_effect']);rows.append({'index':spec['index'],'route':spec['route'],'scores':scores,'errors':bad});errors.extend(bad)
out={'allocation':P['allocation'],'disposition':'PASS_SCOPED_KEYBOARD_REFERENCE; HOLD_FULL_COMPARISON' if counts=={'direct':2,'keyboard':2} and not errors else 'HOLD_INCOMPLETE_OR_TASK_FAILURE','counts':counts,'rows':rows,'errors':errors,'scope':'Known Calc-specific task and frozen historical X11 closure; no model/economic/generalGUI qualification. Original HOME STOP unchanged. Parent cleanup not all-descendant certificate.'}
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
