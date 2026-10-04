from pathlib import Path
import json
r=Path(__file__).resolve().parent/'controller-visual-03'
samples=[json.loads(x)['payload'] for x in (r/'episode/runtime/scorer-samples.jsonl').read_bytes().splitlines()]
i=next(i for i,s in enumerate(samples) if s['kill_count']==1)
before,after=samples[i-1:i+1]
lo,hi=before['sample_ns'],after['sample_ns']
rows=[json.loads(x) for x in (r/'episode/runtime/events.jsonl').read_bytes().splitlines()]
holds=[]
for row in rows:
 if row.get('event')!='keys_held':continue
 endings=[x for x in rows if x.get('event')=='input_release_transition' and x.get('id')==row['id'] and x.get('step')==row['step'] and x.get('key') in row['keys']]
 if not endings:continue
 end=max(x['release_call_returned_ns'] for x in endings)
 start=row['input_ack_ns']
 if start<=hi and end>=lo:holds.append({'id':row['id'],'step':row['step'],'keys':row['keys'],'ack_ns':start,'last_up_return_ns':end})
result={'scope':'saved-only temporal overlap, not causal attribution or exact game-event onset','last_zero':before,'first_one':after,'detection_bracket_ns':[lo,hi],'detection_bracket_width_ms':(hi-lo)/1e6,'overlapping_ack_to_release_holds':holds,'disposition':'HOLD_CAUSAL_INPUT_ATTRIBUTION; HOLD_POST_INVALIDATION_RECOVERY','limits':['sample timestamps are client observations, not authoritative engine kill timestamps','delayed effects from earlier firing not excluded','no policy invalidation in this episode','keys_held ack aggregates keys; no physical per-key timestamp certificate']}
(r/'SAVED_INTERVAL_AUDIT.json').write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps(result))
