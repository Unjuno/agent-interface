"""Post-hoc pairing of R31 trace rows; does not modify frozen raw or conditions."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
raw=json.loads((P/'raw.json').read_text(encoding='utf-8'))
events=[json.loads(x) for x in (P/'run'/'cancellation_call_trace.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
cb=raw.get('hook_stopped',{}).get('callback_return_ns')
roles={e['pid']:e['helper'] for e in events if e.get('event')=='helper_enter'}
spans=[]
def ordered_pairs(pid, start_name, end_names):
    stack=[]
    for e in [x for x in events if x.get('pid')==pid]:
        if e.get('event')==start_name:
            stack.append(e)
        elif e.get('event') in end_names and stack:
            a=stack.pop(0)
            spans.append({'boundary':start_name.removesuffix('_enter'),'pid':pid,'helper_role':roles.get(pid),
              'start_ns':a.get('monotonic_ns'),'end_ns':e.get('monotonic_ns'),'elapsed_ns':e.get('elapsed_ns'),
              'overlaps_callback_block':type(cb)is int and a.get('monotonic_ns',0)<=cb<e.get('monotonic_ns',0),
              'unreturned_at_end':False,'event_fields':{k:a.get(k) for k in ('helper','request_id','recovery_id','vk','flags','key_up','input_type') if k in a}})
    for a in stack:
        spans.append({'boundary':start_name.removesuffix('_enter'),'pid':pid,'helper_role':roles.get(pid),
          'start_ns':a.get('monotonic_ns'),'end_ns':None,'elapsed_ns':None,
          'overlaps_callback_block':False,'unreturned_at_end':True,
          'event_fields':{k:a.get(k) for k in ('helper','request_id','recovery_id','vk','flags','key_up','input_type') if k in a}})
for pid,role in roles.items():
    if role=='recovery':
        for a_name,b_names in [('recover_enter',{'recover_return','recover_exception'}),('release_all_enter',{'release_all_return','release_all_exception'}),('sendinput_enter',{'sendinput_return','sendinput_exception'})]:
            ordered_pairs(int(pid),a_name,b_names)
for pid in sorted({e.get('pid') for e in events}):
    ordered_pairs(pid,'exchange_enter',{'exchange_return','exchange_exception'})
overlap=[s for s in spans if s['overlaps_callback_block']]
unicode_ups=[s for s in spans if s['boundary']=='sendinput' and s['event_fields'].get('flags')==6]
result={'schema':'win32-supervised-standard-caller-r31-posthoc-trace-analysis-v1',
 'attempt_id':'win32-supervised-standard-caller-20261024-r31',
 'callback_return_ns':cb,'callback_hold_ms':raw.get('post_cancel_io_hold',{}).get('target_hold_ms'),
 'helper_processes':{str(k):v for k,v in roles.items()},'span_count':len(spans),
 'unicode_keyup_sendinput_calls':unicode_ups,'spans_overlapping_callback_block':overlap,
 'posthoc_interpretation':'Four recovery-process SendInput calls carrying KEYEVENTF_UNICODE|KEYEVENTF_KEYUP (flags=6) each remained inside the API wrapper for roughly 299–314 ms; the fourth interval crossed the callback return. This timing is consistent with the blocked low-level hook delaying native injection, but a single trace does not prove causal kernel behavior. No claim is made that the Q key-up itself was accepted before callback return; the recorded 4 long calls are Unicode compensating key-ups. The trace shows SendInput call intervals and later Q-up; OS application timing remains unobserved.'}
(P/'posthoc_trace_analysis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'unicode_up_count':len(unicode_ups),'unicode_up_durations_ms':[round(s['elapsed_ns']/1e6,3) for s in unicode_ups], 'overlap_count':len(overlap),'overlap':[{'boundary':s['boundary'],'elapsed_ms':round(s['elapsed_ns']/1e6,3) if s.get('elapsed_ns') else None,'fields':s['event_fields']} for s in overlap]},sort_keys=True))