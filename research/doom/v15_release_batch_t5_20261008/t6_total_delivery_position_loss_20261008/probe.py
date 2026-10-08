import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent / 'package'
sys.path.insert(0,str(PACKAGE))
from adapter import adapt_session_records
from test_delivery_batches import sample, event, row

def build(delivery):
    first=row('input_release_transition','space',0); first.update(release_batch_size=2,release_batch_position=0)
    second=row('input_release_transition','up',1); second.update(release_batch_size=2,release_batch_position=1)
    rows=[row('input_admission','space'),first,row('input_admission','up'),second]
    if not delivery:
        for item in rows:
            if item.get('event')=='input_release_transition': item.pop('release_batch_delivery_position',None)
    return rows

def run(rows):
    return adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
current=build(True)
legacy=build(False)
result={'schema':'v15-t6-schema-loss-identifiability-v1',
 'comparison':{'current_rows_have_positions':all('release_batch_delivery_position' in r for r in current if r.get('event')=='input_release_transition'),
 'legacy_rows_omit_positions':all('release_batch_delivery_position' not in r for r in legacy if r.get('event')=='input_release_transition'),
 'positions_deleted_current_equals_legacy':[{k:v for k,v in r.items() if k!='release_batch_delivery_position'} for r in current if r.get('event')=='input_release_transition']==[r for r in legacy if r.get('event')=='input_release_transition'],
 'current':run(current),'total_loss':run(legacy),'legacy':run(legacy)},
 'decision':'UNIDENTIFIABLE_WITH_ROW_FIELDS_ONLY',
 'limits':'Synthetic producer-shaped adapter construction; no runtime, GUI, OS input, game, model, causal attribution, safety, recovery, latency or task completion.'}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))

