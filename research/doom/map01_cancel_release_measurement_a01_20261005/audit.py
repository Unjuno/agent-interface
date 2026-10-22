#!/usr/bin/env python3
"""Independent classification of the frozen cancellation trace."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
x=json.loads((HERE/'candidate-output.json').read_text())
admissions=[e for e in x['events_after_down'] if e.get('event')=='input_admission']
releases=[e for e in x['owner_records'] if e.get('event')=='owner_release' and e.get('reason')=='cancelled']
up_events=[e for e in x['bridge_events_after_cancel'] if e.get('event')=='input_release_measurement']
assert len(admissions)==1, 'expected one owner admission'
down=admissions[0]
measurement=down.get('physical_key_measurement',{})
assert measurement.get('actuation_id'), 'admitted down lacks actuation identity'
assert (down.get('id'),down.get('step'))==tuple(x['source_context']), 'down context mismatch'
assert x['physical_after_down']==[74], 'fake display did not show down'
assert len(releases)==1, 'missing/duplicate cancellation release record'
release=releases[0]
assert release.get('verified') is True and release.get('keys_down')==[], 'cleanup not verified empty'
assert x['physical_after_cancel']==[], 'fake physical key remains down'
if up_events:
    verdict='FAIL_HYPOTHESIS'
else:
    verdict='PASS_GAP_CONFIRMED'
result={'verdict':verdict,'admission_id':measurement['actuation_id'],'program_id':down['id'],'step':down['step'],'verified_cancel_release':True,'matching_bridge_up_receipts':len(up_events),'physical_empty_after_cancel':True,'backend_held_after_cancel':x['backend_held_after_cancel'],'scope':'fake-display cancellation only'}
(HERE/'AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
