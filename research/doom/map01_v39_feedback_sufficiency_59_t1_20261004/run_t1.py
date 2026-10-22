"""One-shot application of the frozen attribution gate to retained v39 data."""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
from scorer_feedback_attribution_v1 import SAMPLE_SCHEMA, EVENT_SCHEMA, attribute_positive_events
ROOT = Path(__file__).resolve().parent

def load_inputs():
    report=json.loads((ROOT/'inputs/report.json').read_text(encoding='utf-8'))
    events=[json.loads(line) for line in (ROOT/'inputs/events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    owners=json.loads((ROOT/'inputs/owner-events.json').read_text(encoding='utf-8'))
    occupancy=json.loads((ROOT/'inputs/occupancy-v39.json').read_text(encoding='utf-8'))
    return report,events,owners,occupancy

def analyze(report, events, owners, occupancy):
    # Only producer records already carrying the exact T0 schemas qualify.
    scorer_samples=[e for e in events if e.get('schema') == SAMPLE_SCHEMA]
    scorer_events=[e for e in events if e.get('schema') == EVENT_SCHEMA]
    receipt_rows=[r for d in report.get('decisions',[]) for r in d.get('effect_receipts',[])]
    pixel_only=[r for r in receipt_rows if r.get('scope') == 'viewport pixels only']
    typed=[e for e in events if e.get('event') == 'typed_observation']
    admissions=[e for e in events if e.get('event') == 'input_admission']
    held=[e for e in events if e.get('event') == 'keys_held']
    releases=[e for e in events if e.get('event') == 'input_released']
    per_key_complete=[]
    for e in events:
        if (isinstance(e.get('intent_token'),str) and isinstance(e.get('key'),str)
            and type(e.get('admitted_ns')) is int and type(e.get('release_sync_ns')) is int
            and e.get('release_verified') is True):
            per_key_complete.append(e)
    terminal_scores=[e for e in events if e.get('event') == 'post_control_score']
    gate_output=attribute_positive_events(scorer_samples,scorer_events,per_key_complete)
    admission_missing_identity=sum(not all(k in e for k in ('id','step','intent_token')) for e in admissions)
    admission_missing_release=sum(not all(k in e for k in ('release_sync_ns','release_verified')) for e in admissions)
    owner_per_key=sum(isinstance(e.get('key'),str) and type(e.get('verified_ns')) is int for e in owners)
    hold_rows=occupancy.get('holds',[])
    return {
      'schema':'map01-v39-feedback-sufficiency-t1-v1',
      'input_counts':{'runtime_event_rows':len(events),'typed_observation_rows':len(typed),'input_admission_rows':len(admissions),'keys_held_rows':len(held),'input_released_rows':len(releases),'verified_owner_release_rows':sum(e.get('event')=='owner_release' and e.get('verified') is True for e in owners),'occupancy_hold_rows':len(hold_rows),'effect_receipt_rows':len(receipt_rows),'pixel_only_receipt_rows':len(pixel_only),'post_control_score_rows':len(terminal_scores)},
      'qualifying_data':{'independent_scorer_samples':len(scorer_samples),'independent_scorer_events':len(scorer_events),'complete_explicit_per_key_intervals':len(per_key_complete),'per_key_owner_release_rows':owner_per_key},
      'gate_invocation':{'invoked':True,'output_rows':len(gate_output),'output':gate_output,'disposition':'NOT_EVALUABLE_NO_INPUT_EVENTS' if not scorer_samples or not scorer_events or not per_key_complete else 'EVALUATED'},
      'observed_gaps':{'input_admissions_without_id_step_intent_token':admission_missing_identity,'input_admissions_without_per_key_verified_release':admission_missing_release,'controller_visible_typed_observations_excluded':len(typed),'pixel_only_receipts_excluded':len(pixel_only),'terminal_score_has_timestamped_progress_sample':sum(type(e.get('sample_sequence')) is int for e in terminal_scores)},
      'terminal_score':[{k:e.get(k) for k in ('emit_ns','map_exit','episode_finished','player_dead','death_count','kill_count','reward')} for e in terminal_scores],
      'disposition':'HOLD_NO_INDEPENDENT_FEEDBACK_STREAM' if not scorer_samples or not scorer_events else 'INPUTS_AVAILABLE_REQUIRES_ATTRIBUTION',
      'per_key_disposition':'HOLD_NO_COMPLETE_EXPLICIT_PER_KEY_RELEASE_INTERVALS' if not per_key_complete else 'INPUTS_AVAILABLE_REQUIRES_ATTRIBUTION',
      'interpretation':'The retained record supports terminal task outcome and per-key admission events, but has no independently sampled positive feedback stream using T0 schemas and no explicit verified per-key release interval rows. Controller-visible health/ammo and viewport-only pixel receipts were not promoted. No event-to-intent attribution was attempted.'
    }

def main():
    result=analyze(*load_inputs())
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=='__main__': main()
