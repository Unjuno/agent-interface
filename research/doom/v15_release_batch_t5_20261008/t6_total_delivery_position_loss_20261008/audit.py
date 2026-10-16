import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'package'))
from adapter import adapt_session_records
from test_delivery_batches import sample,event,row

def candidate(positions):
    a=row('input_release_transition','space',0); a.update(release_batch_size=2,release_batch_position=0)
    b=row('input_release_transition','up',1); b.update(release_batch_size=2,release_batch_position=1)
    rows=[row('input_admission','space'),a,row('input_admission','up'),b]
    if not positions:
        for r in rows:
            if r.get('event')=='input_release_transition': r.pop('release_batch_delivery_position',None)
    return rows

def output(rows):return adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
current=candidate(True); degraded=candidate(False); legacy=candidate(False)
current_up=[r for r in current if r.get('event')=='input_release_transition']
degraded_up=[r for r in degraded if r.get('event')=='input_release_transition']
legacy_up=[r for r in legacy if r.get('event')=='input_release_transition']
if degraded_up!=legacy_up: raise SystemExit('failed: total-loss and legacy rows differ')
if output(degraded)!=output(legacy): raise SystemExit('failed: adapter outcomes differ')
for r in (output(degraded),output(legacy)):
    if r['trace_integrity']!='SOURCE_ROWS_JOINED' or r['attributions'][0]['status']!='TEMPORALLY_UNIQUE': raise SystemExit('failed: expected accepted disposition changed')
if not all(r.get('release_batch_schema')=='input-release-batch-v3' for r in current_up+degraded_up): raise SystemExit('failed: schema marker mismatch')
report={'audit':'PASS_ROW_ONLY_TOTAL_LOSS_UNIDENTIFIABLE','checks':{'current_has_delivery_positions':all('release_batch_delivery_position' in r for r in current_up),'degraded_rows_equal_legacy_rows':degraded_up==legacy_up,'degraded_output_equals_legacy_output':output(degraded)==output(legacy),'both_unique_not_causal':output(degraded)['attributions'][0]['causal_attribution']=='NOT_ESTABLISHED','no_live_claim':True},'disposition':{'trace_integrity':output(degraded)['trace_integrity'],'attribution':output(degraded)['attributions'][0]['status']}}
(HERE/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))

