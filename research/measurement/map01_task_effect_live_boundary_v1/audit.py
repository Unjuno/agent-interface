import argparse, hashlib, json, pathlib, sys
S=['PRESS_EFFECT','RELEASE_EFFECT','STATE_ONLY','BACKGROUND_EFFECT']
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(root,reps=3):
 root=pathlib.Path(root); errors=[]; rows=json.load(open(root/'RAW.json')); man=json.load(open(root/'MANIFEST.json'))
 expected={f'{s.lower()}-r{r}' for r in range(reps) for s in S}; ids=[x['case_id'] for x in rows]
 if len(rows)!=(4*reps) or set(ids)!=expected or len(ids)!=len(set(ids)): errors.append('denominator')
 actual={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
 if man.get('files')!=actual or man.get('count')!=len(actual): errors.append('manifest')
 for x in rows:
  cid=x['case_id']; c=root/cid; ev=[json.loads(z) for z in open(c/'app.jsonl') if z.strip()]; score=json.load(open(c/'score.json'))
  if x['app_exit']!=0 or x['xvfb_exit'] not in (0,-15): errors.append(cid+':exit')
  if not x['down_seen'] or x['up_seen_after_release'] or x['final_down']: errors.append(cid+':key_state')
  if not (x['down_emit_ns']<=x['down_ack_ns']<=x['up_emit_ns']<=x['up_ack_ns']): errors.append(cid+':controller_order')
  if score.get('authority')!='none' or score.get('scorer')!='raw-app-journal-v1' or score.get('plan_id')!=x['plan_id'] or score.get('actuation_id')!=x['actuation_id']: errors.append(cid+':score_identity')
  te=[e for e in ev if e.get('kind')=='task_effect']
  bg=[e for e in ev if e.get('kind')=='background_effect']
  if x['schedule'] in ('PRESS_EFFECT','RELEASE_EFFECT'):
   if len(te)!=1 or score.get('disposition')!='TASK_EFFECT' or not score.get('scored'): errors.append(cid+':task_effect')
   else:
    if score.get('t_ns')!=te[0].get('t_ns') or score['t_ns']<x['down_emit_ns']: errors.append(cid+':task_time')
    want='key_press' if x['schedule']=='PRESS_EFFECT' else 'key_release'
    if score.get('source')!=want or te[0].get('source')!=want: errors.append(cid+':source')
  else:
   if te or score.get('disposition')!='UNRESOLVED_NO_TASK_EFFECT' or score.get('scored'): errors.append(cid+':unresolved')
   if x['schedule']=='BACKGROUND_EFFECT' and len(bg)!=1: errors.append(cid+':background')
 return {'decision':'PASS_PLAN_BOUND_TASK_EFFECT_LIVE_BOUNDARY_SCOPED' if not errors else 'FAIL_AUDIT','cases':len(rows),'errors':errors}
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); ap.add_argument('--expected-reps',type=int,default=3); a=ap.parse_args(); r=audit(a.root,a.expected_reps)
 if a.out: json.dump(r,open(a.out,'w'),sort_keys=True,indent=2)
 print(json.dumps(r,sort_keys=True)); raise SystemExit(0 if not r['errors'] else 1)
