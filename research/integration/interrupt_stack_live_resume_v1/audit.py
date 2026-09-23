#!/usr/bin/env python3
import argparse, hashlib, json, pathlib
POLICIES=['POP_ONLY','EVIDENCE_BOUND_RESUME']; SCENARIOS=['NORMAL','TARGET_REPLACED','QUEUE_CHANGED','SOURCE_STALE','PENDING_UNKNOWN','TASK_CANCELED']
EXPECTED_CAND={'NORMAL':'RESUME','TARGET_REPLACED':'REVALIDATE_TARGET','QUEUE_CHANGED':'REPLAN_QUEUE','SOURCE_STALE':'YIELD_STALE','PENDING_UNKNOWN':'RECONCILE_RESULT','TASK_CANCELED':'CANCELED'}
SOURCE_NAMES=['app.py','run.py','audit.py','controls.py']
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(root,reps,freeze_path=None):
 root=pathlib.Path(root); rows=[]; errors=[]
 if freeze_path:
   freeze=json.loads(pathlib.Path(freeze_path).read_text())
   for name,expected in freeze['source_sha256'].items():
     if not pathlib.Path(name).exists() or sha(name)!=expected: errors.append('source_hash:'+name)
 for rep in reps:
   p=root/f'batch-{rep}'/'ROWS.json'
   if not p.exists(): errors.append(f'missing_batch:{rep}'); continue
   batch=json.loads(p.read_text())
   if len(batch)!=12: errors.append(f'batch_count:{rep}:{len(batch)}')
   rows+=batch
 exp=len(reps)*12
 if len(rows)!=exp: errors.append(f'row_count:{len(rows)}!={exp}')
 ids=set(); expected_ids={f'r{rep}-{p}-{s}' for rep in reps for s in SCENARIOS for p in POLICIES}
 for r in rows:
   cid=r.get('case_id')
   if cid in ids: errors.append('duplicate:'+str(cid))
   ids.add(cid)
   if type(r.get('rep')) is not int: errors.append('rep_type:'+str(cid)); continue
   if cid != f"r{r['rep']}-{r['policy']}-{r['scenario']}": errors.append('case_identity:'+str(cid))
   if r['rep'] not in reps: errors.append('rep_scope:'+str(cid))
   if r['policy'] not in POLICIES or r['scenario'] not in SCENARIOS: errors.append('enum:'+str(cid)); continue
   if r['app_exit']!=0 or r['xvfb_exit']!=0: errors.append('exit:'+cid)
   if not r['neutral_a'] or not r['neutral_b']: errors.append('neutral:'+cid)
   if r['saved']['interrupt_resolved'] is not False or r['current']['interrupt_resolved'] is not True: errors.append('interrupt:'+cid)
   if r['saved']['task_active'] is not True or r['saved']['source_fresh'] is not True or r['saved']['pending_result']!='NONE': errors.append('saved_frame:'+cid)
   for n in SOURCE_NAMES:
     if r.get('source_hashes',{}).get(n)!=sha(n): errors.append('row_source_hash:'+cid+':'+n)
   sc=r['scenario']
   if sc=='TARGET_REPLACED' and r['current']['target_id']==r['saved']['target_id']: errors.append('target_not_changed:'+cid)
   if sc=='QUEUE_CHANGED' and r['current']['queue_version']==r['saved']['queue_version']: errors.append('queue_not_changed:'+cid)
   if sc=='SOURCE_STALE' and (r['current']['source_fresh'] is not False or r['current']['source_epoch']==r['saved']['source_epoch']): errors.append('source_not_stale:'+cid)
   if sc=='PENDING_UNKNOWN' and r['current']['pending_result']!='UNKNOWN': errors.append('pending_not_unknown:'+cid)
   if sc=='TASK_CANCELED' and r['current']['task_active'] is not False: errors.append('task_not_canceled:'+cid)
   if sc=='NORMAL':
     if r['current']['target_id']!=r['saved']['target_id'] or r['current']['queue_version']!=r['saved']['queue_version'] or r['current']['source_epoch']!=r['saved']['source_epoch'] or r['current']['pending_result']!='NONE': errors.append('normal_changed:'+cid)
   if r['policy']=='EVIDENCE_BOUND_RESUME':
      if r['decision']!=EXPECTED_CAND[sc]: errors.append('candidate_decision:'+cid)
      if sc=='NORMAL':
         if not r['suffix_sent'] or not r['task_success']: errors.append('candidate_normal:'+cid)
      else:
         if r['suffix_sent'] or r['unsafe_resume']: errors.append('candidate_unsafe:'+cid)
   else:
      exp_dec='CANCELED' if sc=='TASK_CANCELED' else 'RESUME'
      if r['decision']!=exp_dec: errors.append('pop_decision:'+cid)
      if sc=='NORMAL' and not r['task_success']: errors.append('pop_normal:'+cid)
      if sc in ('TARGET_REPLACED','QUEUE_CHANGED','SOURCE_STALE','PENDING_UNKNOWN') and not r['unsafe_resume']: errors.append('pop_expected_unsafe:'+cid)
      if sc=='TASK_CANCELED' and r['suffix_sent']: errors.append('pop_cancel_input:'+cid)
   if sc=='TARGET_REPLACED' and r['policy']=='POP_ONLY' and r['final']['a']!='b': errors.append('target_wrong_effect_missing:'+cid)
 if ids!=expected_ids: errors.append('id_set')
 return {'decision':'PASS_INTERRUPT_STACK_LIVE_RESUME_SCOPED' if not errors else 'FAIL_OR_HOLD','rows':len(rows),'errors':errors,
   'candidate_unsafe_resumes':sum(1 for r in rows if r.get('policy')=='EVIDENCE_BOUND_RESUME' and r.get('unsafe_resume')),
   'pop_unsafe_resumes':sum(1 for r in rows if r.get('policy')=='POP_ONLY' and r.get('unsafe_resume'))}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--reps',nargs='+',type=int,required=True); ap.add_argument('--freeze'); ap.add_argument('--out'); a=ap.parse_args(); res=audit(a.root,a.reps,a.freeze); txt=json.dumps(res,indent=2,sort_keys=True)+'\n';
 if a.out:pathlib.Path(a.out).write_text(txt)
 print(txt,end=''); raise SystemExit(0 if not res['errors'] else 1)
if __name__=='__main__': main()
