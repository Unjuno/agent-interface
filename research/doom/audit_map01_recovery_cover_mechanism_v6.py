"""V6 audit: unchanged V4 decision thresholds plus planner-boundary integrity."""
from __future__ import annotations
import argparse,json
from pathlib import Path

ALLOCATION_ID='map01-recovery-cover-mechanism-live-v6-01'
PHASE='immediately_after_delay_before_fallback_cleanup'

def audit(root:Path)->dict:
    import audit_map01_recovery_cover_mechanism_v4 as base
    old=base.ALLOCATION_ID
    try:
        base.ALLOCATION_ID=ALLOCATION_ID
        result=dict(base.audit(Path(root)))
    finally:
        base.ALLOCATION_ID=old
    boundary_failures=[]
    for i in (1,2,3):
        for arm in ('coast_control','bounded_recovery'):
            p=Path(root)/f'pair-{i:02d}'/arm/'arm-summary.json'
            try: row=json.loads(p.read_text(encoding='utf-8'))
            except Exception as exc:
                boundary_failures.append(f'pair{i}:{arm}:planner_boundary_missing:{type(exc).__name__}');continue
            window=row.get('planner_window') or {}
            if window.get('end_boundary_phase')!=PHASE:
                boundary_failures.append(f'pair{i}:{arm}:planner_end_phase')
            duration=window.get('duration_ns')
            if type(duration) is not int or duration<=0:
                boundary_failures.append(f'pair{i}:{arm}:planner_window_duration')
    if boundary_failures:
        result['hard_failures']=list(result.get('hard_failures') or [])+boundary_failures
        result['decision']='FAIL';result['valid_experiment']=False;result['promotable_mechanism_result']=False
    result['schema']='map01-recovery-cover-mechanism-v6-audit';result['allocation_id']=ALLOCATION_ID
    result['planner_boundary_failures']=boundary_failures
    result['harness_change']='planner end sampled immediately after delay and before cleanup; v5 event preservation retained; V4 scientific thresholds unchanged'
    return result

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();r=audit(a.root)
    text=json.dumps(r,indent=2,sort_keys=True)+'\n';print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
    return 0 if r.get('valid_experiment') is True else 1
if __name__=='__main__':raise SystemExit(main())
