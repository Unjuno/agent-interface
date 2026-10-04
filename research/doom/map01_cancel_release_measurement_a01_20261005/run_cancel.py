#!/usr/bin/env python3
"""One fake-display cancellation trace through the current v39 bridge."""
import copy, importlib.util, json, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
DOOM=HERE.parent
BRIDGE_TEST=DOOM/'map01_v39_perkey_bridge_a01'/'test_bridge.py'
spec=importlib.util.spec_from_file_location('bridge_test_under_cancel_probe',BRIDGE_TEST)
bridge_test=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=bridge_test
spec.loader.exec_module(bridge_test)
HarnessModule=bridge_test.load_v12_test_harness()
harness=HarnessModule.Harness(HarnessModule.owner_module)
lease=HarnessModule.Lease(intent='intent-cancel-a01')
Backend=bridge_test.Backend
backend=object.__new__(Backend)
backend.owner=harness.owner
backend.lease=lease
backend.held=set()
backend._input_event_context=('cover-cancel-a01',7)
backend.events=[]
backend.emit=backend.events.append
out={"source_context":["cover-cancel-a01",7],"operation":"down then asynchronous lease cancellation"}
try:
    backend.raw('F8',True)
    out['events_after_down']=copy.deepcopy(backend.events)
    out['physical_after_down']=sorted(harness.d.physical)
    lease.cancel.set()
    deadline=time.monotonic()+1.0
    while time.monotonic()<deadline and not any(r.get('event')=='owner_release' and r.get('reason')=='cancelled' for r in harness.owner.records):
        time.sleep(0.002)
    out['owner_records']=copy.deepcopy(harness.owner.records)
    out['bridge_events_after_cancel']=copy.deepcopy(backend.events)
    out['physical_after_cancel']=sorted(harness.d.physical)
    out['backend_held_after_cancel']=sorted(backend.held)
finally:
    harness.close()
(HERE/'candidate-output.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
