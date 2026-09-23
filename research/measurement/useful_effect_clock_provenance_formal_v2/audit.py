from __future__ import annotations
import hashlib,json
from pathlib import Path
from candidate import clock_bound
from oracle_independent import classify,parent988
from corpus import cases,COUNTS,SEED
HERE=Path(__file__).resolve().parent; r=json.loads((HERE/'FORMAL_RESULT.json').read_text()); N=sum(COUNTS.values())
equal=0; same=0; cross=0; digest=hashlib.sha256(); strata={k:0 for k in COUNTS}
for s,e,acts in cases():
 c=clock_bound(e,acts); o=classify(e,acts); equal += c==o; strata[s]+=1
 if s=='same_clock': same += c!=parent988(e,acts)
 if s in ('cross_domain','cross_epoch','missing_clock') and c in ('useful_bound','nonuseful_bound'):cross+=1
 digest.update(json.dumps([s,e.__dict__,[a.__dict__ for a in acts],c],sort_keys=True,separators=(',',':')).encode())
checks={'task':r.get('task')=='USEFUL-EFFECT-CLOCK-PROVENANCE-FORMAL-20260917-002','candidate_blob':r.get('candidate_git_blob')=='b8e35581eaf1f99f6ad973f4bde1367e43eb0a1b','seed':r.get('seed')==SEED,'counts':r.get('records')==N and r.get('strata')==strata,'oracle':equal==N and r.get('candidate_oracle_equal')==N,'parent':same==0 and r.get('same_clock_parent_mismatches')==0,'cross':cross==0 and r.get('cross_clock_bound_promotions')==0,'controls':r.get('controls_passed')==r.get('controls_total')==13,'digest':r.get('digest_sha256')==digest.hexdigest(),'formal':(r.get('formal_invocations'),r.get('reruns'))==(1,0),'side_effects':all(r.get(k)==0 for k in ['model_calls','network_actions','task_input_actions','authority_actions','occupancy_mutations']),'decision':r.get('decision')=='PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED'}
a={'task':r['task'],'passed':all(checks.values()),'checks':checks,'errors':[k for k,v in checks.items() if not v]};(HERE/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n');print(json.dumps(a,sort_keys=True))
