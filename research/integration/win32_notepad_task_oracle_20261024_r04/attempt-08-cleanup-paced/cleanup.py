import asyncio,base64,ctypes,hashlib,json,re,time
from ctypes import wintypes
from pathlib import Path
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.cli_v1.mcp_server import create_server
ROOT=Path(__file__).resolve().parent; HW=24840738; TARGET='notepad'; EXPECT='AI-CTRL-20261024-R04'; ORACLE='08080808080808080808080808080808'; expected={}; logs={}
def text_now():
 u=ctypes.WinDLL('user32',use_last_error=True); P=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM); hs=[]
 def cb(h,_):
  n=ctypes.create_unicode_buffer(128);u.GetClassNameW(h,n,128)
  if n.value=='RichEditD2DPT':hs.append(int(h))
  return True
 u.EnumChildWindows(HW,P(cb),0)
 if len(hs)!=1:raise RuntimeError('edit child ambiguity')
 s=u.SendMessageTimeoutW;s.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)];s.restype=wintypes.LPARAM;n=ctypes.c_size_t()
 if not s(hs[0],14,0,0,2,750,ctypes.byref(n)) or n.value>4096:raise RuntimeError('length read failed')
 b=ctypes.create_unicode_buffer(n.value+1);g=ctypes.c_size_t()
 if not s(hs[0],13,len(b),ctypes.addressof(b),2,750,ctypes.byref(g)):raise RuntimeError('text read failed')
 return {'text':b.value,'characters':int(g.value),'child_hwnd':hs[0]}
def generation():
 b=Win32Backend({TARGET:HW})
 try:return b.target_generation(TARGET)
 finally:b.close()
def oracle(a):
 start=time.monotonic_ns(); cid=a['call_id'];exp=expected.get(cid)
 try:
  g=generation();r=text_now();observed=time.monotonic_ns();out='unknown' if g!=a['target_generation'] or exp is None else ('success' if r['text']==exp else 'failure');logs[cid]={'start_ns':start,'observed_ns':observed,'expected':exp,'actual':r['text'],'characters':r['characters'],'child_hwnd':r['child_hwnd'],'generation_match':g==a['target_generation']}
 except Exception as e:observed=time.monotonic_ns();out='unknown';logs[cid]={'start_ns':start,'observed_ns':observed,'error':repr(e)}
 return {'call_id':cid,'operation_id':a['operation_id'],'target_generation':a['target_generation'],'oracle_id':ORACLE,'outcome':out,'observed_monotonic_ns':observed,'evidence_ref':'oracle-log.json#'+cid}
def save(name,reply):
 o={'isError':bool(getattr(reply,'isError',False)),'content':[]}
 for i,c in enumerate(reply.content):
  if c.type=='text':o['content'].append({'type':'text','text':c.text})
  elif c.type=='image':
   f=f'{name}-{i}.png';d=base64.b64decode(c.data);(ROOT/f).write_bytes(d);o['content'].append({'type':'image','file':f,'sha256':hashlib.sha256(d).hexdigest()})
 (ROOT/f'{name}.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return o
def parse(x):return json.loads(next(c['text'] for c in x['content'] if c['type']=='text'))
def raw(x):return x.get('receipt',{}).get('source',{}).get('raw_report',x)
async def main():
 before=text_now()
 if before['text']!=EXPECT:raise RuntimeError('cleanup precondition changed; no input sent')
 gen=generation();(ROOT/'preflight.json').write_text(json.dumps({'target_hwnd':HW,'before':before,'target_generation':gen},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 server=create_server({TARGET:HW},ROOT/'mcp-calls',session_mode='supervised-win32',supervised_win32_task_oracle=oracle);out={}
 try:
  ob=parse(save('observe',await server.call_tool('interface_observe',{'target':TARGET,'frame':'window_client','region':[0,0,640,240]})));rr=raw(ob)
  if rr.get('status')!='returned' or rr.get('target_generation')!=gen:raise RuntimeError('fresh observation mismatch')
  p={'schema':'agent-interface/program-v1','program_id':'notepad-r04-clear-with-yield','source':{'observation_seq':1,'binding_revision':1,'target_generations':{TARGET:gen}},'authority':{'lease_id':'r04-clear-paced','expires_at_ns':time.monotonic_ns()+15_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':TARGET},{'op':'key_chord','keys':['CTRL','A']},{'op':'wait_update','timeout_ms':50},{'op':'key_chord','keys':['BACKSPACE']},{'op':'wait_update','timeout_ms':50},{'op':'release_all'}]}
  d=parse(save('cleanup-dispatch',await server.call_tool('interface_dispatch',{'program':p,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000})));dr=raw(d);a=(dr.get('supervision') or {}).get('action') or {};res=dr.get('result') or {};cid=dr.get('call_id')
  expected[cid]='';v=parse(save('cleanup-verification',await server.call_tool('interface_verify_task',{'call_id':cid,'wait_for_result_ms':5000})))
  out={'call_id':cid,'dispatch_status':res.get('status'),'emissions':(res.get('execution') or {}).get('emissions'),'release_confirmed':a.get('release_confirmed'),'verification_status':v.get('status'),'task_success':v.get('task_success'),'oracle_outcome':((v.get('task_effect') or {}).get('receipt') or {}).get('outcome') if isinstance((v.get('task_effect') or {}).get('receipt'),dict) else None,'verification_uncertainty':(v.get('task_effect') or {}).get('uncertainty'),'oracle':logs.get(cid)}
 finally:
  try:out['close']=parse(save('close',await server.call_tool('interface_close',{})))
  except Exception as e:out['close_error']=repr(e)
 out['final_readback']=text_now();out['empty']=out['final_readback']['text']=='';out['status']='PASS_CLEANUP' if out.get('dispatch_status')=='completed' and out.get('release_confirmed') is True and out.get('verification_status')=='verified' and out.get('task_success') is True and out['empty'] else 'FAIL_OR_UNKNOWN'
 (ROOT/'oracle-log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'RESULT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':asyncio.run(main())
