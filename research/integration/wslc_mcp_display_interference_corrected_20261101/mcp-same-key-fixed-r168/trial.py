import asyncio,json,os,pathlib,subprocess,time,traceback,sys

def main():
 from Xlib import X,XK,display
 from Xlib.ext import xtest
 from runtime.cli_v1.mcp_server import create_server
 from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata,_xvfb_blocking_owner_factory
 out=pathlib.Path('/out');r={'status':'started'};server=target=conn=None;servers=[]
 async def experiment():
  nonlocal servers
  opts=dict(display_name=':196',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_observation_worker=True,guarded_owned_process=True)
  first=create_server({'app':window.id},out/'first',_guarded_owner_factory=_xvfb_blocking_owner_factory,**opts)
  second=create_server({'app':window.id},out/'second',_guarded_owner_factory=_xvfb_blocking_owner_factory,**opts);servers=[first,second]
  async def call(s,n,args):return _metadata(await asyncio.wait_for(s.call_tool(n,args),timeout=6))
  async def mint(s):
   obs=await call(s,'interface_guarded_observe',{});assert obs['status']=='observed',obs
   return await call(s,'interface_guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[30,30],'region_size':[12,12]})
  m1=await mint(first);r['first_mint']=m1
  r['first_input']=await call(first,'interface_guarded_input',{'alias':'field','offset':m1['offset'],'interaction':'keyboard','observe_after':False,'wait_for_result_ms':0,'tail':[{'op':'key_chord','keys':['a']}]})
  assert r['first_input']['status']=='pending',r['first_input'];marker=out/'first'/'xvfb-owner-sync-entered.json';end=time.monotonic()+4
  while not marker.exists():
   if time.monotonic()>end:raise RuntimeError('first owner not blocked')
   await asyncio.sleep(.005)
  code_a=conn.keysym_to_keycode(XK.string_to_keysym('a'));code_c=conn.keysym_to_keycode(XK.string_to_keysym('c'))
  def down(code):return bool(bytes(conn.query_keymap())[code//8] & (1<<(code%8)))
  r['before_second']={'a':down(code_a),'c':down(code_c)};assert r['before_second']=={'a':True,'c':False}
  xtest.fake_input(conn,X.KeyRelease,detail=code_a);conn.sync();r['after_fixture_release']={'a':down(code_a)};assert not down(code_a)
  m2=await mint(second);r['second_mint']=m2
  r['second_input']=await call(second,'interface_guarded_input',{'alias':'field','offset':m2['offset'],'interaction':'keyboard','observe_after':False,'wait_for_result_ms':0,'tail':[{'op':'key_chord','keys':['a']}]})
  assert r['second_input']['status']=='pending',r['second_input'];marker2=out/'second'/'xvfb-owner-sync-entered.json';end=time.monotonic()+4
  while not marker2.exists():
   if time.monotonic()>end:raise RuntimeError('second owner not blocked')
   await asyncio.sleep(.005)
  r['second_hold_before_cancel']={'a':down(code_a)};assert down(code_a)
  r['first_cancel']=await call(first,'interface_guarded_cancel',{'call_id':r['first_input']['call_id']})
  r['first_close_initial']=await call(first,'interface_close',{})
  deadline=time.monotonic()+6;history=[]
  while time.monotonic()<deadline:
   terminal=await call(first,'interface_results',{'call_id':r['first_input']['call_id'],'include_image':False})
   cancellation=terminal.get('cancellation') or {};history.append({'status':terminal.get('status'),'cancellation_status':cancellation.get('status'),'observed_ns':time.monotonic_ns()})
   if cancellation.get('status') in ('completed','unknown'):
    r['first_terminal']=terminal;break
   await asyncio.sleep(.02)
  else:raise RuntimeError('cancellation did not reach a terminal receipt')
  r['poll_history']=history;r['second_hold_after_first_cancel']={'a':down(code_a)}
  r['first_close_final']=await call(first,'interface_close',{});servers.remove(first)
  r['second_cancel']=await call(second,'interface_guarded_cancel',{'call_id':r['second_input']['call_id']})
  deadline=time.monotonic()+6
  while time.monotonic()<deadline:
   terminal2=await call(second,'interface_results',{'call_id':r['second_input']['call_id'],'include_image':False})
   if (terminal2.get('cancellation') or {}).get('status') in ('completed','unknown'):
    r['second_terminal']=terminal2;break
   await asyncio.sleep(.02)
  else:raise RuntimeError('second cancellation did not reach terminal receipt')
  r['second_close_final']=await call(second,'interface_close',{});servers.remove(second)
  delayed=json.loads((out/'first'/'xvfb-delayed-request-queued.json').read_text());delayed2=json.loads((out/'second'/'xvfb-delayed-request-queued.json').read_text());horizon=max(delayed['flushed_ns'],delayed2['flushed_ns'])+8_500_000_000
  while time.monotonic_ns()<horizon:await asyncio.sleep(.01)
  code_b=conn.keysym_to_keycode(XK.string_to_keysym('b'));r['horizon']={'a':down(code_a),'b':down(code_b),'c':down(code_c)};r['target_result']=json.loads((out/'target-events.json').read_text())
  r['injections']={name:[json.loads(line) for line in (out/name/'xvfb-delayed-injections.jsonl').read_text().splitlines()] for name in ('first','second')}
  assert all(len(rows)==1 for rows in r['injections'].values());r['status']='passed'
 async def cleanup():
  for s in servers:
   try:await asyncio.wait_for(s.call_tool('interface_close',{}),timeout=4)
   except Exception as e:r.setdefault('close_errors',[]).append(repr(e))
 try:
  server=subprocess.Popen(['Xvfb',':196','-screen','0','640x480x24','-nolisten','tcp'],stdout=(out/'xvfb.log').open('wb'),stderr=subprocess.STDOUT)
  for _ in range(100):
   if server.poll() is not None:raise RuntimeError('Xvfb exited')
   try:conn=display.Display(':196');break
   except Exception:time.sleep(.05)
  if conn is None:raise RuntimeError('Xvfb unavailable')
  target=subprocess.Popen(['python3','-B','/target.py'],stdout=(out/'target.stdout').open('wb'),stderr=(out/'target.stderr').open('wb'),env=dict(os.environ,TEST_DISPLAY=':196'))
  end=time.monotonic()+4
  while not (out/'target-ready.json').exists():
   if target.poll() is not None or time.monotonic()>end:raise RuntimeError('target unavailable')
   time.sleep(.01)
  ready=json.loads((out/'target-ready.json').read_text());window=conn.create_resource_object('window',ready['xid']);conn.set_input_focus(window,X.RevertToParent,X.CurrentTime);conn.sync()
  async def run():
   try:await experiment()
   finally:await cleanup()
  asyncio.run(run())
 except BaseException as e:r.update(status='failed',error=repr(e),traceback=traceback.format_exc())
 finally:
  if target is not None:
   (out/'target-stop').write_text('stop')
   try:target.wait(timeout=3)
   except subprocess.TimeoutExpired:target.terminate();target.wait();r['status']='failed'
   r['target_exit']=target.returncode
  if conn:conn.close()
  if server and server.poll() is None:
   server.terminate()
   try:server.wait(timeout=5)
   except subprocess.TimeoutExpired:server.kill();server.wait();r['status']='failed'
  r['server_exit']=None if server is None else server.poll();(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
 return 0 if r['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
