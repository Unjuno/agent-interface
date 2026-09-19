#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(root):
    r=json.loads((root/'RESULT.json').read_text()); errs=[]
    if r.get('formal_invocation')!=1 or r.get('formal_reruns')!=0: errs.append('formal_count')
    rows=r.get('rows',[])
    if [x.get('task_id') for x in rows] != ['A1','A2','A3','B1','B2','B3']: errs.append('task_order')
    if [x.get('layout') for x in rows] != ['A','A','A','B','B','B']: errs.append('layout_order')
    if len(rows)!=6 or not all(x.get('task_evaluation',{}).get('status')=='VERIFIED' and x.get('task_evaluation',{}).get('contract_satisfied') is True for x in rows): errs.append('task_effect')
    if len(rows)!=6 or not all(x.get('reset',{}).get('ok') is True for x in rows): errs.append('reset')
    allowed={'task_id','task','layout','benchmark_epoch'}
    forbidden={'tiles','copper','source_item','core_x','core_y','unit','oracle','evaluation','contract_satisfied'}
    if any(set(x.get('controller_visible',{}))!=allowed or set(x.get('controller_visible',{})) & forbidden or x.get('oracle_leak_free') is not True for x in rows): errs.append('oracle_leak')
    c=r.get('controls',{})
    if c.get('missing_reset',{}).get('next_task_authority') is not False: errs.append('missing_reset_escape')
    for k in ('target_occupied_reset','collateral_reset','copper_not_restored','duplicate_epoch'):
        if c.get(k,{}).get('ok') is not False: errs.append(k)
    if c.get('wrong_rotation_task',{}).get('contract_satisfied') is not False: errs.append('reset_laundered_task')
    if c.get('oracle_leak',{}).get('leak_free') is not False: errs.append('leak_control')
    expected='PASS_MINDUSTRY_REPEAT_RESET_CONTRACT_SCOPED' if not errs else 'FAIL_MINDUSTRY_REPEAT_RESET_CONTRACT'
    if r.get('decision')!=expected: errs.append('decision')
    return {'schema':'mindustry_repeat_reset_contract_audit_v1','passed':not errs,'decision':expected,'errors':errs,'result_sha256':sha(root/'RESULT.json')}

def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT
    out=audit(root)
    if len(sys.argv)==1:(root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['passed'] else 1)
if __name__=='__main__': main()
