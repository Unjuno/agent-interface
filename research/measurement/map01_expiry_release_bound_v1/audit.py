from __future__ import annotations
import copy,json,sys
from pathlib import Path

def merge_len(xs,lo,hi):
 ys=[]
 for a,b in xs:
  a=max(a,lo);b=min(b,hi)
  if a<b:ys.append((a,b))
 ys.sort(); total=0
 while ys:
  a,b=ys.pop(0)
  while ys and ys[0][0]<=b:
   _,d=ys.pop(0);b=max(b,d)
  total+=b-a
 return total

def derive(root,pair):
 d=Path(root)/f'pair-{pair:02d}'/'bounded_recovery'
 arm=json.loads((d/'arm-summary.json').read_text())
 ev=[json.loads(x) for x in (d/'runtime'/'events.jsonl').read_text().splitlines() if x.strip()]
 oe=json.loads((d/'runtime'/'owner-events.json').read_text())
 fid=arm['fallback_id']; acc=[x for x in ev if x.get('event')=='accepted' and x.get('id')==fid]
 if len(acc)!=1:return {'ok':False,'why':'accepted'}
 token=acc[0].get('intent_token');deadline=acc[0].get('valid_until_ns')
 ads=[x for x in ev if x.get('event')=='input_admission' and x.get('intent_token')==token]
 ups=[x for x in ev if x.get('event')=='input_release_transition' and x.get('intent_token')==token and x.get('operation')=='up']
 if len(ads)!=len(ups) or {x.get('key') for x in ads+ups}!={'d'}:return {'ok':False,'why':'shape'}
 ex=[x for x in oe if x.get('event')=='owner_release' and x.get('reason')=='expired' and x.get('valid_until_ns')==deadline]
 L=[];U=[];subs=0
 for a,u in zip(ads,ups):
  admitted=a.get('admitted_ns');ack=a.get('input_ack_ns');rs=u.get('release_call_started_ns');rr=u.get('release_call_returned_ns')
  if not all(type(x) is int for x in (admitted,ack,rs,rr)) or not admitted<=ack<=rs<=rr:return {'ok':False,'why':'clock'}
  if u.get('owner_transition_verified') is True:
   L.append((ack,rs));U.append((admitted,rr));continue
  if len(ex)!=1:return {'ok':False,'why':'expiry_count'}
  x=ex[0];v=x.get('verified_ns')
  if x.get('verified') is not True or x.get('keys_down')!=[] or x.get('buttons_down')!=[]:return {'ok':False,'why':'expiry_neutral'}
  if type(deadline) is not int or type(v) is not int or not ack<=deadline<=v<=rs:return {'ok':False,'why':'expiry_order'}
  L.append((ack,deadline));U.append((admitted,v));subs+=1
 term=[x for x in ev if x.get('event')=='terminal' and x.get('id')==fid]
 if len(term)!=1 or term[0].get('release',{}).get('verified') is not True or term[0].get('release',{}).get('keys_down')!=[] or term[0].get('release',{}).get('buttons_down')!=[]:return {'ok':False,'why':'terminal'}
 lo=arm['planner_window']['start_ns'];hi=arm['planner_window']['end_ns']; span=hi-lo
 low=merge_len(L,lo,hi);up=merge_len(U,lo,hi)
 return {'ok':0<=low<=up<=span,'subs':subs,'lower':low,'upper':up,'no_lower':span-up,'no_upper':span-low}

def selftest():
 base={'event':'owner_release','reason':'expired','verified':True,'keys_down':[],'buttons_down':[],'verified_ns':620,'valid_until_ns':600}
 tests=[]
 for key,val in [('reason','cancelled'),('verified',False),('keys_down',[40]),('valid_until_ns',601),('verified_ns',701)]:
  x=copy.deepcopy(base);x[key]=val
  good=x.get('reason')=='expired' and x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] and x.get('valid_until_ns')==600 and 600<=x.get('verified_ns',-1)<=700
  tests.append((key,not good))
 assert all(v for _,v in tests),tests
 print('PASS audit selftest',tests)

def main(root,result_path,out):
 claimed=json.loads(Path(result_path).read_text()); errs=[]; rows=[]
 for p in (1,2,3):
  got=derive(root,p); rows.append({'pair':p,**got})
  c=claimed['pairs'][p-1]['reconstructed']
  if not got.get('ok') or c.get('valid') is not True:errs.append(f'pair{p}:valid')
  if got.get('subs')!=len(c.get('substitutions',[])):errs.append(f'pair{p}:subs')
  for a,b in [('lower','retained_input_lower_bound_ns'),('upper','retained_input_upper_bound_ns'),('no_lower','no_retained_input_lower_bound_ns'),('no_upper','no_retained_input_upper_bound_ns')]:
   if got.get(a)!=c.get(b):errs.append(f'pair{p}:{a}')
 if [r.get('subs') for r in rows] != [0,1,1]:errs.append('substitution_shape')
 decision='PASS_AUDIT_EXPIRY_RELEASE_BOUND_SCOPED' if not errs else 'FAIL_AUDIT'
 data={'decision':decision,'errors':errs,'rows':rows,'mismatch_count':len(errs)}
 Path(out).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 print(json.dumps(data,sort_keys=True))
 return 0 if not errs else 1
if __name__=='__main__':
 if len(sys.argv)==2 and sys.argv[1]=='--self-test':selftest()
 else:raise SystemExit(main(sys.argv[1],sys.argv[2],sys.argv[3]))
