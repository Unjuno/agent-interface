from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

PASS='PASS_X11_ACTION_GUARD_ROI_COST_SCOPED'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def invariant_errors(r):
    e=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0: e.append('invocation/rerun')
    if r.get('authority_actions')!=0: e.append('authority')
    if r.get('exceptions'): e.append('exceptions')
    c=r.get('cleanup',{})
    if not c.get('fixture_exit') or not c.get('xvfb_exit'): e.append('cleanup')
    s=r.get('summary',{}); f=s.get('FULL_FRAME_GUARD',{}); q=s.get('ROI_GUARD',{}); m=s.get('matched',{})
    if f.get('cases')!=24 or q.get('cases')!=24 or f.get('cases_completed')!=24 or q.get('cases_completed')!=24: e.append('case completeness')
    if f.get('nonoverlap_mismatch')!=0 or q.get('nonoverlap_mismatch')!=0: e.append('classification mismatch')
    if f.get('hard_invalid_effects')!=0 or q.get('hard_invalid_effects')!=0: e.append('hard stale effect')
    if f.get('ambiguous_effects')!=0 or q.get('ambiguous_effects')!=0: e.append('ambiguous effect')
    if q.get('guard_duration_p95_ns',10**18)>=1_000_000: e.append('roi p95')
    if q.get('guard_duration_p99_ns',10**18)>=2_000_000: e.append('roi p99')
    if m.get('roi_full_p95_ratio',9)>0.50: e.append('ratio')
    if q.get('hard_invalidation_to_stop_p95_ns',10**18)>10_000_000: e.append('stop p95')
    if q.get('action_start_lag_p95_ns',10**18)>2_500_000 or q.get('action_start_lag_max_ns',10**18)>10_000_000: e.append('schedule lag')
    if not m.get('roi_all_pairs_fewer_bytes',False): e.append('bytes')
    if f.get('host_noise_cases',99)>2 or q.get('host_noise_cases',99)>2: e.append('host noise')
    if r.get('decision')!=PASS: e.append('decision')
    return e

def mutation_controls(result):
    controls={}
    muts={}
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']['ambiguous_effects']=1; muts['ambiguous_is_valid']=a
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']['hard_invalid_effects']=1; muts['ignore_hard']=a
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']['nonoverlap_mismatch']=1; muts['reuse_previous_guard_state']=a
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']['hard_invalidation_to_stop_p95_ns']=99_000_000; muts['corrupt_fixture_timing']=a
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']=copy.deepcopy(a['summary']['FULL_FRAME_GUARD']); a['summary']['matched']['roi_full_p95_ratio']=1.0; a['summary']['matched']['roi_all_pairs_fewer_bytes']=False; muts['copy_full_metrics_into_roi']=a
    a=copy.deepcopy(result); a['summary']['ROI_GUARD']['nonoverlap_mismatch']=3; muts['swap_fingerprints']=a
    for name,m in muts.items(): controls[name]={'detected':bool(invariant_errors(m)),'errors':invariant_errors(m)}
    return controls

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--freeze',type=Path,required=True); ap.add_argument('--result',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    fr=json.loads(a.freeze.read_text()); r=json.loads(a.result.read_text()); errors=[]
    for rel,expected in fr['source_sha256'].items():
        actual=sha(a.root/rel)
        if actual!=expected: errors.append(f'source hash {rel}')
    errors.extend(invariant_errors(r)); controls=mutation_controls(r)
    for n,c in controls.items():
        if not c['detected']: errors.append(f'mutation undetected {n}')
    out={'task':r.get('task'),'result_sha256':sha(a.result),'pass':not errors,'errors':errors,'source_integrity':not any(x.startswith('source hash') for x in errors),'mutation_controls':controls}
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps({'pass':out['pass'],'errors':errors,'result_sha256':out['result_sha256']},sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
