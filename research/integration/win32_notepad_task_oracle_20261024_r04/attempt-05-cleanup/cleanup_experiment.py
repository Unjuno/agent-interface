import asyncio, base64, ctypes, hashlib, json, re, time
from ctypes import wintypes
from pathlib import Path
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.cli_v1.mcp_server import create_server

ROOT=Path(__file__).resolve().parent; TARGET='notepad'; HWND=24840738
EXPECTED_BEFORE='AIRL-202-6CT024-1R04'; ORACLE_ID='05050505050505050505050505050505'
expected_by_call={}; oracle_log={}

def read_text(hwnd):
    u=ctypes.WinDLL('user32',use_last_error=True); Proc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM); found=[]
    def cb(h,_):
        n=ctypes.create_unicode_buffer(128); u.GetClassNameW(h,n,len(n))
        if n.value=='RichEditD2DPT': found.append(int(h))
        return True
    if not u.EnumChildWindows(hwnd,Proc(cb),0) or len(found)!=1: raise RuntimeError(f'edit child count={len(found)}')
    h=found[0]; send=u.SendMessageTimeoutW
    send.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]; send.restype=wintypes.LPARAM
    n=ctypes.c_size_t()
    if not send(h,0x000E,0,0,2,750,ctypes.byref(n)): raise TimeoutError('WM_GETTEXTLENGTH')
    if n.value>4096: raise ValueError('text length over bound')
    b=ctypes.create_unicode_buffer(n.value+1); got=ctypes.c_size_t()
    if not send(h,0x000D,len(b),ctypes.addressof(b),2,750,ctypes.byref(got)): raise TimeoutError('WM_GETTEXT')
    return {'hwnd':h,'text':b.value,'characters':got.value}

def generation():
    b=Win32Backend({TARGET:HWND})
    try: return b.target_generation(TARGET)
    finally: b.close()

def oracle(action):
    t0=time.monotonic_ns(); cid=action['call_id']; expected=expected_by_call.get(cid)
    try:
        gen=generation(); row=read_text(HWND); t1=time.monotonic_ns()
        outcome=('unknown' if gen!=action['target_generation'] or expected is None else 'success' if row['text']==expected else 'failure')
        oracle_log[cid]={'started_ns':t0,'finished_ns':t1,'characters':row['characters'],'observed_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),'child_hwnd':row['hwnd']}
    except Exception as e:
        t1=time.monotonic_ns(); outcome='unknown'; oracle_log[cid]={'started_ns':t0,'finished_ns':t1,'error':repr(e)}
    return {'call_id':cid,'operation_id':action['operation_id'],'target_generation':action['target_generation'],'oracle_id':ORACLE_ID,'outcome':outcome,'observed_monotonic_ns':max(t1,t0+1),'evidence_ref':'oracle-log.json#'+cid}

def save(name,reply):
    row={'isError':bool(getattr(reply,'isError',False)),'content':[]}
    for i,c in enumerate(reply.content):
        if c.type=='text': row['content'].append({'type':'text','text':c.text})
        elif c.type=='image':
            f=f'{name}-image-{i}.png'; data=base64.b64decode(c.data); (ROOT/f).write_bytes(data)
            row['content'].append({'type':'image','file':f,'mimeType':c.mimeType,'sha256':hashlib.sha256(data).hexdigest()})
    (ROOT/f'{name}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return row

def parsed(row): return json.loads(next(x['text'] for x in row['content'] if x['type']=='text'))
def raw(obj): return obj.get('receipt',{}).get('source',{}).get('raw_report',obj)

async def main():
    before=read_text(HWND); gen=generation()
    if before['text']!=EXPECTED_BEFORE: raise RuntimeError('cleanup precondition changed; no input sent')
    pre={'window_hwnd':HWND,'initial_text':before['text'],'initial_chars':before['characters'],'generation':gen,'task':'remove only the synthetic text produced by attempt-04'}
    (ROOT/'preflight.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    server=create_server({TARGET:HWND},ROOT/'mcp-calls',session_mode='supervised-win32',supervised_win32_task_oracle=oracle)
    outcome={}
    try:
        ob=save('observe',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]})); obj=parsed(ob); report=raw(obj)
        if report.get('status')!='returned' or report.get('target_generation')!=gen: raise RuntimeError('fresh public observation/gen mismatch')
        program={'schema':'agent-interface/program-v1','program_id':'notepad-r04-clear-synthetic-text','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:gen}},'authority':{'lease_id':'r04-cleanup','expires_at_ns':time.monotonic_ns()+15_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_chord','keys':['CTRL','A']},{'op':'key_chord','keys':['BACKSPACE']},{'op':'release_all'}]}
        d=save('cleanup-dispatch',await server.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000})); dobj=parsed(d); dr=raw(dobj); cid=dr.get('call_id')
        if not isinstance(cid,str) or not re.fullmatch('[0-9a-f]{32}',cid): raise RuntimeError('dispatch returned no call ID; no replay')
        expected_by_call[cid]=''
        v=save('cleanup-task-verification',await server.call_tool('interface_verify_task',{'call_id':cid,'wait_for_result_ms':5000})); vobj=parsed(v)
        action=(dr.get('supervision') or {}).get('action') or {}; result=dr.get('result') or {}
        outcome={'cleanup_call_id':cid,'dispatch_status':result.get('status'),'execution_emissions':(result.get('execution') or {}).get('emissions'),'release_confirmed':action.get('release_confirmed'),'verification_status':vobj.get('status'),'task_success':vobj.get('task_success'),'oracle_outcome':(vobj.get('task_effect') or {}).get('receipt',{}).get('outcome'),'oracle_evidence':oracle_log.get(cid)}
    finally:
        try: outcome['close']=parsed(save('close',await server.call_tool('interface_close',{})))
        except Exception as e: outcome['close_error']=repr(e)
    (ROOT/'oracle-log.json').write_text(json.dumps(oracle_log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    final=read_text(HWND); outcome['final_text_characters']=final['characters']; outcome['final_text_sha256']=hashlib.sha256(final['text'].encode()).hexdigest(); outcome['final_text_empty']=final['text']==''
    outcome['status']='PASS_CLEANUP' if outcome.get('dispatch_status')=='completed' and outcome.get('release_confirmed') is True and outcome.get('verification_status')=='verified' and outcome.get('task_success') is True and outcome.get('final_text_empty') else 'FAIL_OR_UNKNOWN'
    (ROOT/'RESULT.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(outcome,ensure_ascii=False,indent=2))

if __name__=='__main__': asyncio.run(main())
