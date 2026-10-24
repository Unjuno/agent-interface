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
async def main():
    before=key_state()
    if before['generation'] is None or before['shift_down'] is not False: raise RuntimeError('target generation/SHIFT-up precondition not established; no input sent')
    # Build production native supervisor and real recovery/observer helpers; only producer is fault-injected after a real SendInput.
    factory_box={}
    def owner_factory(targets, root, display_name): return create_native_win32_components(targets,root)[0]
    def producer_factory(targets,root,display_name):
        f=HeldAfterNativeSendFactory(targets,root); factory_box['factory']=f; return f
    server=create_server({TARGET:HWND},ROOT/'mcp-calls',session_mode='supervised-win32',
        _supervised_win32_owner_factory=owner_factory,_supervised_win32_producer_factory=producer_factory)
    result={'scope':'native SendInput accepted SHIFT-down, producer held after return, production supervisor recovery','preflight':before,'limitations':['Fault injection blocks after the native SendInput call returns; it does not block inside the Windows API.','No claim about arbitrary platform-I/O stalls.','No WSLc allocation used.']}
    dispatch_task=None; call_id=None; factory=None
    try:
        ob=parsed(save('observe',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]}))); rr=raw(ob)
        if rr.get('status')!='returned' or rr.get('target_generation')!=before['generation']: raise RuntimeError('public observation/generation preflight mismatch')
        program={'schema':'agent-interface/program-v1','program_id':'notepad-r04-held-shift-cancel','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:before['generation']}},'authority':{'lease_id':'r04-held-shift','expires_at_ns':time.monotonic_ns()+20_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_state','key':'SHIFT','down':True},{'op':'key_state','key':'SHIFT','down':False},{'op':'release_all'}]}
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
    result['success_gate']={'cancellation_status':((result.get('cancel') or {}).get('cancellation') or {}).get('status'),
        'cancel_release_confirmed':(result.get('cancel') or {}).get('release_confirmed'),
        'dispatch_status':((action.get('supervision') or {}).get('action') or {}).get('status'),
        'dispatch_release_confirmed':(result.get('dispatch') or {}).get('release_confirmed'),
        'shift_up_after':(result.get('state_after_supervised_recovery') or {}).get('shift_down') is False,
        'task_success':None,'replay_allowed':False}
    result['status']='PASS_INJECTED_POST_SEND_RECOVERY' if result['success_gate']['cancellation_status']=='recovered' and result['success_gate']['cancel_release_confirmed'] is True and result['success_gate']['dispatch_release_confirmed'] is True and result['success_gate']['shift_up_after'] else 'FAIL_OR_UNKNOWN'
    (ROOT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': asyncio.run(main())
