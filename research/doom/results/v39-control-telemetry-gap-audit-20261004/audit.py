from pathlib import Path
import collections, hashlib, json
HERE=Path(__file__).resolve().parent
PINS={
 'events.jsonl':'2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381',
 'owner-events.json':'cdf628825312e6eb0cd810f7d0b3a77e52c1c2f646099bc07a34b4e3a90c08b7',
 'sources.json':'3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8',
}
def digest(data): return hashlib.sha256(data).hexdigest()
def main():
 raw={name:(HERE/name).read_bytes() for name in PINS}
 for name,want in PINS.items():
  got=digest(raw[name])
  if got!=want: raise SystemExit(f'STOP_INPUT_HASH:{name}:{got}')
 events=[json.loads(line) for line in raw['events.jsonl'].splitlines() if line]
 owners=json.loads(raw['owner-events.json'])
 sources=json.loads(raw['sources.json'])
 counts=collections.Counter(row.get('event','<missing>') for row in events)
 admissions=[row for row in events if row.get('event')=='input_admission']
 held=[row for row in events if row.get('event')=='keys_held']
 released=[row for row in events if row.get('event')=='input_released']
 owner_release=[row for row in owners if row.get('event')=='owner_release']
 keyup_names={'input_up','key_up','key_release','input_release_transition','owner_keyup','owner_key_release_bracket'}
 keyup_events=[row for row in events if row.get('event') in keyup_names]
 keyup_owner=[row for row in owners if row.get('event') in keyup_names]
 result={
  'schema':'v39-control-telemetry-gap-audit-v1','status':'PASS_RAW_SCHEMA_INVENTORY_SCOPED',
  'source_main':'0ba1ef384965267c38a120f61977953636220fd3',
  'inputs':{name:{'sha256':digest(raw[name]),'bytes':len(raw[name])} for name in PINS},
  'events':{'count':len(events),'counts':dict(sorted(counts.items()))},
  'per_key_admission':{'count':len(admissions),'all_have_key':all(type(row.get('key')) is str for row in admissions),'all_have_admission_and_ack_clocks':all(type(row.get('admitted_ns')) is int and type(row.get('input_ack_ns')) is int for row in admissions),'rows_with_intent_token':sum('intent_token' in row for row in admissions),'rows_with_program_id':sum('id' in row for row in admissions),'rows_with_step_index':sum('step' in row for row in admissions)},
  'aggregate_hold_acknowledgements':{'count':len(held),'all_have_program_and_step':all(type(row.get('id')) is str and type(row.get('step')) is int for row in held),'all_have_keys_and_ack_clock':all(isinstance(row.get('keys'),list) and type(row.get('input_ack_ns')) is int for row in held)},
  'explicit_input_released_events':{'count':len(released),'verified_empty_owner_receipts':sum(row.get('owner_release',{}).get('verified') is True and row.get('owner_release',{}).get('keys_down')==[] and row.get('owner_release',{}).get('buttons_down')==[] for row in released)},
  'owner_release_records':{'count':len(owner_release),'verified_empty_count':sum(row.get('verified') is True and row.get('keys_down')==[] and row.get('buttons_down')==[] for row in owner_release),'per_key_release_brackets':sum(row.get('event')=='owner_key_release_bracket' for row in owners)},
  'direct_key_up_or_per_key_release_events':{'event_stream_count':len(keyup_events),'owner_stream_count':len(keyup_owner)},
  'observations':{'count':sum(row.get('event')=='observation' for row in events),'semantic_completion_values':dict(sorted(collections.Counter(str(row.get('semantic_completion')) for row in events if row.get('event')=='observation').items()))},
  'runtime_source_pins':{'input_owner_v10.py':sources.get('live_control/input_owner_v10.py'),'doom_typed_release_backend_v1.py':sources.get('doom/doom_typed_release_backend_v1.py')},
  'limits':['Per-key admission timing does not establish a per-key up time.','Aggregate verified-empty owner state is not an exact per-key transition timestamp.','Observation/image change is not independently useful task feedback.','No physical keyboard state, application effect, recovery efficacy, or live outcome is inferred.']}
 if len(events)!=634 or len(admissions)!=39 or len(held)!=28 or len(owner_release)!=13: raise SystemExit('STOP_EXPECTED_INVENTORY')
 if not all(type(row.get('key')) is str and type(row.get('admitted_ns')) is int and type(row.get('input_ack_ns')) is int for row in admissions): raise SystemExit('STOP_ADMISSION_SHAPE')
 if any(('intent_token' in row or 'id' in row or 'step' in row) for row in admissions): raise SystemExit('STOP_ADMISSION_IDENTITY_CHANGED')
 if not all(type(row.get('id')) is str and type(row.get('step')) is int and isinstance(row.get('keys'),list) and type(row.get('input_ack_ns')) is int for row in held): raise SystemExit('STOP_HELD_ACK_SHAPE')
 if result['owner_release_records']['verified_empty_count']!=13 or keyup_events or keyup_owner: raise SystemExit('STOP_RELEASE_SHAPE_CHANGED')
 if result['observations']['semantic_completion_values']!={'unknown':218}: raise SystemExit('STOP_FEEDBACK_SHAPE_CHANGED')
 (HERE/'audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'events':len(events),'input_admission':len(admissions),'keys_held':len(held),'owner_release':len(owner_release),'direct_key_up_events':len(keyup_events)+len(keyup_owner),'observation_semantics':result['observations']['semantic_completion_values']},sort_keys=True))
if __name__=='__main__': main()
