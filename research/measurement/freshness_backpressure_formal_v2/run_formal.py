from __future__ import annotations
import hashlib,json
from pathlib import Path
from contract import Record,CRITICAL,STATE_KINDS,reduce_candidate
from oracle_independent import reduce_oracle
from corpus import random_batches,exhaustive_batches,SEED,RANDOM_BATCHES
HERE=Path(__file__).resolve().parent; OUT=HERE/'FORMAL_RESULT.json'
if OUT.exists(): raise RuntimeError('formal result exists')
random_equal=0;random_records=0;exhaustive_equal=0;exhaustive_total=0;critical_total=0;critical_errors=0;stale_delivered=0;scope_errors=0;authority_errors=0;digest=hashlib.sha256()
def check_batch(rows,now,max_age):
 global critical_total,critical_errors,stale_delivered,scope_errors,authority_errors
 c=reduce_candidate(rows,now,max_age);o=reduce_oracle(rows,now,max_age)
 ids={r.event_id:r for r in rows}; crit=[r.event_id for r in rows if r.kind in CRITICAL]; critical_total+=len(crit)
 if c['critical_ids']!=crit or [x for x in c['delivered_ids'] if ids[x].kind in CRITICAL]!=crit: critical_errors+=1
 state_delivered=[ids[x] for x in c['delivered_ids'] if ids[x].kind not in CRITICAL]
 if any(now-r.t_ns>max_age for r in state_delivered): stale_delivered+=1
 keys=[(r.session,r.target,r.stream) for r in state_delivered]
 if len(keys)!=len(set(keys)): scope_errors+=1
 if c.get('grants_input_authority') is not False: authority_errors+=1
 digest.update(json.dumps([[(r.event_id,r.seq,r.t_ns,r.session,r.target,r.stream,r.kind) for r in rows],now,max_age,c],sort_keys=True,separators=(',',':')).encode())
 return c==o
for rows,now,max_age in random_batches():
 random_records+=len(rows);random_equal+=check_batch(rows,now,max_age)
for rows,now,max_age in exhaustive_batches():
 exhaustive_total+=1;exhaustive_equal+=check_batch(rows,now,max_age)
controls=[]
def expect_error(name,rows,now=100,max_age=10):
 try: reduce_candidate(rows,now,max_age); got='accepted'; ok=False
 except ValueError: got='ValueError'; ok=True
 controls.append({'name':name,'pass':ok,'got':got})
def expect_value(name,rows,want,now=100,max_age=10):
 try: got=reduce_candidate(rows,now,max_age); ok=(got==want)
 except Exception as e: got=type(e).__name__;ok=False
 controls.append({'name':name,'pass':ok,'got':got if isinstance(got,str) else got})
R=lambda eid,seq,t,s='s',ta='t',st='r',k='FRAME':Record(eid,seq,t,s,ta,st,k)
expect_error('duplicate_id',[R('a',0,90),R('a',1,91)])
expect_error('same_seq',[R('a',0,90),R('b',0,91)])
expect_error('malformed_scope',[R('a',0,90,s=' ')])
expect_error('future_timestamp',[R('a',0,101)])
expect_error('unknown_kind',[R('a',0,90,k='BOGUS')])
expect_error('negative_clock',[R('a',0,0)],now=-1)
expect_value('stale_only',[R('a',0,50)],reduce_oracle([R('a',0,50)],100,10))
expect_value('old_critical',[R('a',0,1,k='LEASE_EXPIRED')],reduce_oracle([R('a',0,1,k='LEASE_EXPIRED')],100,10))
expect_value('critical_only',[R('a',0,1,k='FOCUS_CHANGED'),R('b',1,2,k='EFFECT_VERIFIED')],reduce_oracle([R('a',0,1,k='FOCUS_CHANGED'),R('b',1,2,k='EFFECT_VERIFIED')],100,10))
cross=[R('a',0,95,s='s0',ta='t0',st='r0'),R('b',1,96,s='s1',ta='t1',st='r1')];expect_value('cross_scope',cross,reduce_oracle(cross,100,10))
controls_pass=sum(x['pass'] for x in controls)
passed=(random_equal==RANDOM_BATCHES and exhaustive_equal==exhaustive_total and critical_errors==0 and stale_delivered==0 and scope_errors==0 and authority_errors==0 and controls_pass==len(controls))
r={'task':'FRESHNESS-BACKPRESSURE-CRITICAL-RETENTION-FORMAL-20260917-002','candidate_git_blob':'404a452aa304b4bde73ec0182450d241e2a744af','seed':SEED,'formal_invocations':1,'reruns':0,'random_batches':RANDOM_BATCHES,'random_records':random_records,'random_equal':random_equal,'exhaustive_batches':exhaustive_total,'exhaustive_equal':exhaustive_equal,'critical_records':critical_total,'critical_batch_errors':critical_errors,'stale_noncritical_delivered_batches':stale_delivered,'scope_cardinality_errors':scope_errors,'authority_errors':authority_errors,'controls_passed':controls_pass,'controls_total':len(controls),'controls':controls,'digest_sha256':digest.hexdigest(),'model_calls':0,'network_actions':0,'task_input_actions':0,'decision':'PASS_FRESHNESS_BACKPRESSURE_FORMAL_SCOPED' if passed else 'FAIL_FRESHNESS_BACKPRESSURE_FORMAL'}
OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
