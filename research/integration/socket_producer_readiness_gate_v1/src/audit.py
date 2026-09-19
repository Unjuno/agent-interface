#!/usr/bin/env python3
import collections,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];RESULT=HERE/'RESULT.json';AUDIT=HERE/'AUDIT.json';FREEZE=HERE/'FREEZE.json';PREFLIGHT=HERE/'PREFLIGHT.json'
if AUDIT.exists():raise SystemExit('audit exists; overwrite forbidden')
data=json.loads(RESULT.read_text());freeze=json.loads(FREEZE.read_text());pre=json.loads(PREFLIGHT.read_text());rows=data['rows'];errors=[]
if len(rows)!=12:errors.append('row_count')
if data.get('formal_invocations')!=1 or data.get('formal_reruns')!=0:errors.append('rerun_accounting')
if hashlib.sha256(PREFLIGHT.read_bytes()).hexdigest()!=freeze['preflight_sha256']:errors.append('preflight_hash')
if pre.get('decision')!='PREFLIGHT_PASS':errors.append('preflight_controls')
cells=collections.Counter((r['policy'],r['scope']) for r in rows)
for p in ('endpoint_only','first_record_gate'):
 for s in ('action','request'):
  if cells[(p,s)]!=3:errors.append(f'cell:{p}:{s}')
baseline=[r for r in rows if r['policy']=='endpoint_only'];candidate=[r for r in rows if r['policy']=='first_record_gate']
if any(r['status']!='timeout' or r['record_count']!=0 or r['response_authority']!='none' for r in baseline):errors.append('baseline_discriminator')
for r in candidate:
 cid=r['case_id'];rec=r['record'] or {};expected_action=f'action-{cid}';expected_request=f'request-{cid}'
 if r['status']!='boundary' or r['record_count']!=1:errors.append(cid+':boundary')
 if r['response_authority']!='none':errors.append(cid+':authority')
 if r['socket_readiness']!='first_record_appended' or not isinstance(r['first_record_appended_ns'],int) or not isinstance(r['endpoint_published_ns'],int) or r['first_record_appended_ns']>r['endpoint_published_ns']:errors.append(cid+':readiness_order')
 if rec.get('event')!='effect_evidence' or rec.get('final_program')!=expected_action:errors.append(cid+':action_identity')
 if (rec.get('effect') or {}).get('action_id')!=expected_action:errors.append(cid+':effect_identity')
 adm=rec.get('admitted_request') or {}
 if adm.get('declared_action_id')!=expected_action or adm.get('transport_request_id')!=expected_request:errors.append(cid+':request_identity')
 if r['read_timeout_s']!=0.05 or r['producer_delay_s']!=0.15:errors.append(cid+':timing_mutation')
# Rehash every frozen source after formal.
rehash={};
for rel,meta in freeze['files'].items():
 p=HERE/rel;got=hashlib.sha256(p.read_bytes()).hexdigest();rehash[rel]=got
 if got!=meta['sha256']:errors.append('source_hash:'+rel)
# Exact git blob identities for upstream current-main dependencies.
for rel,want in freeze['exact_git_blobs'].items():
 got=subprocess.check_output(['git','hash-object',str(HERE/rel)],text=True).strip()
 if got!=want:errors.append('git_blob:'+rel)
if any('readiness_order' in e for e in errors):decision='FAIL_FALSE_READINESS'
elif any(e.endswith(':boundary') for e in errors):decision='FAIL_READY_LIVENESS'
elif 'baseline_discriminator' in errors and not any(e!='baseline_discriminator' for e in errors):decision='HOLD_NO_READINESS_DISCRIMINATOR'
elif errors:decision='FAIL_INTEGRITY'
else:decision='PASS_SOCKET_FIRST_RECORD_READINESS_SCOPED'
out={'schema':'socket-producer-readiness-audit-v1','decision':decision,'errors':errors,'cells':{f'{p}:{s}':cells[(p,s)] for p in ('endpoint_only','first_record_gate') for s in ('action','request')},'result_sha256':hashlib.sha256(RESULT.read_bytes()).hexdigest(),'postformal_source_sha256':rehash}
AUDIT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(decision,errors)
