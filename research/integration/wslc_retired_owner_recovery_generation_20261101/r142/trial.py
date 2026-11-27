"""Compare late buffered idle response around retirement of a real Xvfb owner."""
import json,os,pathlib,subprocess,sys,threading,time,traceback

def active_ticket_owner(targets,directory,display_name,options):
 owner=GuardedSessionOwner(targets,directory,display_name,**options);owner.get()
 owner._fixture_scope=owner.bridge.cancellation_scope("active-token",cancel_when_idle=True);owner._fixture_scope.__enter__()
 return owner

def main():
 from Xlib import X,XK,display
 from Xlib.ext import xtest
 from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _xvfb_blocking_owner_factory
 from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
 from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
 out=pathlib.Path('/out');mode=os.environ['CONTROL_MODE'];r={'status':'started','mode':mode}
 server=target=conn=owner=fresh=thread=None;resume=threading.Event();entered=threading.Event();thread_result={}
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
  assert not any(bytes(conn.query_keymap())) and not(conn.screen().root.query_pointer().mask & 0x1f00)
  (out/'old').mkdir();owner=OwnedGuardedSessionOwner({'app':window.id},out/'old',':196',process_identity=True,query_worker=True,observation_worker=True,_owner_factory=_xvfb_blocking_owner_factory);owner.get()
  obs=owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='old-observe');g=obs['source']['pointer_binding']['geometry'];(out/'old-mint').mkdir();(out/'old-action').mkdir()
  minted=owner.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'old-mint')
  action_result={}
  def act():
   try:action_result['value']=owner.invoke_guarded('guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'old-action')
   except Exception as error:action_result['error']=repr(error)
  action_thread=threading.Thread(target=act);action_thread.start();until=time.monotonic()+4;marker=out/'old'/'xvfb-owner-sync-entered.json'
  while not marker.exists():
   if time.monotonic()>until:raise RuntimeError('owner did not reach sync boundary')
   time.sleep(.005)
  code_a=conn.keysym_to_keycode(XK.string_to_keysym('a'));code_b=conn.keysym_to_keycode(XK.string_to_keysym('b'))
  def down(code):return bool(bytes(conn.query_keymap())[code//8] & (1<<(code%8)))
  until=time.monotonic()+1
  while not down(code_a) and time.monotonic()<until:time.sleep(.005)
  r['before_cancel_keys']={'a':down(code_a),'b':down(code_b)};assert r['before_cancel_keys']=={'a':True,'b':False}
  started=time.monotonic_ns()
  r['response']=owner.cancel_guarded('old-action')
  r['cancel_elapsed_ms']=(time.monotonic_ns()-started)/1_000_000
  action_thread.join(3);assert not action_thread.is_alive();r['action_result']=action_result
  conn.sync();r['after_cancel_keys']={'a':down(code_a),'b':down(code_b)}
  response=r['response'];assert response.get('status')=='cancel_requested' and response.get('owner_process_retired') is True
  assert response.get('owner_client_disconnect',{}).get('status')=='disconnected'
  assert response.get('owner_release_attempt',{}).get('status')=='readback_verified'
  assert response.get('cleanup_status')=='UNKNOWN' and response.get('replay_allowed') is False
  assert r['after_cancel_keys']=={'a':False,'b':False}
  r['old_close']=owner.close();owner=None;assert r['old_close']['cleanup_status']=='UNKNOWN'
  delayed=json.loads((out/'old'/'xvfb-delayed-request-queued.json').read_text());end_ns=delayed['flushed_ns']+8_500_000_000
  while time.monotonic_ns()<end_ns:time.sleep(.01)
  r['horizon_keys']={'a':down(code_a),'b':down(code_b)};assert not any(r['horizon_keys'].values())
  (out/'fresh').mkdir();fresh=OwnedGuardedSessionOwner({'app':window.id},out/'fresh',':196',process_identity=True,query_worker=True,observation_worker=True)
  fresh.get();obs=fresh.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='fresh')
  g=obs['source']['pointer_binding']['geometry'];(out/'mint').mkdir();(out/'action').mkdir()
  minted=fresh.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'mint')
  action=fresh.invoke_guarded('guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'action')
  end=time.monotonic()+2
  while time.monotonic()<end:
   try:events=json.loads((out/'target-events.json').read_text())
   except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01);continue
   if events['value']=='aa' and sum(e['type']=='release' and e['key']=='a' for e in events['events'])>=2:break
   time.sleep(.01)
  else:raise RuntimeError('fresh task effect or release absent')
  r['target_result']=events;r['release_verified']=action['result']['execution']['releases'][-1]['verified'];r['fresh_close']=fresh.close();fresh=None
  conn.sync();r['input_neutral']=not any(bytes(conn.query_keymap())) and not(conn.screen().root.query_pointer().mask & 0x1f00)
  assert minted['status']=='minted' and action['status']=='completed' and r['release_verified'] and r['input_neutral'] and r['fresh_close']['release_confirmed']
  r['status']='passed'
 except BaseException as error:r.update(status='failed',error=repr(error),traceback=traceback.format_exc())
 finally:
  resume.set()
  if thread is not None:thread.join(3)
  for name,obj in [('owner',owner),('fresh',fresh)]:
   if obj is not None:
    try:r[name+'_cleanup']=obj.close()
    except Exception as error:r[name+'_cleanup_error']=repr(error);r['status']='failed'
  if target is not None:
   (out/'target-stop').write_text('stop')
   try:target.wait(timeout=3)
   except subprocess.TimeoutExpired:target.terminate();target.wait();r['status']='failed'
   r['target_exit']=target.returncode
  if conn is not None:conn.close()
  if server is not None and server.poll() is None:
   server.terminate()
   try:server.wait(timeout=5)
   except subprocess.TimeoutExpired:server.kill();server.wait();r['status']='failed'
  r['server_exit']=None if server is None else server.poll()
  (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
 sys.exit(0 if r['status']=='passed' else 1)
if __name__=='__main__':main()
