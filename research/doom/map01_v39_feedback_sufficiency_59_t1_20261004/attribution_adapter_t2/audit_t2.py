"""Independent raw-result audit for producer-composition T2."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; RUN=ROOT/'run'
result=json.loads((RUN/'candidate.json').read_text(encoding='utf-8'))
inputs=json.loads((RUN/'input-records.json').read_text(encoding='utf-8'))
samples=[json.loads(x) for x in (RUN/'scorer/scorer-samples.jsonl').read_text(encoding='utf-8').splitlines() if x]
events=[json.loads(x) for x in (RUN/'scorer/scorer-events.jsonl').read_text(encoding='utf-8').splitlines() if x]
assert result['schema']=='v15-attribution-adapter-t2-result-v1'
assert len(samples)==2 and all(x.get('controller_visible') is False for x in samples)
assert [x['payload']['schema'] for x in samples]==['independent-progress-sample-v2']*2
assert len(events)==1 and events[0]['schema']=='independent-progress-event-v2'
assert events[0]['controller_visible'] is False and events[0]['observed_ns']==samples[1]['payload']['sample_ns']
expect={'single_verified':('SOURCE_ROWS_JOINED','TEMPORALLY_UNIQUE','intent-a'),
        'overlapping':('SOURCE_ROWS_JOINED','AMBIGUOUS',None),
        'mismatched_release':('HOLD_UNMATCHED_RELEASE_IDENTITY','UNRESOLVED',None),
        'unverified_release':('SOURCE_ROWS_JOINED','UNRESOLVED',None),
        'incomplete_release_batch':('HOLD_INCOMPLETE_RELEASE_BATCH','UNRESOLVED',None),
        'unbound_admission':('HOLD_UNBOUND_INPUT_IDENTITY','UNRESOLVED',None)}
assert set(result['scenarios'])==set(expect)==set(inputs)
for name,(integrity,status,token) in expect.items():
    scenario=result['scenarios'][name]
    assert scenario['trace_integrity']==integrity,(name,scenario['trace_integrity'])
    assert len(scenario['attributions'])==1,(name,scenario['attributions'])
    row=scenario['attributions'][0]
    assert (row['status'],row['intent_token'])==(status,token),(name,row)
    assert row['causal_attribution']=='NOT_ESTABLISHED',(name,row)
print(json.dumps({'audit':'PASS_V15_PRODUCER_COMPOSITION_SCOPED','sample_rows':len(samples),
                  'positive_events':len(events),'scenario_count':len(expect),'errors':[]},indent=2,sort_keys=True))
