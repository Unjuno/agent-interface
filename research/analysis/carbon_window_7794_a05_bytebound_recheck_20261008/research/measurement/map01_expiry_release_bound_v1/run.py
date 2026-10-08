from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

ARTIFACT_SHA256='571be29b4501b7e697f5edcfdc373519f6e404190ae93fdee0f87ba3cfb39f49'

def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def union_duration(intervals,lo,hi):
 xs=[]
 for a,b in intervals:
  a=max(a,lo); b=min(b,hi)
  if b>a: xs.append((a,b))
 xs.sort()
 if not xs:return 0
 total=0;a,b=xs[0]
 for c,d in xs[1:]:
  if c<=b:b=max(b,d)
  else:total+=b-a;a,b=c,d
 return total+b-a

def recover_arm(arm, events, owner_events):
 fallback=arm['fallback_id']; window=arm['planner_window']; wlo=window['start_ns']; whi=window['end_ns']
 accepted=[r for r in events if r.get('event')=='accepted' and r.get('id')==fallback]
 if len(accepted)!=1:return {'valid':False,'errors':['accepted_count']}
 token=accepted[0].get('intent_token'); deadline=accepted[0].get('valid_until_ns')
 if not isinstance(token,str) or type(deadline) is not int:return {'valid':False,'errors':['accepted_identity']}
 admissions=[r for r in events if r.get('event')=='input_admission' and r.get('intent_token')==token]
 releases=[r for r in events if r.get('event')=='input_release_transition' and r.get('intent_token')==token and r.get('operation')=='up']
 errors=[]; substitutions=[]; lower=[]; upper=[]
 if len(admissions)!=len(releases): errors.append('count')
 keys={r.get('key') for r in admissions+releases}
 if keys != {'d'}: errors.append('single_key_scope')
 expiry=[r for r in owner_events if r.get('event')=='owner_release' and r.get('reason')=='expired' and r.get('valid_until_ns')==deadline]
 for idx,(a,r) in enumerate(zip(admissions,releases)):
  vals=[a.get('admitted_ns'),a.get('input_ack_ns'),r.get('release_call_started_ns'),r.get('release_call_returned_ns')]
  if any(type(x) is not int for x in vals): errors.append(f'{idx}:clock');continue
  admitted,ack,rs,rr=vals
  if not admitted<=ack<=rs<=rr: errors.append(f'{idx}:order');continue
  if r.get('owner_transition_verified') is True:
   lower.append((ack,rs)); upper.append((admitted,rr)); continue
  if len(expiry)!=1: errors.append(f'{idx}:expiry_count');continue
  e=expiry[0]; ev=e.get('verified_ns')
  if e.get('verified') is not True or e.get('keys_down')!=[] or e.get('buttons_down')!=[]: errors.append(f'{idx}:expiry_not_neutral');continue
  if type(ev) is not int or not ack<=deadline<=ev<=rs: errors.append(f'{idx}:expiry_order');continue
  lower.append((ack,deadline)); upper.append((admitted,ev)); substitutions.append({'index':idx,'key':'d','release_interval':[deadline,ev],'redundant_release_started_ns':rs})
 terminal=[r for r in events if r.get('event')=='terminal' and r.get('id')==fallback]
 if len(terminal)!=1 or not isinstance(terminal[0].get('release'),dict) or terminal[0]['release'].get('verified') is not True or terminal[0]['release'].get('keys_down')!=[] or terminal[0]['release'].get('buttons_down')!=[]: errors.append('terminal_neutrality')
 lo=union_duration(lower,wlo,whi); up=union_duration(upper,wlo,whi)
 if up<lo or up>whi-wlo: errors.append('bounds')
 return {'valid':not errors,'errors':errors,'substitutions':substitutions,'retained_input_lower_bound_ns':lo,'retained_input_upper_bound_ns':up,'no_retained_input_lower_bound_ns':whi-wlo-up,'no_retained_input_upper_bound_ns':whi-wlo-lo,'admission_count':len(admissions),'release_count':len(releases),'deadline_ns':deadline}

def extract(root:Path):
 rows=[]
 for pair in (1,2,3):
  d=root/f'pair-{pair:02d}'/'bounded_recovery'
  arm=json.loads((d/'arm-summary.json').read_text())
  events=[json.loads(x) for x in (d/'runtime'/'events.jsonl').read_text().splitlines() if x.strip()]
  owner=json.loads((d/'runtime'/'owner-events.json').read_text())
  rows.append({'pair':pair,'arm_summary':arm,'events':events,'owner_events':owner})
 return rows

def main(root,out):
 rows=extract(Path(root)); result=[]
 for row in rows:
  rec=recover_arm(row['arm_summary'],row['events'],row['owner_events'])
  old=row['arm_summary']['input_bounds']
  result.append({'pair':row['pair'],'historical_valid':old['valid'],'historical_invalid':old['invalid'],'historical_bounds':old,'reconstructed':rec})
 decision='PASS_EXPIRY_RELEASE_BOUND_RECONSTRUCTION_SCOPED' if result[0]['historical_valid'] and result[0]['reconstructed']['valid'] and len(result[0]['reconstructed']['substitutions'])==0 and all((not x['historical_valid']) and x['reconstructed']['valid'] and len(x['reconstructed']['substitutions'])==1 for x in result[1:]) else 'HOLD_EXPIRY_RELEASE_BINDING_INCOMPLETE'
 outp={'schema':'map01-expiry-release-bound-v1','decision':decision,'pairs':result,'formal_invocations':1,'reruns':0}
 Path(out).write_text(json.dumps(outp,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'decision':decision,'pairs':[{'pair':x['pair'],'old':x['historical_valid'],'new':x['reconstructed']['valid'],'subs':len(x['reconstructed']['substitutions'])} for x in result]},sort_keys=True))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
