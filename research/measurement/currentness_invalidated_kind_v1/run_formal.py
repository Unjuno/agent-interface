from __future__ import annotations
import hashlib,json,random
from pathlib import Path
from candidate_contract import Record,reduce_candidate
from parent_contract import Record as PRecord, reduce_candidate as parent_reduce
from reference import R,reduce_ref
H=Path(__file__).resolve().parent; O=H/'RESULT.json'; SEED=106020260918001; MIXED=100000; OLD=50000
CRIT=['FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED','CURRENTNESS_INVALIDATED']; STATES=['FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH']; OLDK=CRIT[:-1]+STATES

def gen(rng,i,kinds):
 n=rng.randrange(1,10); now=1000+rng.randrange(1000); age=rng.randrange(0,200); rows=[]
 for j in range(n):
  t=max(0,now-rng.randrange(0,250)); rows.append(Record(f'{i}-{j}',j,t,f's{rng.randrange(3)}',f't{rng.randrange(3)}',f'x{rng.randrange(3)}',rng.choice(kinds)))
 return rows,now,age

def main():
 if O.exists(): raise RuntimeError('RESULT exists')
 rng=random.Random(SEED); mm=oldmm=newlost=auth=0; h=hashlib.sha256(); newevents=0
 for i in range(MIXED):
  rows,now,age=gen(rng,i,CRIT+STATES); a=reduce_candidate(rows,now,age); b=reduce_ref([R(**x.__dict__) for x in rows],now,age); mm+=a!=b; auth+=bool(a['grants_input_authority']); new=[x.event_id for x in rows if x.kind=='CURRENTNESS_INVALIDATED']; newevents+=len(new); newlost+=any(x not in a['critical_ids'] or x not in a['delivered_ids'] for x in new); h.update(json.dumps(a,sort_keys=True,separators=(',',':')).encode())
 for i in range(OLD):
  rows,now,age=gen(rng,200000+i,OLDK); a=reduce_candidate(rows,now,age); p=parent_reduce([PRecord(**x.__dict__) for x in rows],now,age); oldmm+=a!=p; h.update(json.dumps(['old',a],sort_keys=True,separators=(',',':')).encode())
 d='PASS_CURRENTNESS_INVALIDATED_KIND_SCOPED' if (mm,oldmm,newlost,auth)==(0,0,0,0) and newevents>0 else 'FAIL_CURRENTNESS_KIND_CONTRACT'
 r={'schema':'currentness_invalidated_kind_result_v1','task':'CURRENTNESS-INVALIDATED-CRITICAL-KIND-20260918-001','base':'f9815a0ae8f3c54e02d66b19cb999c03f52719cf','seed':SEED,'mixed_streams':MIXED,'parent_domain_streams':OLD,'mixed_mismatches':mm,'parent_regressions':oldmm,'new_kind_events':newevents,'new_kind_loss_cases':newlost,'authority_promotions':auth,'digest':h.hexdigest(),'decision':d,'formal_invocation':1,'reruns':0,'source_git_blobs':{'parent_contract':'404a452aa304b4bde73ec0182450d241e2a744af','#1051_RESULT':'ecae38ae21361ec9696c6ef604841846364dce5b'},'model_calls':0,'gui_actions':0,'task_input_actions':0}
 O.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(d)
if __name__=='__main__': main()
