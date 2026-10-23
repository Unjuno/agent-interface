from __future__ import annotations
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
raw=json.loads((HERE/'raw.json').read_text(encoding='utf-8'))
original=json.loads((HERE/'audit.json').read_text(encoding='utf-8'))
checks=[]
def check(name,passed,evidence): checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
hold=raw.get('post_cancel_io_hold',{})
hook_after=hold.get('hook_trace_after_release',{})
events=hook_after.get('events',[])
callback_return=hook_after.get('callback_return_ns')
if type(callback_return) is not int:
    callback_return=next((e.get('callback_return_ns') for e in events
        if type(e.get('callback_return_ns')) is int),None)
producer=raw.get('producer_identity_from_cancel') or {}
samples=hold.get('producer_liveness_samples',[])
start,end=hold.get('started_monotonic_ns'),hold.get('ended_monotonic_ns')
exited=[s for s in samples if s.get('status')=='exited' and s.get('wait_result')==0
    and s.get('pid')==producer.get('pid')
    and s.get('creation_time_100ns')==producer.get('creation_time_100ns')
    and type(s.get('sampled_monotonic_ns')) is int
    and type(start) is int and type(end) is int
    and start <= s['sampled_monotonic_ns'] <= end]
check('exact_producer_exit_during_hold_before_callback_return',
    bool(exited) and type(callback_return) is int
    and callback_return > min(s['sampled_monotonic_ns'] for s in exited),
    {'producer_identity':producer,'matching_exit_samples':exited,
     'callback_return_ns':callback_return,'hold_start_ns':start,'hold_end_ns':end})
unknown=[s for s in hold.get('status_polls',[]) if s.get('cancellation_status')=='unknown']
first=min(unknown,key=lambda s:s.get('returned_monotonic_ns',2**63-1)) if unknown else {}
cancel=raw.get('public_cancel') or {}
returned=first.get('returned_monotonic_ns'); cancel_ns=cancel.get('started_monotonic_ns')
elapsed_ms=(returned-cancel_ns)/1_000_000 if type(returned) is int and type(cancel_ns) is int else None
check('terminal_action_unknown_within_bound_while_hook_held',
    type(start) is int and type(end) is int and (end-start)/1_000_000 >= 3950
    and type(callback_return) is int and callback_return > end
    and type(returned) is int and returned < end and elapsed_ms is not None
    and elapsed_ms <= 3500 and first.get('action_status')=='unknown'
    and first.get('cancellation_release_confirmed') is False
    and first.get('owner_release_confirmed') is False,
    {'hold_ms':(end-start)/1_000_000 if type(start) is int and type(end) is int else None,
     'cancel_to_unknown_ms':elapsed_ms,'unknown_poll':first,
     'callback_return_ns':callback_return,'hold_end_ns':end})
suppressed=[e for e in events if e.get('message')==0x0100 and e.get('vk')==ord('Q')
    and e.get('flags',0)&0x10 and e.get('suppressed') is True]
check('held_injected_q_down_suppressed_on_callback_return',
    bool(suppressed) and all(type(e.get('callback_return_ns')) is int for e in suppressed),
    {'matching_suppressed_events':suppressed,'hook_trace_after_release':hook_after})
blocked=raw.get('blocked_io_independent_readback') or {}
hook_before=hold.get('hook_trace_before_release') or {}
readback_witness=blocked.get('state_witness',[])
check('same_generation_q_up_sample_occurred_before_blocked_down_was_forwarded',
    blocked.get('status')=='observed' and blocked.get('q_down') is False
    and blocked.get('generation_before')==hook_before.get('generation',blocked.get('expected_generation'))
    and blocked.get('generation_after')==blocked.get('expected_generation')
    and blocked.get('process_retired') is True
    and type(blocked.get('returned_monotonic_ns')) is int
    and type(hook_before.get('callback_entry_ns')) is int
    and blocked['started_monotonic_ns'] >= hook_before['callback_entry_ns']
    and type(callback_return) is int
    and blocked['returned_monotonic_ns'] < callback_return
    and bool(readback_witness)
    and all(w.get('input_desktop_active') is True
            and w.get('hwnd')==raw.get('fixture',{}).get('hwnd')
            and w.get('target_integrity_rid')==w.get('probe_integrity_rid')
            for w in readback_witness),
    {'readback':blocked,'hook_callback_entry_ns':hook_before.get('callback_entry_ns'),
     'hook_callback_return_ns':callback_return,
     'interpretation':'q_down=false while this injected Q-down was still held before CallNextHookEx; this readback is not proof of release'})

passed=sum(x['passed'] for x in checks)
result={'schema':'win32-supervised-standard-caller-r20-posthoc-audit-v1',
    'attempt_id':raw.get('attempt_id'),'source_commit':raw.get('source_commit'),
    'status':'PASS_SCOPED_POSTHOC' if passed==len(checks) else 'FAIL_OR_UNKNOWN',
    'passed':passed,'total':len(checks),'checks':checks,
    'frozen_audit_status':original.get('status'),
    'frozen_audit_passed':original.get('passed'),'frozen_audit_total':original.get('total'),
    'claim_scope':'one-run bounded terminal UNKNOWN with action UNKNOWN while the owned callback is held; no input release or recovery claim',
    'release_proven':False,'task_success':None,'replay_allowed':False}
(HERE/'audit_supplement.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'passed':passed,'total':len(checks)},sort_keys=True))
