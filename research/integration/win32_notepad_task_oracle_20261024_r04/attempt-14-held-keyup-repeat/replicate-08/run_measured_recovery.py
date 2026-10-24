import asyncio, base64, ctypes, hashlib, json, multiprocessing, re, time
from ctypes import wintypes
from pathlib import Path
from runtime.backends.win32_v1.backend import Win32Backend, virtual_key, VK_SHIFT
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components

ROOT=Path(__file__).resolve().parent
TARGET='notepad'; HWND=24840738
HOLD_ENTERED=None

def held_child(gate, entered, targets, action):
    if not gate.wait(10): return
    from runtime.backends.win32_v1.backend import Win32Backend, VK_SHIFT
    from runtime.backends.win32_v1.session import Win32RuntimeSession
    backend=Win32Backend(targets)
    original=backend._send
    def send_then_block(item):
        original(item)
        if (item.type==1 and item.ki.wVk==VK_SHIFT and not (item.ki.dwFlags & 0x0002)):
            entered.set()
            while True:
                time.sleep(0.05)
    backend._send=send_then_block
    source=action['program']['source']
    Win32RuntimeSession(backend).dispatch(action['program'],
        current_observation_seq=source['observation_seq'],
        current_binding_revision=source['binding_revision'])

class HeldAfterNativeSendFactory:
    def __init__(self, targets, root):
        self.targets=dict(targets); self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.ctx=multiprocessing.get_context('spawn'); self.entered=self.ctx.Event(); self.gate=None; self.process=None
    def __call__(self, action):
        self.gate=self.ctx.Event(); self.entered.clear()
        self.process=self.ctx.Process(target=held_child,args=(self.gate,self.entered,self.targets,action),daemon=True)
        return self.process, lambda: __import__('runtime.guarded_win32_v1.win32_process_identity',fromlist=['Win32ProcessIdentityReader']).Win32ProcessIdentityReader()(self.process), self.gate.set
    def read_result(self, process):
        raise RuntimeError('held producer unexpectedly returned without a retained packet')

def save(name, reply):
    row={'isError':bool(getattr(reply,'isError',False)),'content':[]}
    for i,c in enumerate(reply.content):
        if c.type=='text': row['content'].append({'type':'text','text':c.text})
        elif c.type=='image':
            f=f'{name}-{i}.png'; data=base64.b64decode(c.data); (ROOT/f).write_bytes(data)
            row['content'].append({'type':'image','file':f,'mimeType':c.mimeType,'sha256':hashlib.sha256(data).hexdigest()})
    (ROOT/f'{name}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return row
def parsed(row): return json.loads(next(x['text'] for x in row['content'] if x['type']=='text'))
def raw(obj): return obj.get('receipt',{}).get('source',{}).get('raw_report',obj)
def key_state():
    b=Win32Backend({TARGET:HWND})
    try:
        g=b.target_generation(TARGET); state=b._key_down_state(virtual_key('SHIFT'),TARGET); witness=b._last_state_query_witness
        return {'generation':g,'shift_down':state,'witness':witness}
    finally:b.close()

def document_state():
    u=ctypes.WinDLL('user32',use_last_error=True)
    proc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    found=[]
    def visit(h,_):
        name=ctypes.create_unicode_buffer(128);u.GetClassNameW(h,name,128)
        if name.value=='RichEditD2DPT': found.append(int(h))
        return True
    u.EnumChildWindows(HWND,proc(visit),0)
    if len(found)!=1: raise RuntimeError(f'expected one edit control, got {len(found)}')
    h=found[0];send=u.SendMessageTimeoutW
    send.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
    send.restype=wintypes.LPARAM
    length=ctypes.c_size_t()
    if not send(h,14,0,0,2,750,ctypes.byref(length)) or length.value>4096:
        raise RuntimeError('bounded WM_GETTEXTLENGTH failed')
    buffer=ctypes.create_unicode_buffer(length.value+1);read=ctypes.c_size_t()
    if not send(h,13,len(buffer),ctypes.addressof(buffer),2,750,ctypes.byref(read)):
        raise RuntimeError('bounded WM_GETTEXT failed')
    return {'text':buffer.value,'characters':int(read.value),'child_hwnd':h}
async def main():
    before=key_state()
    before_document=document_state()
    if (before['generation'] is None or before['shift_down'] is not False
            or before_document['text']!=''):
        raise RuntimeError('target generation/SHIFT-up/empty-document precondition not established; no input sent')
    # Build production native supervisor and real recovery/observer helpers; only producer is fault-injected after a real SendInput.
    factory_box={}
    def owner_factory(targets, root, display_name): return create_native_win32_components(targets,root)[0]
    def producer_factory(targets,root,display_name):
        f=HeldAfterNativeSendFactory(targets,root); factory_box['factory']=f; return f
    server=create_server({TARGET:HWND},ROOT/'mcp-calls',session_mode='supervised-win32',
        _supervised_win32_owner_factory=owner_factory,_supervised_win32_producer_factory=producer_factory)
    result={'scope':'SHIFT-down accepted; producer blocks at key-up backend boundary before SendInput; production supervisor recovery','preflight':before,'document_before':before_document,'limitations':['Producer is held before invoking native SendInput for SHIFT-up, after the preceding native SHIFT-down returned; this does not simulate a kernel-level hang inside SendInput.','No claim about arbitrary platform-I/O stalls.','No WSLc allocation used.','No task-success outcome is claimed for this recovery-only action.']}
    dispatch_task=None; call_id=None; factory=None
    try:
        ob=parsed(save('observe',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]}))); rr=raw(ob)
        if rr.get('status')!='returned' or rr.get('target_generation')!=before['generation']: raise RuntimeError('public observation/generation preflight mismatch')
        program={'schema':'agent-interface/program-v1','program_id':'notepad-r04-held-keyup-r14-08','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:before['generation']}},'authority':{'lease_id':'r04-held-keyup-r14-08','expires_at_ns':time.monotonic_ns()+20_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_state','key':'SHIFT','down':True},{'op':'key_state','key':'SHIFT','down':False},{'op':'release_all'}]}
        dispatch_task=asyncio.create_task(server.call_tool('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000}))
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            factory=factory_box.get('factory')
            if factory and factory.entered.wait(0.05): break
            await asyncio.sleep(0.05)
        if not factory or not factory.entered.is_set():
            result['fault_injection']='producer did not reach the post-SendInput hold; no cancel was issued'
            if dispatch_task.done(): result['dispatch']=parsed(save('dispatch',await dispatch_task))
            raise RuntimeError('fault injection did not enter bounded hold')
        result['hold_entered_monotonic_ns']=time.monotonic_ns()
        result['state_during_hold']=key_state()
        req_root=ROOT/'mcp-calls'
        for _ in range(100):
            candidates=list(req_root.glob('*/request.json'))
            for q in candidates:
                try:
                    req=json.loads(q.read_text(encoding='utf-8'))
                    if (req.get('arguments',{}).get('program',{}).get('program_id')==program['program_id']): call_id=q.parent.name; break
                except Exception: pass
            if call_id: break
            await asyncio.sleep(0.02)
        if not call_id: raise RuntimeError('could not identify unique dispatch call ID')
        cancel_started=time.monotonic_ns()
        cancel=parsed(save('cancel',await server.call_tool('interface_cancel',{'call_id':call_id})))
        cancel_received=time.monotonic_ns(); result['cancel']=cancel; result['cancel_elapsed_ms']=(cancel_received-cancel_started)/1_000_000
        if dispatch_task.done():
            result['dispatch']=parsed(save('dispatch',await dispatch_task))
        else:
            result['dispatch_wait']='still pending after interface_cancel returned'
            result['dispatch']=parsed(save('dispatch-after-cancel',await asyncio.wait_for(dispatch_task,5)))
        result['cancel_started_monotonic_ns']=cancel_started
        result['cancel_received_monotonic_ns']=cancel_received
        result['state_after_supervised_recovery']=key_state()
        if result['state_after_supervised_recovery']['shift_down'] is not False and factory.process and not factory.process.is_alive():
            b=Win32Backend({TARGET:HWND})
            try:
                b.held_keys['SHIFT']=VK_SHIFT; b.held_key_targets['SHIFT']=TARGET
                result['emergency_release']=b.release_all()
            finally:b.close()
            result['state_after_emergency_check']=key_state()
        c=save('results',await server.call_tool('interface_results',{'call_id':call_id})); result['retained_result']=parsed(c)
    finally:
        try: result['close']=parsed(save('close',await server.call_tool('interface_close',{})))
        except Exception as e: result['close_error']=repr(e)
    action=(result.get('dispatch') or {}).get('receipt',{}).get('source',{}).get('raw_report',{})
    public_result=action.get('result') or {}
    retained_action=(result.get('retained_result') or {}).get('action') or {}
    retained_cancel=(result.get('retained_result') or {}).get('cancellation') or {}
    custody=retained_cancel.get('result') or {}
    after_document=document_state()
    result['document_after']=after_document
    timing={'cleanup_requested_monotonic_ns':custody.get('cleanup_requested_monotonic_ns'),
        'recovery_completed_monotonic_ns':custody.get('recovery_completed_monotonic_ns'),
        'cleanup_latency_ns':custody.get('cleanup_latency_ns'),
        'cleanup_requested_perf_counter_ns':custody.get('cleanup_requested_perf_counter_ns'),
        'recovery_completed_perf_counter_ns':custody.get('recovery_completed_perf_counter_ns'),
        'cleanup_latency_perf_counter_ns':custody.get('cleanup_latency_perf_counter_ns'),
        'cleanup_deadline_ns':custody.get('cleanup_deadline_ns')}
    if all(type(timing[k]) is int for k in ('cleanup_requested_monotonic_ns','recovery_completed_monotonic_ns','cleanup_latency_ns','cleanup_requested_perf_counter_ns','recovery_completed_perf_counter_ns','cleanup_latency_perf_counter_ns','cleanup_deadline_ns')):
        timing['derived_latency_ns']=timing['recovery_completed_monotonic_ns']-timing['cleanup_requested_monotonic_ns']
        timing['deadline_margin_ns']=timing['cleanup_deadline_ns']-timing['recovery_completed_monotonic_ns']
        timing['high_resolution_interval_consistent']=timing['cleanup_latency_perf_counter_ns']==timing['recovery_completed_perf_counter_ns']-timing['cleanup_requested_perf_counter_ns']
        timing['cancel_response_to_recovery_ns']=timing['recovery_completed_monotonic_ns']-result['cancel_received_monotonic_ns']
    result['recovery_timing']=timing
    result['success_gate']={'dispatch_status':public_result.get('status'),
        'dispatch_release_confirmed':public_result.get('release_confirmed'),
        'retained_action_status':retained_action.get('status'),
        'retained_cancel_status':retained_cancel.get('status'),
        'retained_cancel_release_confirmed':retained_cancel.get('release_confirmed'),
        'shift_down_observed_during_hold':(result.get('state_during_hold') or {}).get('shift_down') is True,
        'shift_up_after':(result.get('state_after_supervised_recovery') or {}).get('shift_down') is False,
        'same_generation':(result.get('state_after_supervised_recovery') or {}).get('generation')==before['generation'],
        'document_still_empty':after_document.get('text')=='',
        'deadline_passed':type(timing.get('recovery_completed_monotonic_ns')) is int and type(timing.get('cleanup_deadline_ns')) is int and timing['recovery_completed_monotonic_ns']<timing['cleanup_deadline_ns'],
        'high_resolution_interval_present':type(timing.get('cleanup_latency_perf_counter_ns')) is int and timing.get('high_resolution_interval_consistent') is True,
        'task_success':None,'replay_allowed':public_result.get('replay_allowed')}
    gate=result['success_gate']
    result['status']='PASS_SCOPED_BOUNDED_RECOVERY' if all((gate['dispatch_status']=='recovered',gate['dispatch_release_confirmed'] is True,gate['retained_action_status']=='recovered',gate['retained_cancel_status']=='recovered',gate['retained_cancel_release_confirmed'] is True,gate['shift_down_observed_during_hold'],gate['shift_up_after'],gate['same_generation'],gate['document_still_empty'],gate['deadline_passed'],gate['high_resolution_interval_present'],gate['task_success'] is None,gate['replay_allowed'] is False)) else 'FAIL_OR_UNKNOWN'
    (ROOT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': asyncio.run(main())
