import asyncio, base64, ctypes, hashlib, json, re, time
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
from runtime.cli_v1.mcp_server import create_server

ROOT=Path(__file__).resolve().parent
HWND=24840738
TARGET='notepad'
MARKER='AI-CTRL-20261024-R16'
ORACLE_ID='16161616161616161616161616161616'
expected_by_call={}
oracle_log={}

def text_now():
    u=ctypes.WinDLL('user32',use_last_error=True)
    proc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    found=[]
    def visit(h,_):
        c=ctypes.create_unicode_buffer(128);u.GetClassNameW(h,c,128)
        if c.value=='RichEditD2DPT':found.append(int(h))
        return True
    u.EnumChildWindows(HWND,proc(visit),0)
    if len(found)!=1:raise RuntimeError(f'expected one edit control, got {found}')
    h=found[0];send=u.SendMessageTimeoutW
    send.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
    send.restype=wintypes.LPARAM
    n=ctypes.c_size_t()
    if not send(h,14,0,0,2,750,ctypes.byref(n)) or n.value>4096:raise RuntimeError('bounded WM_GETTEXTLENGTH failed')
    b=ctypes.create_unicode_buffer(n.value+1);read=ctypes.c_size_t()
    if not send(h,13,len(b),ctypes.addressof(b),2,750,ctypes.byref(read)):raise RuntimeError('bounded WM_GETTEXT failed')
    return {'text':b.value,'characters':int(read.value),'child_hwnd':h}

def state_now():
    b=Win32Backend({TARGET:HWND})
    try:return {'generation':b.target_generation(TARGET),'shift_down':b._key_down_state(virtual_key('SHIFT'),TARGET),'foreground_hwnd':int(b.user32.GetForegroundWindow())}
    finally:b.close()

def oracle(a):
    cid=a['call_id'];start_perf=time.perf_counter_ns();expected=expected_by_call.get(cid)
    try:
        state=state_now();row=text_now();observed_perf=time.perf_counter_ns()
        exact=expected is not None and row['text']==expected
        outcome='unknown' if state['generation']!=a['target_generation'] or expected is None else ('success' if exact else 'failure')
        oracle_log[cid]={'start_perf_counter_ns':start_perf,'observed_perf_counter_ns':observed_perf,'return_perf_counter_ns':time.perf_counter_ns(),'expected':expected,'observed_text':row['text'],'characters':row['characters'],'edit_hwnd':row['child_hwnd'],'observed_generation':state['generation'],'generation_match':state['generation']==a['target_generation'],'shift_down':state['shift_down'],'foreground_hwnd':state['foreground_hwnd']}
    except Exception as e:
        observed_perf=time.perf_counter_ns();outcome='unknown';oracle_log[cid]={'start_perf_counter_ns':start_perf,'observed_perf_counter_ns':observed_perf,'return_perf_counter_ns':time.perf_counter_ns(),'error':repr(e)}
    return {'call_id':cid,'operation_id':a['operation_id'],'target_generation':a['target_generation'],'oracle_id':ORACLE_ID,'outcome':outcome,'observed_monotonic_ns':time.monotonic_ns(),'evidence_ref':'oracle-log.json#'+cid}

def save(name,reply):
    row={'isError':bool(getattr(reply,'isError',False)),'content':[]}
    for i,c in enumerate(reply.content):
        if c.type=='text':row['content'].append({'type':'text','text':c.text})
        elif c.type=='image':
            f=f'{name}-{i}.png';d=base64.b64decode(c.data);(ROOT/f).write_bytes(d)
            row['content'].append({'type':'image','file':f,'mimeType':c.mimeType,'sha256':hashlib.sha256(d).hexdigest()})
    (ROOT/f'{name}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return row

def parsed(o):return json.loads(next(x['text'] for x in o['content'] if x['type']=='text'))
def raw(o):return o.get('receipt',{}).get('source',{}).get('raw_report',o)
def summary(dispatch):
    r=raw(dispatch);result=r.get('result') or {};action=(r.get('supervision') or {}).get('action') or {}
    return {'call_id':r.get('call_id'),'status':result.get('status'),'generation':action.get('target_generation') or r.get('target_generation'),'release_confirmed':action.get('release_confirmed'),'task_success_from_dispatch':action.get('task_success'),'emissions':(result.get('execution') or {}).get('emissions'),'detail':result.get('detail')}

def preflight():
    state=state_now();row=text_now()
    u=ctypes.WinDLL('user32',use_last_error=True)
    return {'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'target':{'name':TARGET,'hwnd':HWND,'generation':state['generation'],'edit_hwnd':row['child_hwnd']},'conditions':{'is_window':bool(u.IsWindow(HWND)),'visible':bool(u.IsWindowVisible(HWND)),'enabled':bool(u.IsWindowEnabled(HWND)),'foreground_hwnd':state['foreground_hwnd'],'foreground_is_target':state['foreground_hwnd']==HWND,'shift_down':state['shift_down'],'text':row['text'],'characters':row['characters']},'allocation':'authorized local Windows PC; WSLc=false; Docker=false'}

async def main():
    pre=preflight();(ROOT/'preflight.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cond=pre['conditions']
    if not all((cond['is_window'],cond['visible'],cond['enabled'],cond['foreground_is_target'],cond['shift_down'] is False,cond['text']=='')):
        stop={'status':'STOP_PREFLIGHT_NO_INPUT','preflight':pre,'input_dispatched':False}
        (ROOT/'RESULT.json').write_text(json.dumps(stop,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(stop,ensure_ascii=False,indent=2));return
    generation=pre['target']['generation']
    server=create_server({TARGET:HWND},ROOT/'mcp-calls',session_mode='supervised-win32',supervised_win32_task_oracle=oracle)
    out={'preflight':pre,'target_generation':generation,'marker':MARKER,'faults':[],'task':{},'cleanup':{},'scope':'one exact token through standard public supervised-Win32 caller; independent native text/generation oracle; no model/provider calls'}
    try:
        observe=parsed(save('observe-1',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]})))
        o_raw=raw(observe)
        if o_raw.get('status')!='returned' or o_raw.get('target_generation')!=generation:raise RuntimeError('public observation did not retain preflight generation; no task dispatch')
        out['observation_generation']=o_raw.get('target_generation')
        program={'schema':'agent-interface/program-v1','program_id':'notepad-r16-exact-token','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:generation}},'authority':{'lease_id':'r16-task-effect','expires_at_ns':time.monotonic_ns()+20_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'text','text':MARKER,'gap_ms':25},{'op':'release_all'}]}
        dispatch_start=time.perf_counter_ns();task=asyncio.create_task(server.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000}))
        polls=0;first_nonempty=None;first_exact=None
        while not task.done():
            try:
                row=text_now();stamp=time.perf_counter_ns();polls+=1
                if row['text'] and first_nonempty is None:first_nonempty={'perf_counter_ns':stamp,'elapsed_from_dispatch_start_ns':stamp-dispatch_start,'text':row['text'],'characters':row['characters']}
                if row['text']==MARKER and first_exact is None:first_exact={'perf_counter_ns':stamp,'elapsed_from_dispatch_start_ns':stamp-dispatch_start,'text':row['text'],'characters':row['characters'],'edit_hwnd':row['child_hwnd']}
            except Exception as e:
                out['poll_error']=repr(e);break
            await asyncio.sleep(0.01)
        d=save('task-dispatch',await asyncio.wait_for(task,15));dispatch_return=time.perf_counter_ns();dobj=parsed(d);ds=summary(dobj);cid=ds['call_id']
        out['task']={'dispatch':ds,'dispatch_start_perf_counter_ns':dispatch_start,'dispatch_return_perf_counter_ns':dispatch_return,'dispatch_elapsed_ns':dispatch_return-dispatch_start,'poll_count':polls,'first_nonempty_observation':first_nonempty,'first_exact_observation':first_exact}
        if not isinstance(cid,str) or not re.fullmatch('[0-9a-f]{32}',cid):raise RuntimeError('missing exact action call ID; no verifier attribution')
        expected_by_call[cid]=MARKER
        verify=parsed(save('task-verification',await server.call_tool('interface_verify_task',{'call_id':cid,'wait_for_result_ms':5000})))
        out['task'].update({'verification_status':verify.get('status'),'task_success':verify.get('task_success'),'oracle_outcome':(verify.get('task_effect') or {}).get('receipt',{}).get('outcome') if isinstance((verify.get('task_effect') or {}).get('receipt'),dict) else None,'oracle_observation':oracle_log.get(cid),'retained_result':(verify.get('task_effect') or {})})
        out['task']['independent_text_after']=text_now()
        ob2=parsed(save('observe-2',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]})));rr2=raw(ob2)
        if rr2.get('status')!='returned' or rr2.get('target_generation')!=generation:raise RuntimeError('cleanup observation generation mismatch; no cleanup dispatched')
        clean={'schema':'agent-interface/program-v1','program_id':'notepad-r16-clear-token','source':{'observation_seq':2,'binding_revision':1,'target_generations':{TARGET:generation}},'authority':{'lease_id':'r16-cleanup','expires_at_ns':time.monotonic_ns()+15_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_chord','keys':['CTRL','A']},{'op':'wait_update','timeout_ms':50},{'op':'key_chord','keys':['BACKSPACE']},{'op':'wait_update','timeout_ms':50},{'op':'release_all'}]}
        c=parsed(save('cleanup-dispatch',await server.call_tool('interface_dispatch',{'program':clean,'current_observation_seq':2,'current_binding_revision':1,'wait_for_result_ms':10000})));cs=summary(c);ccid=cs.get('call_id')
        out['cleanup']={'dispatch':cs,'final_text':text_now()}
        if isinstance(ccid,str) and re.fullmatch('[0-9a-f]{32}',ccid):
            expected_by_call[ccid]=''
            cv=parsed(save('cleanup-verification',await server.call_tool('interface_verify_task',{'call_id':ccid,'wait_for_result_ms':5000})))
            ce=cv.get('task_effect') or {}
            out['cleanup'].update({'verification_status':cv.get('status'),'task_success':cv.get('task_success'),'oracle_outcome':ce.get('receipt',{}).get('outcome') if isinstance(ce.get('receipt'),dict) else None,'oracle_observation':oracle_log.get(ccid)})
    finally:
        try:out['close']=parsed(save('close',await server.call_tool('interface_close',{})))
        except Exception as e:out['close_error']=repr(e)
    (ROOT/'oracle-log.json').write_text(json.dumps(oracle_log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    t=out.get('task',{});c=out.get('cleanup',{})
    out['status']='PASS_TASK_EFFECT_AND_TIMING_SCOPED' if (t.get('dispatch',{}).get('status')=='completed' and t.get('dispatch',{}).get('release_confirmed') is True and t.get('verification_status')=='verified' and t.get('task_success') is True and t.get('oracle_outcome')=='success' and t.get('oracle_observation',{}).get('generation_match') is True and t.get('first_exact_observation',{}).get('text')==MARKER and c.get('dispatch',{}).get('release_confirmed') is True and c.get('verification_status')=='verified' and c.get('task_success') is True and c.get('final_text',{}).get('text')=='') else 'FAIL_OR_UNKNOWN'
    (ROOT/'RESULT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':asyncio.run(main())
