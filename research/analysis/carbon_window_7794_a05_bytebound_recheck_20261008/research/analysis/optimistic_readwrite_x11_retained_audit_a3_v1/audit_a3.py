from __future__ import annotations
import base64, copy, gzip, hashlib, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PARENT=Path(os.environ['AI1750_PARENT']) if 'AI1750_PARENT' in os.environ else ROOT.parents[1]/'live_control'/'optimistic_readwrite_x11_transfer_r1_v1'
EXPECTED={
 'raw_rows_sha256':'230a7253f6b013a728feab0f8d5d3b75b12b9d1c47ddf0856b223b67e7b0fba8',
 'result_sha256':'180f6a75a8ed2876cf93d5abfd0d07e4fe2d3b90f0a08db7d2fb481c7a554fa2',
 'original_audit_sha256':'dae25b7c69fed2d04236a02e1abf66230f1991f4803132d492b709eabae554b8',
 'parent_disposition':'FAIL_INTEGRITY_AUDIT_GATE_COUNT',
}
SCENARIOS=('INDEPENDENT','SHARED_GLOBAL_CANDIDATE','SHARED_GLOBAL_SURFACE_ONLY','EXTERNAL_STALE')
GATE_NAMES={'allocation','complete','distinct_xids','independent','candidate_shared','surface_only_discriminator','external_stale'}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def load_parent(parent=PARENT, expected=EXPECTED):
    b64=(parent/'FORMAL_ROWS.json.gz.b64').read_bytes()
    retention=json.loads((parent/'RETENTION.json').read_text())
    errors=[]
    if sha(b64)!=retention.get('base64_sha256'): errors.append('base64_hash')
    gz=base64.b64decode(b64)
    if sha(gz)!=retention.get('gzip_sha256'): errors.append('gzip_hash')
    raw=gzip.decompress(gz)
    if sha(raw)!=retention.get('raw_sha256') or sha(raw)!=expected['raw_rows_sha256']: errors.append('raw_hash')
    result_bytes=(parent/'RESULT.json').read_bytes(); audit_bytes=(parent/'AUDIT.json').read_bytes()
    if sha(result_bytes)!=expected['result_sha256']: errors.append('result_hash')
    if sha(audit_bytes)!=expected['original_audit_sha256']: errors.append('original_audit_hash')
    disposition=json.loads((parent/'FORMAL_DISPOSITION.json').read_text())
    if disposition.get('scientific_disposition')!=expected['parent_disposition']: errors.append('parent_disposition')
    return json.loads(raw),json.loads(result_bytes),json.loads(audit_bytes),disposition,errors

def oracle_decision(scenario,changed=()):
    if scenario=='INDEPENDENT': ra={'A_LOCAL'};wa={'A_EFFECT'};rb={'B_LOCAL'};wb={'B_EFFECT'}
    elif scenario in ('SHARED_GLOBAL_CANDIDATE','SHARED_GLOBAL_SURFACE_ONLY'):ra=set();wa={'GLOBAL'};rb={'GLOBAL'};wb={'B_EFFECT'}
    else:ra=set();wa=set();rb={'B_LOCAL'};wb={'B_EFFECT'}
    ch=set(changed)
    if (ra|rb)&ch:return 'REVALIDATE'
    if wa&wb or wa&rb or wb&ra:return 'SERIALIZE'
    return 'PARALLEL'

def recompute(rows):
    e=[];by={s:[] for s in SCENARIOS};ids=set()
    for r in rows:
        cid=r.get('case_id')
        if cid in ids:e.append('duplicate_case')
        ids.add(cid);s=r.get('scenario')
        if s not in by:e.append('scenario');continue
        by[s].append(r)
        if r.get('error') is not None or not r.get('pass_case'):e.append('case_error')
        if not r.get('cleanup_workers_exited') or not r.get('cleanup_xvfb_exited'):e.append('cleanup')
        x=r.get('surface_xids',{})
        if not r.get('mapped_distinct_xids') or x.get('A')==x.get('B'):e.append('xid')
        if set(r.get('prepared_receipts',{}))!={'A_LOCAL','B_LOCAL','GLOBAL'}:e.append('receipts')
    gates={}
    gates['allocation']=len(rows)==12 and all(len(by[s])==3 for s in SCENARIOS)
    gates['complete']=not any(x in e for x in ('case_error','cleanup'))
    gates['distinct_xids']='xid' not in e
    gates['independent']=all(oracle_decision('INDEPENDENT')=='PARALLEL' and r.get('decision')=='PARALLEL' and r.get('final_effects')=={'A':'LOCAL1','B':'LOCAL1'} and r.get('final_receipts',{}).get('GLOBAL')==0 and sorted((c.get('command',{}).get('op'),c.get('command',{}).get('value')) for c in r.get('owner_commands',[]))==[('set_effect','LOCAL1'),('set_effect','LOCAL1')] for r in by['INDEPENDENT'])
    gates['candidate_shared']=all(oracle_decision('SHARED_GLOBAL_CANDIDATE')=='SERIALIZE' and r.get('decision')=='SERIALIZE' and r.get('prepared_receipts',{}).get('GLOBAL')==0 and r.get('after_a_receipts',{}).get('GLOBAL')==1 and r.get('b_receipt_stale_after_a') is True and r.get('b_reprepare_count')==1 and r.get('final_receipts',{}).get('GLOBAL')==1 and r.get('final_effects',{}).get('B')=='G1' and not any(c.get('command',{}).get('value')=='G0' for c in r.get('owner_commands',[])) for r in by['SHARED_GLOBAL_CANDIDATE'])
    gates['surface_only_discriminator']=all(oracle_decision('SHARED_GLOBAL_SURFACE_ONLY')=='SERIALIZE' and r.get('decision')=='PARALLEL_SURFACE_ONLY' and r.get('a_before_b_effect') is True and r.get('prepared_receipts',{}).get('GLOBAL')==0 and r.get('final_receipts',{}).get('GLOBAL')==1 and r.get('final_effects',{}).get('B')=='G0' for r in by['SHARED_GLOBAL_SURFACE_ONLY'])
    gates['external_stale']=all(oracle_decision('EXTERNAL_STALE',r.get('changed_resources',()))=='REVALIDATE' and r.get('decision')=='REVALIDATE' and r.get('changed_resources')==['B_LOCAL'] and r.get('b_effect_command_count')==0 and r.get('prepared_receipts',{}).get('B_LOCAL')==0 and r.get('final_receipts',{}).get('B_LOCAL')==1 and r.get('final_effects',{}).get('B')=='NONE' and not any(c.get('command',{}).get('op')=='set_effect' for c in r.get('owner_commands',[])) for r in by['EXTERNAL_STALE'])
    summary={'rows':len(rows),'scenario_counts':{s:len(by[s]) for s in SCENARIOS},'gates':gates,'candidate_stale_effects':sum(r.get('final_effects',{}).get('B')=='G0' for r in by['SHARED_GLOBAL_CANDIDATE']),'surface_only_stale_effects':sum(r.get('final_effects',{}).get('B')=='G0' for r in by['SHARED_GLOBAL_SURFACE_ONLY'])}
    return summary,e

def validate(rows,result,audit,disposition,binding_errors):
    e=list(binding_errors);summary,row_errors=recompute(rows);e.extend(row_errors)
    if set(summary['gates'])!=GATE_NAMES or len(summary['gates'])!=7 or not all(summary['gates'].values()):e.append('scientific_gates')
    if result.get('rows')!=summary['rows'] or result.get('scenario_counts')!=summary['scenario_counts'] or result.get('gates')!=summary['gates'] or result.get('candidate_stale_effects')!=summary['candidate_stale_effects'] or result.get('surface_only_stale_effects')!=summary['surface_only_stale_effects']:e.append('result_summary')
    if summary['candidate_stale_effects']!=0 or summary['surface_only_stale_effects']!=3:e.append('stale_counts')
    if result.get('formal_invocations')!=1 or result.get('reruns')!=0 or result.get('replacements')!=0 or result.get('tuning')!=0:e.append('parent_allocation')
    if audit.get('decision')!='FAIL_INTEGRITY' or audit.get('errors')!=['gates'] or audit.get('pass') is not False:e.append('original_audit_identity')
    if disposition.get('scientific_disposition')!='FAIL_INTEGRITY_AUDIT_GATE_COUNT':e.append('parent_disposition')
    return sorted(set(e)),summary

def main():
    rows,result,audit,disposition,binding_errors=load_parent()
    errors,summary=validate(rows,result,audit,disposition,binding_errors)
    out={'task':'OPTIMISTIC-READWRITE-X11-RETAINED-AUDIT-A3-20260919-003','audit_invocations':1,'reruns':0,'parent_live_reruns':0,'parent_scientific_disposition':disposition.get('scientific_disposition'),'bound_hashes':EXPECTED,'recomputed':summary,'errors':errors,'decision':'PASS_RETAINED_OPTIMISTIC_X11_AUDIT_A3_SCOPED' if not errors else 'FAIL_A3_SCIENCE','pass':not errors}
    (ROOT/'RESULT_A3.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
