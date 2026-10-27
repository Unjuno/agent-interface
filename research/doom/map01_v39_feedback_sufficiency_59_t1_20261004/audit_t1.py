"""Independent raw-only sufficiency audit; does not import the candidate."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read():
    report=json.loads((ROOT/'inputs/report.json').read_bytes())
    trace=[json.loads(x) for x in (ROOT/'inputs/events.jsonl').read_text(encoding='utf-8').splitlines() if x]
    owner=json.loads((ROOT/'inputs/owner-events.json').read_bytes())
    holds=json.loads((ROOT/'inputs/occupancy-v39.json').read_bytes())['holds']
    return report,trace,owner,holds

def main():
    report,trace,owner,holds=read()
    sample_rows=[x for x in trace if x.get('schema')=='independent-progress-sample-v2']
    event_rows=[x for x in trace if x.get('schema')=='independent-progress-event-v2']
    per_key_rows=[x for x in trace if isinstance(x.get('key'),str) and isinstance(x.get('intent_token'),str) and type(x.get('admitted_ns')) is int and type(x.get('release_sync_ns')) is int and x.get('release_verified') is True]
    type_counts={}
    for x in trace:
        t=x.get('event','<missing>'); type_counts[t]=type_counts.get(t,0)+1
    receipt_scope_counts={}
    for d in report.get('decisions',[]):
        for x in d.get('effect_receipts',[]):
            s=x.get('scope','<missing>'); receipt_scope_counts[s]=receipt_scope_counts.get(s,0)+1
    admissions=[x for x in trace if x.get('event')=='input_admission']
    owner_key_release_rows=[x for x in owner if isinstance(x.get('key'),str) and x.get('verified') is True]
    terminal=[x for x in trace if x.get('event')=='post_control_score']
    assert len(trace)==634
    assert len(admissions)==39 and all('intent_token' not in x and 'release_sync_ns' not in x for x in admissions)
    assert len(sample_rows)==0 and len(event_rows)==0 and len(per_key_rows)==0
    assert len(terminal)==1 and 'emit_ns' in terminal[0] and 'sample_sequence' not in terminal[0]
    assert len(holds)==29
    assert sum(receipt_scope_counts.values())==4 and receipt_scope_counts=={'viewport pixels only':4}
    assert len(owner)==13 and not owner_key_release_rows
    print(json.dumps({'audit':'PASS_DATA_SUFFICIENCY_HOLD','runtime_event_type_counts':type_counts,'receipt_scope_counts':receipt_scope_counts,'independent_samples':len(sample_rows),'independent_events':len(event_rows),'explicit_complete_per_key_intervals':len(per_key_rows),'input_admissions_without_intent_or_release_fields':len(admissions),'verified_owner_releases_without_key_identity':len(owner),'terminal_scores_without_sample_sequence':len(terminal),'occupancy_hold_rows':len(holds),'errors':[]},sort_keys=True,indent=2))
if __name__=='__main__': main()
