"""Independent raw-only adjudication of the preregistered boundary facts.

This version preserves the frozen audit.py failure. It does not rerun the candidate
and does not make candidate process exit success a hypothesis requirement.
"""
import copy, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def check(row):
    errors=[]
    def need(ok,label):
        if not ok: errors.append(label)
    t=row.get('up_transition'); events=row.get('fake_keyrelease',[])
    cancel=row.get('cancel_set_ns'); dequeue=row.get('queue_dequeue_ns')
    owner_id=row.get('owner_thread_id')
    need(row.get('hypothesis_id')=='EXPLICIT-UP-POSTCHECK-CANCEL-A03-20261004','run identity')
    need(row.get('frozen_merge_tree')=='71b723028a2db51a7f14a6db653d7f3789fa988b','source tree')
    need(isinstance(t,dict),'transition present')
    need(len(events)==1 and events[0].get('event')=='KeyRelease','one explicit fake keyrelease')
    need(type(cancel) is int and type(dequeue) is int and dequeue<=cancel,'cancel after dequeue')
    false_owner_samples=[s['sample_ns'] for s in row.get('cancel_samples',[])
        if s.get('thread_id')==owner_id and s.get('value') is False and type(s.get('sample_ns')) is int]
    need(bool(false_owner_samples) and type(cancel) is int and max(false_owner_samples)<cancel,
         'owner false cancellation sample precedes set')
    if isinstance(t,dict):
        need(t.get('cancel_requested_at_request') is False,'caller request sample false')
        need(t.get('ordinary_release_candidate') is True,'ordinary candidate emitted')
        need(t.get('owner_thread_keyup_verified') is True,'identity-bound owner receipt verified')
        need(t.get('owner_thread_keyup_history_complete') is True and t.get('owner_thread_keyup_receipt_count')==1,
             'single complete owner history join')
        receipt=t.get('owner_thread_keyup_receipt')
        need(isinstance(receipt,dict) and receipt.get('event')=='owner_explicit_keyup','explicit receipt identity')
        if isinstance(receipt,dict):
            need(receipt.get('owner_id')==t.get('owner_id') and receipt.get('key')=='w' and receipt.get('keycode')==30,
                 'owner/key identity')
            need(type(cancel) is int and cancel<receipt.get('owner_keyrelease_started_ns',0),
                 'cancel precedes owner keyrelease')
            need(receipt.get('owner_keyrelease_started_ns',0)<=receipt.get('owner_sync_returned_ns',-1)
                 <=t.get('release_call_returned_ns',-1),'owner sync inside caller bracket')
    else: receipt=None
    if events:
        need(events[0].get('cancel_set_at_side_effect') is True,'cancel set at fake side effect')
        need(type(cancel) is int and cancel<events[0].get('side_effect_ns',0),'cancel precedes fake side effect')
        need(receipt is not None and receipt.get('owner_keyrelease_started_ns',0)<=events[0].get('side_effect_ns',0)
             <=receipt.get('owner_sync_returned_ns',-1), 'side effect inside owner release bracket')
    history=row.get('owner_records_after_close',[])
    keyups=[r for r in history if isinstance(r,dict) and r.get('event')=='owner_explicit_keyup']
    cleanups=[r for r in history if isinstance(r,dict) and r.get('event')=='owner_release'
              and r.get('reason')=='cancelled']
    need(len(keyups)==1 and receipt==keyups[0],'raw owner history confirms same keyup')
    need(len(cleanups)==1 and cleanups[0].get('verified') is True and cleanups[0].get('keys_down')==[],
         'later cancellation cleanup verifies fake keymap empty')
    need(row.get('owner_thread_stopped') is True,'owner thread terminal')
    need(row.get('candidate_exit')==1 and 'root_x' in row.get('candidate_exception',''),
         'post-observation fake input_state limitation recorded')
    return errors

raw=json.loads((ROOT/'RESULT.json').read_text())
errors=check(raw)
controls={}
for name,mutate in {
    'cancel_after_side_effect':lambda x:x.update(cancel_set_ns=x['fake_keyrelease'][0]['side_effect_ns']+1),
    'ordinary_not_credited':lambda x:x['up_transition'].update(ordinary_release_candidate=False),
    'receipt_unverified':lambda x:x['up_transition'].update(owner_thread_keyup_verified=False),
    'cleanup_not_verified':lambda x:next(r for r in x['owner_records_after_close'] if r.get('reason')=='cancelled').update(verified=False),
}.items():
    bad=copy.deepcopy(raw);mutate(bad);controls[name]=bool(check(bad))
if not all(controls.values()):errors.append('negative control escaped')
summary={
    'audit_version':'v2 raw-only, written after frozen audit.py result retained',
    'hypothesis_gate':'REPRODUCED' if not errors else 'NOT_ESTABLISHED',
    'overall_candidate_run':'STOP_AFTER_TARGET_OBSERVATION' if raw.get('candidate_exit')!=0 else 'EXIT_0',
    'errors':errors,'negative_controls_rejected':controls,
    'interpretation':'The wrapper labels the up ordinary from caller request-time cancellation=false while the queued owner KeyRelease occurs after cancellation is set. The later fake cleanup verifies empty keymap. Candidate then stops in fake input_state because FakeRoot omits root_x; no application or physical effect claim.'
}
(ROOT/'AUDIT_V2.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
raise SystemExit(bool(errors))
