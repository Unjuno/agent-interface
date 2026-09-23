from __future__ import annotations
import json
from pathlib import Path

EXPECTED_1100='PASS_P0_CURRENT_GAP_LOCALIZED_SCOPED'
EXPECTED_1276='PASS_INPUT_OWNER_V12_LIVE_CAUSAL_X11_SCOPED'

def evaluate(f):
    errors=[]
    p=f['parent_1100']; r=f['live_1276']
    if p.get('decision')!=EXPECTED_1100: errors.append('parent_1100_decision')
    if p.get('remaining_live_gates')!=['LIVE_PHYSICAL_EDGE_TRANSFER','LIVE_CAUSAL_EFFECT_SAMPLE']: errors.append('parent_gate_shape')
    if r.get('decision')!=EXPECTED_1276: errors.append('live_1276_decision')
    if (r.get('formal_invocations'),r.get('reruns'))!=(1,0): errors.append('live_invocation')
    if (r.get('sessions'),r.get('baseline_application_ok'),r.get('candidate_application_ok'),r.get('terminal_up'),r.get('candidate_physical_composed'),r.get('exceptions'))!=(12,6,6,12,6,0): errors.append('live_endpoints')
    if r.get('evidence_class')!='LIVE_PHYSICAL_RECEIPT': errors.append('live_class')
    if r.get('is_live_task_effect') is not False: errors.append('effect_class_collapse')
    physical='PROVEN_LIVE_SCOPED' if not errors else 'UNRESOLVED'
    effect='UNPROVEN_CURRENT'
    same_process_live_useful=False
    cross_process_live_useful=False
    cross_clock_required=True
    decision='PASS_P0_ONLY_LIVE_CAUSAL_EFFECT_REMAINS_SCOPED' if not errors else 'FAIL_EVIDENCE_CLASS_INTEGRITY'
    return {'task':f['task'],'decision':decision,'errors':errors,'formal_invocations':1,'reruns':0,'LIVE_PHYSICAL_EDGE_TRANSFER':physical,'LIVE_CAUSAL_EFFECT_SAMPLE':effect,'same_process_live_useful_control_proven':same_process_live_useful,'cross_process_live_useful_control_proven':cross_process_live_useful,'cross_process_clock_axis_required':cross_clock_required,'cross_process_clock_axis_proven':bool(f.get('cross_process_clock_axis_proven')),'next_gate_count':1 if not errors else None}

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('facts');ap.add_argument('--out',required=True);a=ap.parse_args()
    f=json.loads(Path(a.facts).read_text()); out=evaluate(f)
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__': main()
