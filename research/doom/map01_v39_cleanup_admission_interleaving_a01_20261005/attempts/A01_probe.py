import importlib.util, json, sys
from pathlib import Path
pkg=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/pr7805-admission-race-probe/research/doom/map01_v39_cancel_release_fix_a01_20261005')
spec=importlib.util.spec_from_file_location('pr7805_tests',pkg/'test_cancel_release.py')
t=importlib.util.module_from_spec(spec); sys.modules[spec.name]=t; spec.loader.exec_module(t)
bridge_test, hm, harness, lease, bridge_module, backend=t.load_candidate()
original=harness.owner.call
race={'cleanup_before_down_receipt':False,'state':None}
def raced_call(operation, lease_arg, key=None, event_context=None):
    row=original(operation,lease_arg,key,event_context=event_context)
    if operation=='down':
        lease.cancel.set()
        race['state']=original('input_state',lease)
        race['cleanup_before_down_receipt']=True
    return row
harness.owner.call=raced_call
def cancel_during_down(self, identifier, step):
    self._input_event_context=(identifier,step)
    self.raw('F8',True)
try:
    t.run_program(bridge_test,backend,lease,cancel_during_down,identifier='race-a01',step=7)
    events=backend.events
    admission=next(x for x in events if x.get('event')=='input_admission')
    releases=[x for x in events if x.get('event')=='input_release_measurement']
    out={'study_id':'map01-v39-cleanup-admission-race-a02-20261005','candidate_invocations':1,'pr7805_head':'84148054938965dc245602e37220586e07c6f28e','down_receipt':admission,'release_receipts':releases,'events':[x.get('event') for x in events],'cleanup_completed_before_down_return':race['cleanup_before_down_receipt'],'owner_state_at_injected_boundary':race['state'],'fake_physical_keys_after_execute':sorted(harness.d.physical),'bridge_held_after_execute':sorted(backend.held)}
    outpath=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/admission-interleave-result.json')
    outpath.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'events':out['events'],'cleanup_before_return':out['cleanup_completed_before_down_return'],'release_count':len(releases),'release_context':[(x.get('id'),x.get('step'),x.get('key')) for x in releases],'fake_physical_keys':out['fake_physical_keys_after_execute'],'bridge_held':out['bridge_held_after_execute']},indent=2))
finally:
    harness.close()
