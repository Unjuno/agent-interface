from __future__ import annotations
import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=json.loads((P/'raw.json').read_text(encoding='utf-8'))
trace=[json.loads(x) for x in (P/'run/cancellation_call_trace.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
roles={e['pid']:e['helper'] for e in trace if e.get('event')=='helper_enter'}
callback=R['hook_stopped']['callback_return_ns']; entry=R['hook_stopped']['callback_entry_ns']
cancel=R['public_cancel']; cstart=cancel['started_monotonic_ns']; cend=cancel['returned_monotonic_ns']
spans=[]
for pid in {e.get('pid') for e in trace}:
 pending=[]
 for e in [x for x in trace if x.get('pid')==pid]:
  if e.get('event')=='sendinput_enter' and e.get('input_type')==1 and e.get('vk')==ord('Q') and e.get('key_up') is True:
   pending.append(e)
  elif e.get('event') in ('sendinput_return','sendinput_exception') and pending:
   start=pending.pop(0); end=e.get('monotonic_ns')
   spans.append({'pid':pid,'role':roles.get(pid),'start_ns':start.get('monotonic_ns'),'end_ns':end,'elapsed_ms':e.get('elapsed_ns',0)/1e6,'after_cancel_start':start.get('monotonic_ns',0)>=cstart,'overlaps_held_callback':start.get('monotonic_ns',0)<=callback and end>=entry,'crosses_cancel_response':start.get('monotonic_ns',0)<=cend<=end})
result={'schema':'win32-supervised-standard-caller-r36-trace-analysis-v1','attempt_id':R['attempt_id'],'callback_entry_ns':entry,'callback_return_ns':callback,'callback_duration_ms':(callback-entry)/1e6,'cancel_started_ns':cstart,'cancel_returned_ns':cend,'cancel_response_ms':cancel['elapsed_ms'],'callback_return_after_cancel_ms':(callback-cend)/1e6,'post_cancel_hold_ms':(R['post_cancel_io_hold']['ended_monotonic_ns']-R['post_cancel_io_hold']['started_monotonic_ns'])/1e6,'status_poll_count':len(R['post_cancel_io_hold']['status_polls']),'q_up_sendinput_spans':spans,'distinct_q_up_hook_callbacks':sum(1 for e in R['hook_stopped']['events'] if e.get('message')==257 and e.get('vk')==81 and e.get('flags',0)&16),'recovery_terminal_receipt':(R.get('retained_report') or {}).get('supervision',{}).get('cancellation',{}),'public_close_release_confirmed':(R.get('public_close') or {}).get('response',{}).get('release_confirmed'),'interpretation':'SendInput wrapper intervals and same-generation readbacks are timing observations, not kernel-causality or physical application-time claims. The exact cancellation and action receipts plus independent Q-state readings are evaluated in evidence_review_r36.json.'}
(P/'trace_analysis_posthoc_r36.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'spans':len(spans),'q_up_hook_events':result['distinct_q_up_hook_callbacks'],'callback_after_cancel_ms':result['callback_return_after_cancel_ms'],'hold_ms':result['post_cancel_hold_ms'],'polls':result['status_poll_count']},sort_keys=True))
