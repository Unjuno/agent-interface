import importlib.util, json, sys, time
from pathlib import Path
pkg=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/pr7805-admission-race-probe/research/doom/map01_v39_cancel_release_fix_a01_20261005')
spec=importlib.util.spec_from_file_location('pr7805_tests_a02',pkg/'test_cancel_release.py')
t=importlib.util.module_from_spec(spec); sys.modules[spec.name]=t; spec.loader.exec_module(t)
bridge_test, hm, harness, lease, bridge_module, backend=t.load_candidate()
original=harness.owner.call
race={'cleanup_completed_before_owner_call_return':False,'state_samples':[],'records_before_return':[],'poll_count':0}
def raced_call(operation, lease_arg, key=None, event_context=None):
    row=original(operation,lease_arg,key,event_context=event_context)
    if operation=='down':
        lease.cancel.set()
        deadline=time.monotonic()+1.0
        while time.monotonic()<deadline:
            state=original('input_state',lease)
            race['poll_count']+=1
            race['state_samples'].append({'owned_keycodes':list(state.get('owned_keycodes',[])),'owned_buttons':list(state.get('owned_buttons',[]))})
            releases=[r for r in harness.owner.records if r.get('event')=='owner_release']
            if state.get('owned_keycodes')==[] and state.get('owned_buttons')==[] and releases:
                race['cleanup_completed_before_owner_call_return']=True
                race['records_before_return']=releases
                break
            time.sleep(.001)
    return row
harness.owner.call=raced_call
def cancel_during_down(self, identifier, step):
    self._input_event_context=(identifier,step)
    self.raw('F8',True)
try:
    t.run_program(bridge_test,backend,lease,cancel_during_down,identifier='race-a03',step=9)
    events=backend.events
    admission=next(x for x in events if x.get('event')=='input_admission')
    releases=[x for x in events if x.get('event')=='input_release_measurement']
    out={'study_id':'map01-v39-cleanup-admission-race-a03-20261005','candidate_invocations':1,'candidate_head':'39264f167f8f7541aaf10c43d287938b1317f520','down_receipt':admission,'release_receipts':releases,'events':[x.get('event') for x in events],'cleanup_completed_before_owner_call_return':race['cleanup_completed_before_owner_call_return'],'owner_state_samples_at_injected_boundary':race['state_samples'],'owner_cleanup_records_before_return':race['records_before_return'],'poll_count':race['poll_count'],'fake_physical_keys_after_execute':sorted(harness.d.physical),'bridge_held_after_execute':sorted(backend.held)}
    outpath=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/admission-interleave-a03-result.json')
    outpath.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'events':out['events'],'cleanup_before_owner_call_return':out['cleanup_completed_before_owner_call_return'],'poll_count':out['poll_count'],'owner_keys_at_checkpoint':race['state_samples'][-1]['owned_keycodes'] if race['state_samples'] else None,'cleanup_record_count_before_return':len(race['records_before_return']),'release_count':len(releases),'release_context':[(x.get('id'),x.get('step'),x.get('key')) for x in releases],'fake_physical_keys':out['fake_physical_keys_after_execute'],'bridge_held':out['bridge_held_after_execute']},indent=2))
finally:
    harness.close()
