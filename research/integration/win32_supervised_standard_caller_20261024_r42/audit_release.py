from __future__ import annotations
import json
from pathlib import Path
P=Path(__file__).resolve().parent
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
R=json.loads((P/'raw.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,evidence=None): checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
call_id=R.get('blocked_call_id')
pre=R.get('pre_cancel_independent_readback') or {}
gen=(R.get('fixture',{}).get('target_identity') or {}).get('generation')
cancel=R.get('public_cancel') or {}
attempt=R.get('public_cancel_attempt') or {}
hold=R.get('post_cancel_io_hold') or {}
polls=hold.get('status_polls') or []
hook=R.get('hook_stopped') or {}
hook_events=hook.get('events') or []
held=next((e for e in hook_events if e.get('message')==0x0101 and e.get('vk')==ord('Q') and e.get('flags',0)&0x10),{})
entry=held.get('callback_entry_ns'); callback_return=held.get('callback_return_ns')
trace=R.get('cancellation_call_trace') or []
qreturns=[e for e in trace if e.get('event')=='sendinput_return' and e.get('input_type')==1 and e.get('vk')==ord('Q') and e.get('key_up') is True and type(e.get('monotonic_ns')) is int and type(attempt.get('started_monotonic_ns')) is int and e['monotonic_ns']>=attempt['started_monotonic_ns'] and (not type(callback_return)is int or e['monotonic_ns']<callback_return)]
last_qreturn=max((e['monotonic_ns'] for e in qreturns),default=None)
series_path=P/'run'/'independent-state-series.jsonl'
series=[json.loads(x) for x in series_path.read_text(encoding='utf-8').splitlines() if x.strip()] if series_path.exists() else []
samples=[x for x in series if x.get('record_type')=='sample']
eligible=[x for x in samples if type(last_qreturn)is int and type(callback_return)is int and x.get('started_monotonic_ns',0)>last_qreturn and x.get('returned_monotonic_ns',0)<callback_return and x.get('generation_before')==gen and x.get('generation_after')==gen and x.get('expected_generation')==gen and x.get('q_down') is False]
series_meta=R.get('independent_state_series') or {}
close=R.get('public_close') or {}; close=close.get('response',close)
fixture=R.get('fixture') or {}
foreground=fixture.get('foreground_activation') or {}
minimum_polls=C['trial']['required_hold_poll_count']; required_hold=C['trial']['post_cancel_hook_hold_ms']
cancel_start=attempt.get('started_monotonic_ns'); cancel_return=cancel.get('returned_monotonic_ns')
hold_duration=(hold.get('ended_monotonic_ns',0)-hold.get('started_monotonic_ns',0)) if hold.get('ended_monotonic_ns') and hold.get('started_monotonic_ns') else 0
callback_after_cancel=(callback_return-cancel_return) if type(callback_return)is int and type(cancel_return)is int else None
check('one_dispatch_and_one_recorded_cancel_attempt',R.get('dispatch_attempts')==1 and attempt.get('invocation_started') is True and attempt.get('attempt_count')==1 and attempt.get('call_id')==call_id and cancel.get('response') is not None,{'dispatch_attempts':R.get('dispatch_attempts'),'cancel_attempt':attempt,'cancel_recorded':bool(cancel)})
check('foreground_activation_receipt_matches_owned_fixture',foreground.get('activated') is True and foreground.get('fixture_hwnd')==fixture.get('hwnd') and foreground.get('observed_foreground_hwnd')==fixture.get('hwnd') and bool(foreground.get('cua_window_id')),{'foreground_activation':foreground,'fixture_hwnd':fixture.get('hwnd')})
check('same_generation_q_down_before_cancel',pre.get('status')=='observed' and pre.get('q_down') is True and pre.get('generation_before')==gen and pre.get('generation_after')==gen,{'pre_cancel':pre,'generation':gen})
check('exact_call_status_remained_running_before_cancel',(R.get('pre_cancel_status_readback') or {}).get('call_id')==call_id and ((R.get('pre_cancel_status_readback') or {}).get('action') or {}).get('status')=='running',R.get('pre_cancel_status_readback'))
check('public_cancel_response_bounded_and_successful',bool(cancel) and cancel.get('is_error') is False and type(cancel.get('returned_monotonic_ns')) is int and type(cancel.get('started_monotonic_ns')) is int and cancel['returned_monotonic_ns']-cancel['started_monotonic_ns']<=C['timeouts_seconds']['cancel_response']*1_000_000_000,{'started_ns':cancel.get('started_monotonic_ns'),'returned_ns':cancel.get('returned_monotonic_ns'),'is_error':cancel.get('is_error')})
check('callback_held_for_full_1250ms_after_cancel_response',callback_after_cancel is not None and callback_after_cancel>=required_hold*1_000_000,{'callback_entry_ns':entry,'cancel_return_ns':cancel_return,'callback_return_ns':callback_return,'after_cancel_ms':callback_after_cancel/1_000_000 if callback_after_cancel is not None else None,'required_ms':required_hold})
check('minimum_21_same_call_polls_during_hold',len(polls)>=minimum_polls and all(x.get('call_id')==call_id for x in polls) and all(not x.get('is_error',True) for x in polls),{'count':len(polls),'required':minimum_polls,'call_ids':sorted({str(x.get('call_id')) for x in polls})})
check('same_generation_q_up_independently_observed_while_callback_held',bool(eligible) and type(cancel_start)is int and type(last_qreturn)is int and eligible[-1]['returned_monotonic_ns']-cancel_start<=C['trial']['recovery_deadline_ms']*1_000_000,{'recovery_q_up_sendinput_returns':qreturns,'eligible_q_up_sample_count':len(eligible),'recovery_deadline_ms':C['trial']['recovery_deadline_ms']})
check('sampler_exited_cleanly_before_fixture_close',series_meta.get('status')=='observed' and series_meta.get('exit_code')==0 and series and series[-1].get('record_type')=='summary' and series[-1].get('status')=='observed',{'series_meta':series_meta,'summary':series[-1] if series else None})
exit_witness=R.get('producer_exit_witness') or {}
check('producer_retired_and_fixture_session_cleaned',(exit_witness.get('process_exited') is True or exit_witness.get('status')=='exited') and fixture.get('exit_code')==0 and fixture.get('window_exists_after_exit') is False and close.get('status')=='closed' and hook.get('thread_exited') is True and (R.get('foreground_restore') or {}).get('restored') is True,{'producer_exit':exit_witness,'fixture_exit':fixture.get('exit_code'),'window_exists':fixture.get('window_exists_after_exit'),'close':close,'hook_exited':hook.get('thread_exited'),'foreground_restored':(R.get('foreground_restore') or {}).get('restored')})
effect=R.get('effect_readback') or {}
check('runtime_task_success_unclaimed',effect.get('task_success') is None and R.get('task_success') is None,{'runtime_task_success':R.get('task_success'),'effect_task_success':effect.get('task_success')})
passed=sum(c['passed'] for c in checks)
strict_names={'foreground_activation_receipt_matches_owned_fixture','one_dispatch_and_one_recorded_cancel_attempt','same_generation_q_down_before_cancel','exact_call_status_remained_running_before_cancel','public_cancel_response_bounded_and_successful','callback_held_for_full_1250ms_after_cancel_response','minimum_21_same_call_polls_during_hold','same_generation_q_up_independently_observed_while_callback_held','sampler_exited_cleanly_before_fixture_close','producer_retired_and_fixture_session_cleaned'}
strict=all(c['passed'] for c in checks if c['name'] in strict_names)
result={'schema':'win32-supervised-standard-caller-r42-release-audit-v1','attempt_id':C['attempt_id'],'source_commit':C['source_commit'],'status':'STRICT_RELEASE_PASS' if strict else 'FAIL_OR_UNKNOWN','passed':passed,'total':len(checks),'strict_release_gate_passed':strict,'task_success':None,'checks':checks}
(P/'audit_r36.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'passed':passed,'total':len(checks),'strict':strict},sort_keys=True))
