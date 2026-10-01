from __future__ import annotations
import hashlib,json
from pathlib import Path
from contract import CRITICAL,reduce_candidate
from oracle_independent import reduce_oracle
from corpus import random_batches,exhaustive_batches,SEED,RANDOM_BATCHES
HERE=Path(__file__).resolve().parent;r=json.loads((HERE/'FORMAL_RESULT.json').read_text());rnd=rec=exn=exe=crit=cerr=stale=scope=auth=0;h=hashlib.sha256()
def chk(rows,now,max_age):
 global crit,cerr,stale,scope,auth
 c=reduce_candidate(rows,now,max_age);o=reduce_oracle(rows,now,max_age);ids={x.event_id:x for x in rows};cr=[x.event_id for x in rows if x.kind in CRITICAL];crit+=len(cr)
 if c['critical_ids']!=cr or [x for x in c['delivered_ids'] if ids[x].kind in CRITICAL]!=cr:cerr+=1
 states=[ids[x] for x in c['delivered_ids'] if ids[x].kind not in CRITICAL]
 if any(now-x.t_ns>max_age for x in states):stale+=1
 keys=[(x.session,x.target,x.stream) for x in states]
 if len(keys)!=len(set(keys)):scope+=1
 if c.get('grants_input_authority') is not False:auth+=1
 h.update(json.dumps([[(x.event_id,x.seq,x.t_ns,x.session,x.target,x.stream,x.kind) for x in rows],now,max_age,c],sort_keys=True,separators=(',',':')).encode());return c==o
for rows,now,max_age in random_batches():rec+=len(rows);rnd+=chk(rows,now,max_age)
for rows,now,max_age in exhaustive_batches():exn+=1;exe+=chk(rows,now,max_age)
checks={'task':r.get('task')=='FRESHNESS-BACKPRESSURE-CRITICAL-RETENTION-FORMAL-20260917-002','blob':r.get('candidate_git_blob')=='404a452aa304b4bde73ec0182450d241e2a744af','seed':r.get('seed')==SEED,'random':r.get('random_batches')==RANDOM_BATCHES and r.get('random_equal')==rnd==RANDOM_BATCHES and r.get('random_records')==rec,'exhaustive':r.get('exhaustive_batches')==exn and r.get('exhaustive_equal')==exe==exn,'critical':r.get('critical_records')==crit and r.get('critical_batch_errors')==cerr==0,'stale':r.get('stale_noncritical_delivered_batches')==stale==0,'scope':r.get('scope_cardinality_errors')==scope==0,'authority':r.get('authority_errors')==auth==0,'controls':r.get('controls_passed')==r.get('controls_total')==10,'digest':r.get('digest_sha256')==h.hexdigest(),'formal':(r.get('formal_invocations'),r.get('reruns'))==(1,0),'side_effects':all(r.get(k)==0 for k in ['model_calls','network_actions','task_input_actions']),'decision':r.get('decision')=='PASS_FRESHNESS_BACKPRESSURE_FORMAL_SCOPED'}
a={'task':r['task'],'passed':all(checks.values()),'checks':checks,'errors':[k for k,v in checks.items() if not v]};(HERE/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n');print(json.dumps(a,sort_keys=True))
