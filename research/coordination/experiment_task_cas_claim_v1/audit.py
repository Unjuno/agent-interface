from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def task_ref(task_id): return 'refs/experiment-claims/'+hashlib.sha256(task_id.encode()).hexdigest()
def canonical(obj): return (json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
def oid_for(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def audit(result):
    errors=[]; primary=result.get('primary',[]); distinct=result.get('different_task_controls',[])
    if result.get('formal_invocation')!=1 or result.get('reruns')!=0: errors.append('formal_count')
    if len(primary)!=192: errors.append('primary_count')
    base=result.get('base_sha')
    for c in primary:
        n=c['contenders']; rows=c['rows']; policy=c['policy']; tid=c['task_id']
        if c['task_ref']!=task_ref(tid) or len(rows)!=n: errors.append(c['case_id']+':shape'); continue
        contenders={r['worker_id'] for r in rows}
        if not all(r.get('pre_unclaimed') is True for r in rows): errors.append(c['case_id']+':preclaim')
        for r in rows:
            obj={'base_sha':base,'nonce':f"{c['case_id']}-nonce-{int(r['worker_id'][1:])}",'task_id':tid,'worker_id':r['worker_id']}
            if r['claim_oid']!=oid_for(canonical(obj)): errors.append(c['case_id']+':oid')
        if policy=='READ_APPEND':
            if c['owner_count']<=1 or c['owner_count']!=n: errors.append(c['case_id']+':baseline_multiowner')
            if len(c['append_log_lines'])!=n: errors.append(c['case_id']+':append_count')
        elif policy=='TASK_REF_CAS':
            if c['owner_count']!=1: errors.append(c['case_id']+':cas_owner_count')
            obj=c.get('final_object'); oid=c.get('final_oid')
            if not isinstance(obj,dict) or obj.get('worker_id') not in contenders or obj.get('task_id')!=tid: errors.append(c['case_id']+':winner_object')
            elif oid!=oid_for(canonical(obj)): errors.append(c['case_id']+':winner_oid')
            for r in rows:
                if r['owner']:
                    if r['claim_oid']!=oid: errors.append(c['case_id']+':owner_oid')
                else:
                    if r.get('resolved_winner_oid')!=oid or r.get('resolved_winner')!=obj: errors.append(c['case_id']+':loser_resolution')
        else: errors.append(c['case_id']+':policy')
    if len(distinct)!=32: errors.append('distinct_count')
    for c in distinct:
        if c.get('owner_count')!=8 or len(c.get('resolved',[]))!=8: errors.append(c['case_id']+':distinct_liveness'); continue
        if len(set(c['tasks']))!=8: errors.append(c['case_id']+':distinct_tasks')
        for x in c['resolved']:
            if x['object'].get('task_id')!=x['task_id'] or x['oid']!=oid_for(canonical(x['object'])): errors.append(c['case_id']+':distinct_object')
    decision='PASS_TASK_KEYED_CAS_CLAIM_SCOPED' if not errors else 'FAIL_TASK_CAS_OR_INTEGRITY'
    return {'schema':'experiment_task_cas_claim_audit_v1','passed':not errors,'decision':decision,'errors':errors,'primary_cases':len(primary),'different_task_controls':len(distinct)}
if __name__=='__main__':
    r=json.loads((HERE/'formal-output/FORMAL_RESULT.json').read_text()); out=audit(r); (HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['passed'] else 1)
