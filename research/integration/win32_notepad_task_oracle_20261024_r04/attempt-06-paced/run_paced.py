import asyncio, base64, ctypes, hashlib, json, re, sys, time
from ctypes import wintypes
from pathlib import Path
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.cli_v1.mcp_server import create_server
ROOT=Path(__file__).resolve().parent; HWND=24840738; TARGET='notepad'
MARKER='AI-CTRL-20261024-R04'; ID='06060606060606060606060606060606'
expected_by_call={}; oracle_log={}

def text_now():
    u=ctypes.WinDLL('user32',use_last_error=True); proc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM); found=[]
    def visit(h,_):
        n=ctypes.create_unicode_buffer(128); u.GetClassNameW(h,n,128)
        if n.value=='RichEditD2DPT': found.append(int(h))
        return True
    u.EnumChildWindows(HWND,proc(visit),0)
    if len(found)!=1: raise RuntimeError(f'edit count {len(found)}')
    h=found[0]; s=u.SendMessageTimeoutW; s.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)];s.restype=wintypes.LPARAM
    n=ctypes.c_size_t()
    if not s(h,14,0,0,2,750,ctypes.byref(n)) or n.value>4096: raise RuntimeError('bounded length read failed')
    b=ctypes.create_unicode_buffer(n.value+1);g=ctypes.c_size_t()
    if not s(h,13,len(b),ctypes.addressof(b),2,750,ctypes.byref(g)): raise RuntimeError('bounded text read failed')
    return {'text':b.value,'characters':int(g.value),'child_hwnd':h}
def gen_now():
    b=Win32Backend({TARGET:HWND})
    try:return b.target_generation(TARGET)
    finally:b.close()
def oracle(a):
    cid=a['call_id']; start=time.monotonic_ns(); expected=expected_by_call.get(cid)
    try:
        g=gen_now(); row=text_now(); observed=time.monotonic_ns()
        exact=(row['text']==expected) if expected is not None else False
        result='unknown' if g!=a['target_generation'] or expected is None else ('success' if exact else 'failure')
        oracle_log[cid]={'callback_start_ns':start,'observed_monotonic_ns':observed,'callback_return_ns':time.monotonic_ns(),'expected':expected,'observed_text':row['text'],'characters':row['characters'],'child_hwnd':row['child_hwnd'],'target_generation_match':g==a['target_generation']}
    except Exception as e:
        observed=time.monotonic_ns(); result='unknown'; oracle_log[cid]={'callback_start_ns':start,'observed_monotonic_ns':observed,'callback_return_ns':time.monotonic_ns(),'error':repr(e)}
    return {'call_id':cid,'operation_id':a['operation_id'],'target_generation':a['target_generation'],'oracle_id':ID,'outcome':result,'observed_monotonic_ns':max(observed,start+1),'evidence_ref':'oracle-log.json#'+cid}
def save(label,r):
    o={'isError':bool(getattr(r,'isError',False)),'content':[]}
    for i,c in enumerate(r.content):
        if c.type=='text':o['content'].append({'type':'text','text':c.text})
        elif c.type=='image':
            f=f'{label}-{i}.png'; d=base64.b64decode(c.data); (ROOT/f).write_bytes(d);o['content'].append({'type':'image','file':f,'sha256':hashlib.sha256(d).hexdigest(),'mimeType':c.mimeType})
    (ROOT/f'{label}.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return o
def parsed(o):return json.loads(next(x['text'] for x in o['content'] if x['type']=='text'))
def raw(o):return o.get('receipt',{}).get('source',{}).get('raw_report',o)
def summarize(dispatch):
    r=raw(dispatch); a=(r.get('supervision') or {}).get('action') or {}; result=r.get('result') or {}
    return {'call_id':r.get('call_id'),'status':result.get('status'),'emissions':(result.get('execution') or {}).get('emissions'),'release_confirmed':a.get('release_confirmed'),'task_success_from_dispatch':a.get('task_success'),'generation':a.get('target_generation'),'detail':result.get('detail')}
async def main():
    before=text_now()
    if before['text']!='':raise RuntimeError('precondition not blank; no input sent')
    generation=gen_now()
    (ROOT/'preflight.json').write_text(json.dumps({'hwnd':HWND,'initial_text':before['text'],'characters':before['characters'],'generation':generation,'condition':'one Unicode text op per character, 25ms wait_update after each'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    server=create_server({TARGET:HWND},ROOT/'mcp-calls',session_mode='supervised-win32',supervised_win32_task_oracle=oracle)
    out={'condition':'paced per-character standard Win32 MCP dispatch','marker':MARKER,'target_generation':generation,'tasks':[]}
    try:
        ob=parsed(save('observe-1',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]})))
        rr=raw(ob)
        if rr.get('status')!='returned' or rr.get('target_generation')!=generation:raise RuntimeError('public observation/generation mismatch')
        ops=[{'op':'focus','target':TARGET}]
        for ch in MARKER:
            ops.append({'op':'text','text':ch}); ops.append({'op':'wait_update','timeout_ms':25})
        ops.append({'op':'release_all'})
        p={'schema':'agent-interface/program-v1','program_id':'notepad-r04-paced-marker','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:generation}},'authority':{'lease_id':'r04-paced','expires_at_ns':time.monotonic_ns()+20_000_000_000},'terminal':{'release_all_required':True},'ops':ops}
        d=save('paced-dispatch',await server.call_tool('interface_dispatch',{'program':p,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000})); dobj=parsed(d); ds=summarize(dobj); cid=ds['call_id']
        if not isinstance(cid,str) or not re.fullmatch('[0-9a-f]{32}',cid):raise RuntimeError('missing call id, no replay')
        expected_by_call[cid]=MARKER
        v=parsed(save('paced-task-verification',await server.call_tool('interface_verify_task',{'call_id':cid,'wait_for_result_ms':5000})))
        out['tasks'].append({'dispatch':ds,'verification_status':v.get('status'),'task_success':v.get('task_success'),'oracle_outcome':(v.get('task_effect') or {}).get('receipt',{}).get('outcome') if isinstance((v.get('task_effect') or {}).get('receipt'),dict) else None,'verification_uncertainty':(v.get('task_effect') or {}).get('uncertainty'),'oracle_observation':oracle_log.get(cid)})
        current=text_now(); out['after_paced_task']={'text':current['text'],'characters':current['characters']}
        if current['text']!='':
            ob2=parsed(save('observe-2',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]}))); rr2=raw(ob2); generation2=rr2.get('target_generation')
            if rr2.get('status')=='returned' and generation2==generation:
                p2={'schema':'agent-interface/program-v1','program_id':'notepad-r04-clear-after-paced','source':{'observation_seq':2,'binding_revision':1,'target_generations':{TARGET:generation2}},'authority':{'lease_id':'r04-cleanup-after-paced','expires_at_ns':time.monotonic_ns()+15_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_chord','keys':['CTRL','A']},{'op':'key_chord','keys':['BACKSPACE']},{'op':'release_all'}]}
                d2=save('cleanup-dispatch',await server.call_tool('interface_dispatch',{'program':p2,'current_observation_seq':2,'current_binding_revision':1,'wait_for_result_ms':10000})); d2obj=parsed(d2); ds2=summarize(d2obj); cid2=ds2['call_id']
                if isinstance(cid2,str) and re.fullmatch('[0-9a-f]{32}',cid2):
                    expected_by_call[cid2]=''
                    v2=parsed(save('cleanup-task-verification',await server.call_tool('interface_verify_task',{'call_id':cid2,'wait_for_result_ms':5000})))
                    out['cleanup']={'dispatch':ds2,'verification_status':v2.get('status'),'task_success':v2.get('task_success'),'oracle_outcome':(v2.get('task_effect') or {}).get('receipt',{}).get('outcome') if isinstance((v2.get('task_effect') or {}).get('receipt'),dict) else None,'verification_uncertainty':(v2.get('task_effect') or {}).get('uncertainty'),'oracle_observation':oracle_log.get(cid2)}
        out['final_readback']=text_now(); out['empty_after_cleanup']=out['final_readback']['text']==''
    finally:
        try:out['close']=parsed(save('close',await server.call_tool('interface_close',{})))
        except Exception as e:out['close_error']=repr(e)
    (ROOT/'oracle-log.json').write_text(json.dumps(oracle_log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out['overall']='PASS_PACED' if out['tasks'][0]['task_success'] is True and out.get('empty_after_cleanup') else 'FAIL_OR_UNKNOWN'
    (ROOT/'RESULT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':asyncio.run(main())
