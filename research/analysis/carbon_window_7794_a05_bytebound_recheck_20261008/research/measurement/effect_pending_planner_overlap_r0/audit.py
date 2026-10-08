#!/opt/pyvenv/bin/python3
"""Independent retained-result audit for Issue #1616."""
import argparse,json,pathlib

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--corruption',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(pathlib.Path(a.result).read_text())
    c=json.loads(pathlib.Path(a.corruption).read_text())
    errors=[]
    expected_traces=sum(8**k for k in range(6))
    if r.get('event_count') != 8: errors.append('event_count')
    if r.get('max_len') != 5: errors.append('max_len')
    if r.get('trace_count') != expected_traces: errors.append('trace_count')
    if r.get('mismatch_count') != 0 or r.get('mismatches') != []: errors.append('candidate_oracle_mismatch')
    if r.get('invariant_error_count') != 0 or r.get('invariant_errors') != []: errors.append('invariant_violation')
    hist=r.get('state_histogram',{})
    if sum(hist.values()) != expected_traces: errors.append('histogram_total')
    required_states=(
        'tracked:pending:True:False',
        'tracked:resolved:True:False',
        'tracked:unresolved:True:False',
        'tracked:pending:False:False',
        'needs_reconciliation:unknown:False:False',
    )
    for state in required_states:
        if hist.get(state,0) <= 0: errors.append('missing_state:'+state)
    if c.get('pass_count') != 5 or c.get('total') != 5 or not all(c.get('passed',{}).values()): errors.append('corruption_controls')
    term=c.get('controls',{}).get('terminal_not_effect',{})
    if not (term.get('client_can_resume_reasoning') is True and term.get('task_effect_status')=='pending' and term.get('task_effect_resolved') is False and term.get('current_input_authority') is False and term.get('new_input_admissible') is False):
        errors.append('terminal_effect_separation')
    out={'audit_pass':not errors,'errors':errors,'expected_trace_count':expected_traces,
         'decision':'PASS_EFFECT_PENDING_PLANNER_OVERLAP_MODEL_SCOPED' if not errors else 'FAIL_EFFECT_PENDING_STATE_MODEL'}
    pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True))
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if not errors else 1)

if __name__=='__main__': main()
