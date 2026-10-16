from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SCENARIOS=('INDEPENDENT','SHARED_GLOBAL_CANDIDATE','SHARED_GLOBAL_SURFACE_ONLY','EXTERNAL_STALE')

def oracle_decision(scenario, prepared, after=None, changed=None):
    if scenario=='INDEPENDENT':
        ra={'A_LOCAL'};wa={'A_EFFECT'};rb={'B_LOCAL'};wb={'B_EFFECT'}; ch=set()
    elif scenario in ('SHARED_GLOBAL_CANDIDATE','SHARED_GLOBAL_SURFACE_ONLY'):
        ra=set();wa={'GLOBAL'};rb={'GLOBAL'};wb={'B_EFFECT'}; ch=set()
    else:
        ra=set();wa=set();rb={'B_LOCAL'};wb={'B_EFFECT'}; ch=set(changed or [])
    if (ra|rb)&ch:return 'REVALIDATE'
    if wa&wb or wa&rb or wb&ra:return 'SERIALIZE'
    return 'PARALLEL'

def validate(rows,result):
    e=[]
    if result.get('formal_invocations')!=1 or result.get('reruns')!=0 or result.get('replacements')!=0 or result.get('tuning')!=0:e.append('allocation')
    if len(rows)!=12 or result.get('rows')!=12:e.append('row_count')
    by={s:[] for s in SCENARIOS}; ids=set()
    for r in rows:
        cid=r.get('case_id')
        if cid in ids:e.append('duplicate_case')
        ids.add(cid)
        s=r.get('scenario')
        if s not in by:e.append('scenario');continue
        by[s].append(r)
        if r.get('error') is not None or not r.get('pass_case'):e.append('case_error')
        if not r.get('cleanup_workers_exited') or not r.get('cleanup_xvfb_exited'):e.append('cleanup')
        x=r.get('surface_xids',{})
        if not r.get('mapped_distinct_xids') or x.get('A')==x.get('B'):e.append('xid')
        p=r.get('prepared_receipts',{})
        if set(p)!={'A_LOCAL','B_LOCAL','GLOBAL'}:e.append('receipts')
    if any(len(by[s])!=3 for s in SCENARIOS):e.append('scenario_count')
    for r in by['INDEPENDENT']:
        if oracle_decision('INDEPENDENT',r['prepared_receipts'])!='PARALLEL' or r.get('decision')!='PARALLEL':e.append('ind_decision')
        if r.get('final_effects')!={'A':'LOCAL1','B':'LOCAL1'} or r.get('final_receipts',{}).get('GLOBAL')!=0:e.append('ind_effect')
        cmds=[c.get('command',{}) for c in r.get('owner_commands',[])]
        if sorted((c.get('op'),c.get('value')) for c in cmds)!=[('set_effect','LOCAL1'),('set_effect','LOCAL1')]:e.append('ind_ledger')
    for r in by['SHARED_GLOBAL_CANDIDATE']:
        if oracle_decision('SHARED_GLOBAL_CANDIDATE',r['prepared_receipts'])!='SERIALIZE' or r.get('decision')!='SERIALIZE':e.append('cand_decision')
        if r.get('prepared_receipts',{}).get('GLOBAL')!=0 or r.get('after_a_receipts',{}).get('GLOBAL')!=1 or not r.get('b_receipt_stale_after_a') or r.get('b_reprepare_count')!=1:e.append('cand_revalidation')
        if r.get('final_receipts',{}).get('GLOBAL')!=1 or r.get('final_effects',{}).get('B')!='G1':e.append('cand_effect')
        cmds=[c.get('command',{}) for c in r.get('owner_commands',[])]
        if any(c.get('value')=='G0' for c in cmds):e.append('cand_stale_effect')
    for r in by['SHARED_GLOBAL_SURFACE_ONLY']:
        if oracle_decision('SHARED_GLOBAL_SURFACE_ONLY',r['prepared_receipts'])!='SERIALIZE':e.append('surface_oracle')
        if r.get('decision')!='PARALLEL_SURFACE_ONLY' or not r.get('a_before_b_effect'):e.append('surface_comparator')
        if r.get('final_receipts',{}).get('GLOBAL')!=1 or r.get('final_effects',{}).get('B')!='G0':e.append('surface_discriminator')
    for r in by['EXTERNAL_STALE']:
        if oracle_decision('EXTERNAL_STALE',r['prepared_receipts'],changed=r.get('changed_resources'))!='REVALIDATE' or r.get('decision')!='REVALIDATE':e.append('stale_decision')
        if r.get('changed_resources')!=['B_LOCAL'] or r.get('b_effect_command_count')!=0 or r.get('final_effects',{}).get('B')!='NONE':e.append('stale_effect')
        if any(c.get('command',{}).get('op')=='set_effect' for c in r.get('owner_commands',[])):e.append('stale_ledger')
    if result.get('surface_only_stale_effects')!=3 or result.get('candidate_stale_effects')!=0:e.append('summary_stale')
    if not all(result.get('gates',{}).values()) or len(result.get('gates',{}))!=6:e.append('gates')
    if result.get('decision')!='PASS_OPTIMISTIC_READWRITE_X11_TRANSFER_SCOPED' or result.get('pass') is not True:e.append('decision')
    return sorted(set(e))

def main():
    rows=json.loads((ROOT/'FORMAL_ROWS.json').read_text());result=json.loads((ROOT/'RESULT.json').read_text())
    errors=validate(rows,result)
    out={'pass':not errors,'errors':errors,'decision':result.get('decision') if not errors else 'FAIL_INTEGRITY',
         'rows_sha256':hashlib.sha256((ROOT/'FORMAL_ROWS.json').read_bytes()).hexdigest(),
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
