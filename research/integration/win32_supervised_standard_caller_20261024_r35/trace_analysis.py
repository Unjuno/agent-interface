"""Pair the R35 recovery VK_Q key-up with the held callback and readback."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
raw=json.loads((P/'raw.json').read_text(encoding='utf-8'))
events=[json.loads(line) for line in (P/'run'/'cancellation_call_trace.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
callback=raw.get('hook_stopped',{}).get('callback_return_ns')
roles={e['pid']:e['helper'] for e in events if e.get('event')=='helper_enter'}
spans=[]
def pair_ordered(pid,start_event,end_events,predicate=None):
    pending=[]
    for e in [row for row in events if row.get('pid')==pid]:
        if e.get('event')==start_event and (predicate is None or predicate(e)):
            pending.append(e)
        elif e.get('event') in end_events and pending:
            start=pending.pop(0)
            end=e.get('monotonic_ns')
            spans.append({'boundary':start_event.removesuffix('_enter'),'pid':pid,
              'helper_role':roles.get(pid),'start_ns':start.get('monotonic_ns'),'end_ns':end,
              'elapsed_ns':e.get('elapsed_ns'),'overlaps_callback':type(callback)is int and start.get('monotonic_ns',0)<=callback<end,
              'unreturned_at_analysis_end':False,'fields':{k:start.get(k) for k in ('helper','request_id','recovery_id','operation_id','input_type','vk','scan_code','flags','key_up') if k in start}})
    for start in pending:
        spans.append({'boundary':start_event.removesuffix('_enter'),'pid':pid,'helper_role':roles.get(pid),
          'start_ns':start.get('monotonic_ns'),'end_ns':None,'elapsed_ns':None,'overlaps_callback':False,
          'unreturned_at_analysis_end':True,'fields':{k:start.get(k) for k in ('helper','request_id','recovery_id','operation_id','input_type','vk','scan_code','flags','key_up') if k in start}})
for pid,role in roles.items():
    if role=='recovery':
        pair_ordered(int(pid),'recover_enter',{'recover_return','recover_exception'})
        pair_ordered(int(pid),'release_all_enter',{'release_all_return','release_all_exception'})
        pair_ordered(int(pid),'sendinput_enter',{'sendinput_return','sendinput_exception'},
                     lambda e:e.get('input_type')==1 and e.get('vk')==81 and e.get('key_up') is True)
for pid in {e.get('pid') for e in events}:
    pair_ordered(pid,'exchange_enter',{'exchange_return','exchange_exception'})
open_spans=[s for s in spans if s['overlaps_callback'] or s['unreturned_at_analysis_end']]
q_up=[s for s in spans if s['boundary']=='sendinput']
result={'schema':'win32-supervised-standard-caller-r35-trace-analysis-v1',
 'attempt_id':'win32-supervised-standard-caller-20261024-r35','callback_return_ns':callback,
 'event_count':len(events),'helper_processes':{str(k):v for k,v in roles.items()},
 'exact_q_up_sendinput_spans':q_up,'spans_overlapping_or_open_at_callback':open_spans,
 'strict_action_audit_status':json.loads((P/'audit_repaired.json').read_text(encoding='utf-8')).get('status'),
 'interpretation':'This packet has no text operations, so the exact recovery Q-up is isolated from Unicode compensation. The wrapper records entry and return from Win32Backend._send around SendInput, not the kernel/application physical state. A call interval spanning callback return is timing evidence only.'}
(P/'trace_analysis_posthoc.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'event_count':len(events),'q_up_calls':len(q_up),'open_or_overlapping':len(open_spans),'strict':result['strict_action_audit_status']},sort_keys=True))
