"""Measure R32 events inside the exact low-level-hook callback interval."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
raw=json.loads((P/'raw.json').read_text(encoding='utf-8'))
events=[json.loads(x) for x in (P/'run'/'cancellation_call_trace.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
hook=raw.get('hook_stopped',{})
entry=hook.get('callback_entry_ns'); returned=hook.get('callback_return_ns')
roles={e['pid']:e['helper'] for e in events if e.get('event')=='helper_enter'}
def paired(name, end_names, pid, predicate=None, identity=None):
    out=[]; pending=[]
    for e in [x for x in events if x.get('pid')==pid]:
        if e.get('event')==name and (predicate is None or predicate(e)):
            pending.append(e)
        elif e.get('event') in end_names and pending:
            start=pending.pop(0)
            if identity and start.get(identity)!=e.get(identity):
                # Find the first pending start matching the call identity.
                match=next((i for i,a in enumerate(pending) if a.get(identity)==e.get(identity)),None)
                if match is None: continue
                start=pending.pop(match)
            a=start.get('monotonic_ns'); b=e.get('monotonic_ns')
            out.append({'boundary':name.removesuffix('_enter'),'pid':pid,'helper_role':roles.get(pid),
                        'start_ns':a,'end_ns':b,'elapsed_ns':e.get('elapsed_ns'),
                        'inside_callback_interval':type(entry)is int and type(returned)is int and entry<=a<=b<=returned,
                        'overlaps_callback_interval':type(entry)is int and type(returned)is int and a<returned and b>entry,
                        'start_offset_from_cancel_ms':(a-raw['public_cancel']['started_monotonic_ns'])/1e6,
                        'end_offset_from_cancel_ms':(b-raw['public_cancel']['started_monotonic_ns'])/1e6,
                        'fields':{k:start.get(k) for k in ('helper','request_id','recovery_id','operation_id','input_type','vk','scan_code','flags','key_up') if k in start}})
    return out
spans=[]
for pid,role in roles.items():
    if role=='recovery':
        for args in [('recover_enter',{'recover_return','recover_exception'},None,'recovery_id'),('release_all_enter',{'release_all_return','release_all_exception'},None,None),('sendinput_enter',{'sendinput_return','sendinput_exception'},lambda e:e.get('input_type')==1 and e.get('vk')==81 and e.get('key_up') is True,None)]:
            spans += paired(args[0],args[1],int(pid),args[2],args[3])
for pid in {e.get('pid') for e in events}:
    spans += paired('exchange_enter',{'exchange_return','exchange_exception'},pid,identity='request_id')
result={'schema':'win32-supervised-standard-caller-r32-callback-interval-analysis-v1','attempt_id':'win32-supervised-standard-caller-20261024-r32','callback_entry_ns':entry,'callback_return_ns':returned,'callback_interval_ms':(returned-entry)/1e6 if type(entry)is int and type(returned)is int else None,'boundary_spans':spans,'q_up_calls':[s for s in spans if s['boundary']=='sendinput'],'spans_inside_block':[s for s in spans if s['inside_callback_interval']],'public_hold_polls':raw.get('post_cancel_io_hold',{}).get('status_polls',[]),'observer_exchange_returns':[e for e in events if e.get('event')=='exchange_return' and e.get('helper')=='observer'],'hook_event_list':hook.get('events',[]),'interpretation':'Intervals inside the callback lifetime do not establish that the injected event reached the target. The separate Q-up hook event and task state remain independent evidence; this analysis preserves timing only.'}
(P/'callback_interval_analysis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'callback_ms':round(result['callback_interval_ms'],3),'q_up':result['q_up_calls'],'spans_inside_block':[{'boundary':s['boundary'],'elapsed_ms':round(s['elapsed_ns']/1e6,3) if s.get('elapsed_ns') is not None else None,'offset_start_ms':round(s['start_offset_from_cancel_ms'],3),'offset_end_ms':round(s['end_offset_from_cancel_ms'],3),'fields':s['fields']} for s in result['spans_inside_block']]},sort_keys=True))