from __future__ import annotations
import argparse,copy,hashlib,json
from pathlib import Path
SCHEDULE=[('p1-immediate','IMMEDIATE'),('p1-preroll','ONE_WINDOW_PREROLL'),('p2-preroll','ONE_WINDOW_PREROLL'),('p2-immediate','IMMEDIATE'),('p3-immediate','IMMEDIATE'),('p3-preroll','ONE_WINDOW_PREROLL'),('p4-preroll','ONE_WINDOW_PREROLL'),('p4-immediate','IMMEDIATE')]
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reconstruct(case_dir,arm,cid):
 rt=Path(case_dir)/'runtime';ev=rows(rt/'events.jsonl');ss=rows(rt/'scorer-samples.jsonl');launch=json.loads((Path(case_dir)/'launch.json').read_text())
 ds=[];us=[]
 for r in ev:
  if r.get('event')=='input_admission':
   m=r.get('physical_key_measurement');e=m.get('adapter_edge') if isinstance(m,dict) else None
   if isinstance(e,dict) and e.get('key')=='space':ds.append(copy.deepcopy(e))
  if r.get('event')=='input_release_transition' and r.get('key')=='space':
   m=r.get('physical_key_measurement');e=m.get('adapter_edge') if isinstance(m,dict) else None
   if isinstance(e,dict):us.append((copy.deepcopy(r),copy.deepcopy(e)))
 pos=[];prev=None;payloads=[]
 for w in ss:
  cur=w.get('payload')
  if not isinstance(cur,dict):continue
  payloads.append(cur)
  if prev is not None:
   if type(cur.get('kill_count')) is int and type(prev.get('kill_count')) is int and cur['kill_count']>prev['kill_count']:pos.append({'kind':'KILL_COUNT_INCREASE','observed_ns':cur['sample_ns'],'before':prev['kill_count'],'after':cur['kill_count'],'authority':False})
   if cur.get('map_exit') is True and prev.get('map_exit') is False:pos.append({'kind':'MAP_EXIT','observed_ns':cur['sample_ns'],'authority':False})
  prev=cur
 physical=None
 if len(ds)==1 and len(us)==1:
  rr,u=us[0];d=ds[0];lin=all(d.get(k)==u.get(k) for k in ('actuation_id','owner_id','intent_token','key')) and all(d.get(k)==rr.get(k) for k in ('owner_id','intent_token','key'));physical={'down':d,'up':u,'release':rr,'lineage_ok':lin,'confirmed':d.get('status')=='CONFIRMED_PHYSICAL_DOWN' and u.get('status')=='CONFIRMED_PHYSICAL_UP'}
 bound=[]
 if physical and physical['confirmed'] and physical['lineage_ok']:
  hi=physical['down']['interval'][1]
  for e in pos:
   if type(e.get('observed_ns')) is int and e['observed_ns']>=hi:bound.append({**e,'plan_id':cid,'actuation_id':physical['down']['actuation_id'],'scorer_authority':False})
 hi=physical['down']['interval'][1] if physical else None;pre=[s for s in payloads if type(s.get('sample_ns')) is int and type(hi) is int and s['sample_ns']<hi]
 score=json.loads((rt/'score.json').read_text()) if (rt/'score.json').exists() else None
 return {'arm':arm,'pre_roll_ms':launch.get('pre_roll_ms'),'case_id':cid,'seed':launch.get('seed'),'physical_down_count':len(ds),'physical_up_count':len(us),'physical':physical,'positive_events':pos,'bound_task_effects':bound,'scorer_samples':len(ss),'scorer_baseline':payloads[0] if payloads else None,'scorer_pre_attack_last':pre[-1] if pre else (payloads[0] if payloads else None),'score':score,'markers':launch.get('markers',{}),'runtime_sources_sha256':sha(rt/'sources.json')}
def integrity(rs):
 e=[]
 if len(rs)!=8:return ['denominator']
 seen=set()
 for r in rs:
  cid=r.get('case_id');arm=r.get('arm');want=0 if arm=='IMMEDIATE' else 600 if arm=='ONE_WINDOW_PREROLL' else None
  if cid in seen:e.append('duplicate_case:'+str(cid))
  seen.add(cid)
  if r.get('pre_roll_ms')!=want:e.append('wrong_arm_delay:'+str(cid))
  if r.get('seed')!=992600:e.append('wrong_seed:'+str(cid))
  p=r.get('physical')
  if r.get('physical_down_count')!=1 or r.get('physical_up_count')!=1 or not isinstance(p,dict):e.append('physical_count:'+str(cid));continue
  if p.get('confirmed') is not True or p.get('lineage_ok') is not True:e.append('physical_lineage:'+str(cid))
  rr=p.get('release',{})
  if rr.get('owner_transition_verified') is not True or rr.get('owned_keycodes_after_batch')!=[]:e.append('release_neutral:'+str(cid))
  d=p.get('down',{});u=p.get('up',{})
  if d.get('actuation_id')!=u.get('actuation_id'):e.append('actuation_pair:'+str(cid))
  for x in r.get('positive_events',[]):
   if x.get('authority') is not False:e.append('scorer_authority:'+str(cid))
   if x.get('kind') not in ('KILL_COUNT_INCREASE','MAP_EXIT'):e.append('weak_effect:'+str(cid))
  bes=r.get('bound_task_effects',[])
  if len(bes)>1:e.append('duplicate_effect:'+str(cid))
  for x in bes:
   if x.get('plan_id')!=cid:e.append('wrong_plan:'+str(cid))
   if x.get('actuation_id')!=d.get('actuation_id'):e.append('wrong_actuation:'+str(cid))
   if x.get('scorer_authority') is not False:e.append('bound_authority:'+str(cid))
   iv=d.get('interval');
   if not isinstance(iv,list) or len(iv)!=2 or type(x.get('observed_ns')) is not int or x['observed_ns']<iv[1]:e.append('pre_down_effect:'+str(cid))
 return e
def derive_decision(rs):
 if integrity(rs):return 'FAIL_EVIDENCE_INTEGRITY'
 diff=0
 for n in range(1,5):
  a=next(r for r in rs if r['case_id']==f'p{n}-immediate');b=next(r for r in rs if r['case_id']==f'p{n}-preroll');diff+=bool(a['bound_task_effects'])!=bool(b['bound_task_effects'])
 return 'PASS_ATTACK_ONSET_PHASE_DISCRIMINATES_SCOPED' if diff>=3 else 'HOLD_ATTACK_ONSET_PHASE_NOT_DISCRIMINATING'
def audit(root):
 root=Path(root);saved=json.loads((root/'FORMAL_RESULT.json').read_text());rs=[reconstruct(root/cid,arm,cid) for cid,arm in SCHEDULE];errs=[]
 if rs!=saved.get('rows'):errs.append('candidate_auditor_row_mismatch')
 errs.extend('raw:'+x for x in integrity(rs))
 dec=derive_decision(rs)
 if dec!=saved.get('decision'):errs.append('decision')
 if saved.get('formal_invocations')!=1 or any(saved.get(k)!=0 for k in ('reruns','replacements','tuning_after_freeze')):errs.append('budget')
 controls={}
 def reject(name,fn):m=copy.deepcopy(rs);fn(m);controls[name]=bool(integrity(m))
 ai=0
 def effect(m):
  r=m[ai];p=r['physical'];r['bound_task_effects']=[{'kind':'KILL_COUNT_INCREASE','observed_ns':p['down']['interval'][1]+1,'plan_id':r['case_id'],'actuation_id':p['down']['actuation_id'],'scorer_authority':False}]
 reject('wrong_arm_delay',lambda m:m[0].__setitem__('pre_roll_ms',600))
 reject('wrong_seed',lambda m:m[0].__setitem__('seed',1))
 def wrong_act(m):effect(m);m[0]['bound_task_effects'][0]['actuation_id']='wrong'
 reject('wrong_actuation',wrong_act)
 def auth(m):effect(m);m[0]['bound_task_effects'][0]['scorer_authority']=True
 reject('scorer_authority',auth)
 def pred(m):effect(m);m[0]['bound_task_effects'][0]['observed_ns']=0
 reject('pre_down_effect',pred)
 reject('missing_physical_edge',lambda m:m[0].__setitem__('physical_down_count',0))
 def dup(m):effect(m);m[0]['bound_task_effects'].append(copy.deepcopy(m[0]['bound_task_effects'][0]))
 reject('duplicate_effect',dup)
 reject('cross_session_lineage',lambda m:m[0]['physical'].__setitem__('lineage_ok',False))
 if not all(controls.values()):errs.append('mutation_control')
 return {'schema':'map01-attack-onset-phase-audit-v1','decision':dec,'errors':errs,'pass':not errs,'rows':len(rs),'controls':controls}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--formal',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=audit(a.formal);a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
