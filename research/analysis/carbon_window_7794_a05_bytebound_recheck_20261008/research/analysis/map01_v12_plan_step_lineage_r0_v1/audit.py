from __future__ import annotations
import copy,hashlib,json,random,sys
from pathlib import Path
import candidate,oracle
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make():
 r=[dict(event='input_release_transition',operation='up',transition_schema='input-release-transition-v3',key='a',owner_id='o',intent_token='t',ordinary_release_candidate=True,release_batch_schema='input-release-batch-v3',release_batch_size=1,release_batch_position=0,release_batch_identifier='p',release_batch_step=1,owner_transition_verified=True,physical_verification_authoritative=False,grants_input_authority=False,release_call_started_ns=100,release_call_returned_ns=140)]
 p={'a':[dict(edge='down',status='CONFIRMED_PHYSICAL_DOWN',actuation_id='x',owner_id='o',intent_token='t',key='a',interval=(10,20)),dict(edge='up',status='CONFIRMED_PHYSICAL_UP',actuation_id='x',owner_id='o',intent_token='t',key='a',interval=(110,120))]}
 return r,p,copy.deepcopy(candidate.EXPECTED_SOURCE)
def main():
 R=json.loads((ROOT/'RESULT.json').read_text());err=[]
 if R.get('decision')!='PASS_MAP01_V12_PLAN_STEP_LINEAGE_R0_SCOPED':err.append('decision')
 if R.get('primary_invocations')!=1 or R.get('reruns')!=0 or R.get('tuning')!=0:err.append('budget')
 for k in ('exhaustive_mismatches','random_mismatches','v3_only_accepted','timestamp_changes','authority_expansions'):
  if R.get(k)!=0:err.append(k)
 # Independent fresh mutation audit; no primary rerun.
 rng=random.Random(1907);mismatch=0;accepted=0
 for i in range(20000):
  r,p,s=make(); mode=rng.randrange(12)
  if mode==0:pass
  elif mode==1:r[0]['ordinary_release_candidate']=False
  elif mode==2:r[0]['physical_verification_authoritative']=True
  elif mode==3:p['a'][0]['actuation_id']=''
  elif mode==4:p['a'][1]['status']='NOOP_ALREADY_UP';p['a'][1]['interval']=None
  elif mode==5:p['a'][0]['owner_id']='z';p['a'][1]['owner_id']='z'
  elif mode==6:p['a'][0]['intent_token']='z';p['a'][1]['intent_token']='z'
  elif mode==7:p['a'][1]['interval']=(90,95)
  elif mode==8:s['input_owner_v12_sha256']='0'*64
  elif mode==9:r[0]['release_batch_position']=2
  elif mode==10:r[0]['grants_input_authority']=True
  elif mode==11:p={}
  c=candidate.bind_batch(r,p,s);a=c['status']=='BOUND_MAP01_PHYSICAL_BATCH';o=oracle.oracle(r,p,s);mismatch+=(a!=o);accepted+=a
 if mismatch:err.append('audit_oracle_mismatch')
 # Explicit laundering controls.
 r,p,s=make();p={}
 if candidate.bind_batch(r,p,s)['status']=='BOUND_MAP01_PHYSICAL_BATCH':err.append('v3_launder')
 r,p,s=make();c=candidate.bind_batch(r,p,s)
 z=c['actuations'][0]
 if z['physical_down_interval']!=[10,20] or z['physical_up_interval']!=[110,120] or z['map01_release_rpc_interval']!=[100,140]:err.append('timestamp_copy')
 if c['grants_input_authority'] is not False or z['grants_input_authority'] is not False:err.append('authority')
 out=dict(passed=not err,errors=err,audit_cases=20000,audit_mismatches=mismatch,audit_accepted=accepted,result_sha256=sha(ROOT/'RESULT.json'),candidate_sha256=sha(ROOT/'candidate.py'),oracle_sha256=sha(ROOT/'oracle.py'))
 (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));sys.exit(0 if not err else 1)
if __name__=='__main__':main()
