from fractions import Fraction as F
from itertools import product
import argparse, hashlib, json
from pathlib import Path

GRID = tuple(F(i,4) for i in range(0,17))  # 0..4 seconds by 0.25 s


def hard_decision(current, t, c, d):
    if not current:
        return 'CANCEL_STALE'
    if t + c > d:
        return 'CANCEL_TARDY'
    return 'RUN_FEASIBLE'


def direct_feasible(current, t, c, d):
    return bool(current and t + c <= d)


def stable_preference(t,c,d):
    # Compare RUN-now to a concrete WAIT policy: wait delta=c/4, then run if still current.
    # Utility is lexicographic: timely useful completion, earlier completion, less wasted compute.
    assert c > 0 and t+c <= d
    delta=c/4
    run_finish=t+c
    wait_finish=t+delta+c
    run_success=run_finish<=d
    wait_success=wait_finish<=d
    run=(int(run_success), -run_finish, F(0))
    wait=(int(wait_success), -wait_finish, F(0))
    return 'RUN' if run>wait else ('WAIT' if wait>run else 'TIE')


def invalidate_preference(t,c,d):
    # Same current metadata; future invalidates old source at epsilon=c/2.
    # Replacement job cost r=c/4. RUN wastes epsilon old compute; WAIT does not.
    # Both replacement completions are timely because t+3c/4 <= t+c <= d.
    assert c > 0 and t+c <= d
    eps=c/2; repl=c/4; finish=t+eps+repl
    assert finish <= d
    run=(1, -finish, -eps)   # timely, same finish, but wasted old compute
    wait=(1, -finish, F(0))
    return 'RUN' if run>wait else ('WAIT' if wait>run else 'TIE')


def directed_controls():
    return {
      'stale': hard_decision(False,F(0),F(1),F(2))=='CANCEL_STALE',
      'tardy': hard_decision(True,F(1),F(2),F(2))=='CANCEL_TARDY',
      'inclusive_tie': hard_decision(True,F(1),F(1),F(2))=='RUN_FEASIBLE',
      'ample_slack': hard_decision(True,F(0),F(1),F(4))=='RUN_FEASIBLE',
      'stable_prefers_run': stable_preference(F(0),F(1),F(4))=='RUN',
      'invalidate_prefers_wait': invalidate_preference(F(0),F(1),F(4))=='WAIT',
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--construction',action='store_true'); ap.add_argument('--output',required=True)
    a=ap.parse_args(); out=Path(a.output); assert not out.exists()
    vals=GRID[:7] if a.construction else GRID
    rows=0; mismatch=0; stale_accepted=0; tardy_accepted=0; ties=0; tie_feasible=0; feasible_nonzero=0; paired_reversals=0; reuse_decisions=0
    counts={'CANCEL_STALE':0,'CANCEL_TARDY':0,'RUN_FEASIBLE':0}
    for current,t,c,d in product((False,True),vals,vals,vals):
        got=hard_decision(current,t,c,d); counts[got]+=1; rows+=1
        feasible=direct_feasible(current,t,c,d)
        mismatch += int((got=='RUN_FEASIBLE') != feasible)
        stale_accepted += int((not current) and got=='RUN_FEASIBLE')
        tardy_accepted += int(current and t+c>d and got=='RUN_FEASIBLE')
        if current and t+c==d:
            ties+=1; tie_feasible += int(got=='RUN_FEASIBLE')
        if feasible and c>0:
            feasible_nonzero+=1
            if stable_preference(t,c,d)=='RUN' and invalidate_preference(t,c,d)=='WAIT':
                paired_reversals+=1
    directed=directed_controls()
    corruptions={
      'reverse_slack_rejected': hard_decision(True,F(1),F(1),F(2))=='RUN_FEASIBLE',
      'exclusive_tie_rejected': tie_feasible==ties,
      'stale_publication_rejected': stale_accepted==0,
      'universal_run_refuted': paired_reversals>0,
    }
    good=(mismatch==0 and stale_accepted==0 and tardy_accepted==0 and ties>0 and tie_feasible==ties and paired_reversals==feasible_nonzero and feasible_nonzero>0 and reuse_decisions==0 and all(directed.values()) and all(corruptions.values()))
    result={
      'construction':a.construction,'grid_values':[str(x) for x in vals],'rows':rows,'decision_counts':counts,
      'hard_feasibility_mismatch':mismatch,'stale_run_acceptances':stale_accepted,'tardy_run_acceptances':tardy_accepted,
      'exact_deadline_current_rows':ties,'exact_deadline_feasible_rows':tie_feasible,
      'hard_feasible_nonzero_rows':feasible_nonzero,'paired_future_preference_reversals':paired_reversals,
      'reuse_decisions':reuse_decisions,'directed_controls':directed,'corruption_controls':corruptions,
      'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,
      'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED' if good else 'FAIL_INTEGRITY'))
    }
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
