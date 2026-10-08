from __future__ import annotations
import argparse,copy,json,statistics
from pathlib import Path

def pct(vals,p):
    xs=sorted(vals);return None if not xs else xs[max(0,min(len(xs)-1,int((len(xs)-1)*p)))]

def evaluate(r):
    errors=[];cases=r.get('cases',[])
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0:errors.append('invocation')
    if r.get('pairs')!=24 or len(cases)!=48:errors.append('case_count')
    if r.get('authority_actions')!=0 or r.get('task_input_actions')!=0 or r.get('xtest_actions')!=0:errors.append('authority_or_input')
    ws=[c for c in cases if c.get('arm')=='WAIT_FOR_PLANNER'];ks=[c for c in cases if c.get('arm')=='CACHED_POLICY_XTERM_GUARD']
    if len(ws)!=24 or len(ks)!=24:errors.append('arm_count')
    guards=[];stops=[];progress=[]
    for c in cases:
        if c.get('exceptions'):errors.append(f"case{c.get('case_id')}_exception")
        cl=c.get('cleanup',{})
        if not (cl.get('xterm_exit') and cl.get('xvfb_exit') and cl.get('socket_residual') is False):errors.append(f"case{c.get('case_id')}_cleanup")
        w=c.get('window',{})
        if not w.get('mapped') or w.get('roi')!=[0,0,180,20]:errors.append(f"case{c.get('case_id')}_window")
        if len(c.get('fingerprints',{}))!=2:errors.append(f"case{c.get('case_id')}_fingerprint")
        if c.get('fixture_progress_delta')!=c.get('accepted_valid_effects'):errors.append(f"case{c.get('case_id')}_progress_oracle")
        if c.get('hard_accepted_effects',0)!=0:errors.append(f"case{c.get('case_id')}_hard_effect")
        if c.get('post_terminal_commands',0)!=0:errors.append(f"case{c.get('case_id')}_post_terminal")
        if c.get('nonoverlap_mismatch',0)!=0:errors.append(f"case{c.get('case_id')}_roi_mismatch")
        if c.get('semantic_decisions_during_gap')!=0:errors.append(f"case{c.get('case_id')}_semantic")
        if c.get('arm')=='WAIT_FOR_PLANNER':
            if c.get('verified_progress_during_gap')!=0 or c.get('accepted_effects')!=0:errors.append(f"case{c.get('case_id')}_wait_effect")
        else:
            progress.append(c.get('verified_progress_during_gap',0));guards.extend(c.get('guards',[]))
            if c.get('hard_invalidation_to_stop_ns') is not None:stops.append(c['hard_invalidation_to_stop_ns'])
    for pid in range(24):
        w=next((x for x in ws if x.get('pair_id')==pid),None);k=next((x for x in ks if x.get('pair_id')==pid),None)
        if w is None or k is None or k.get('verified_progress_during_gap',0)<=w.get('verified_progress_during_gap',0):errors.append(f'pair{pid}_progress')
    gd=[g['guard_duration_ns'] for g in guards];lags=[g['action_start_lag_ns'] for g in guards]
    metrics={'cached_progress_median':statistics.median(progress) if progress else None,'stop_p95_ns':pct(stops,.95),'stop_max_ns':max(stops) if stops else None,'roi_p95_ns':pct(gd,.95),'roi_p99_ns':pct(gd,.99),'action_lag_p95_ns':pct(lags,.95),'action_lag_max_ns':max(lags) if lags else None}
    if not errors:
        useful=metrics['cached_progress_median']>=4
        safe=metrics['stop_p95_ns'] is not None and metrics['stop_p95_ns']<=10_000_000 and metrics['stop_max_ns']<=15_000_000
        cost=metrics['roi_p95_ns']<1_500_000 and metrics['roi_p99_ns']<3_000_000 and metrics['action_lag_p95_ns']<=3_000_000 and metrics['action_lag_max_ns']<=12_000_000
        if not safe or not cost:return 'HOLD_XTERM_EVIDENCE_TOO_SLOW',errors,metrics
        if not useful:return 'HOLD_NO_USEFUL_REUSE_WINDOW',errors,metrics
        return 'PASS_DECISION_POLICY_CACHE_XTERM_TRANSFER_SCOPED',errors,metrics
    if any('hard_effect' in e or 'post_terminal' in e or 'roi_mismatch' in e for e in errors):return 'FAIL_CACHE_STALENESS_XTERM',errors,metrics
    return 'FAIL_INTEGRITY',errors,metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());decision,errors,metrics=evaluate(r)
    controls={}
    muts=[
      ('hard_effect',lambda x:x['cases'][next(i for i,c in enumerate(x['cases']) if c.get('arm')=='CACHED_POLICY_XTERM_GUARD')].__setitem__('hard_accepted_effects',1)),
      ('post_terminal',lambda x:x['cases'][next(i for i,c in enumerate(x['cases']) if c.get('arm')=='CACHED_POLICY_XTERM_GUARD')].__setitem__('post_terminal_commands',1)),
      ('wait_progress',lambda x:x['cases'][next(i for i,c in enumerate(x['cases']) if c.get('arm')=='WAIT_FOR_PLANNER')].__setitem__('verified_progress_during_gap',1)),
      ('cleanup',lambda x:x['cases'][0]['cleanup'].__setitem__('socket_residual',True)),
      ('authority',lambda x:x.__setitem__('authority_actions',1)),
      ('progress_oracle',lambda x:x['cases'][0].__setitem__('fixture_progress_delta',999)),
      ('invocation',lambda x:x.__setitem__('formal_invocations',2)),
    ]
    for name,fn in muts:
        q=copy.deepcopy(r);fn(q);d,e,m=evaluate(q);controls[name]=d!='PASS_DECISION_POLICY_CACHE_XTERM_TRANSFER_SCOPED'
    if not all(controls.values()):errors.append('corruption_control')
    out={'task':r.get('task'),'decision':decision,'pass':decision=='PASS_DECISION_POLICY_CACHE_XTERM_TRANSFER_SCOPED','errors':errors,'metrics':metrics,'corruption_controls':controls,'corruption_passed':sum(controls.values()),'corruption_total':len(controls)}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
