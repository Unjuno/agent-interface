import json,os,pathlib,subprocess,time,traceback,sys,threading

def main():
 from Xlib import X,XK,display
 from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
 from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _xvfb_blocking_owner_factory
 from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
 from runtime.guarded_x11_v1.private_display_recovery import PrivateDisplayRecovery
 out=pathlib.Path('/out');r={'status':'started'};old_display=new_display=old_owner=new_owner=old_target=new_target=conn=conn2=None;action_thread=None
 def open_target(session,folder):
  folder.mkdir();env=dict(os.environ,DISPLAY=session.display,XAUTHORITY=str(session.authority),TEST_DISPLAY=session.display,TARGET_OUT=str(folder))
  proc=subprocess.Popen(['python3','-B','/target.py'],env=env,stdout=(folder/'stdout').open('wb'),stderr=(folder/'stderr').open('wb'))
  end=time.monotonic()+4
  while not (folder/'target-ready.json').exists():
   if proc.poll() is not None or time.monotonic()>end:raise RuntimeError('target unavailable')
   time.sleep(.01)
  return proc,json.loads((folder/'target-ready.json').read_text())['xid']
 def connect(session,xid):
  os.environ['XAUTHORITY']=str(session.authority);d=display.Display(session.display);w=d.create_resource_object('window',xid);d.set_input_focus(w,X.RevertToParent,X.CurrentTime);d.sync();return d,w
 try:
  old_display=PrivateDisplayOwner('/tmp/r153-old');s=old_display.start(timeout_s=4);r['old_display']=s.display
  old_target,xid=open_target(s,out/'old-target');conn,window=connect(s,xid)
  old_owner=OwnedGuardedSessionOwner({'app':xid},out/'old',s.display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,xauthority=str(s.authority),_owner_factory=_xvfb_blocking_owner_factory);old_owner.get()
  # Public guarded operations are executed directly on the real child.
  (out/'old-observe').mkdir();ob=old_owner.invoke_guarded('guarded_observe',{},out/'old-observe');r['old_observe']=ob
  source=ob['source'];g=source['pointer_binding']['geometry'];(out/'old-mint').mkdir();m=old_owner.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':source['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'old-mint');r['old_mint']=m
  (out/'old-action').mkdir();action={}
  def act():
   try:action['value']=old_owner.invoke_guarded('guarded_input',{'alias':'field','offset':m['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'old-action')
   except Exception as e:action['error']=repr(e)
  action_thread=threading.Thread(target=act);action_thread.start();marker=out/'old'/'xvfb-owner-sync-entered.json';end=time.monotonic()+4
  while not marker.exists():
   if time.monotonic()>end:raise RuntimeError('old owner not blocked')
   time.sleep(.005)
  code=conn.keysym_to_keycode(XK.string_to_keysym('a'));r['old_a_before']=bool(bytes(conn.query_keymap())[code//8] & (1<<(code%8)));assert r['old_a_before']
  recovery=PrivateDisplayRecovery(old_display,old_owner);r['recovery']=recovery.cancel_guarded('old-action',deadline_monotonic_ns=time.monotonic_ns()+5_000_000_000);action_thread.join(3);r['old_action']=action
  assert not action_thread.is_alive() and r['recovery']['display_retirement']['status']=='retired' and r['recovery']['fresh_display_allowed'] and not r['recovery']['replay_allowed'] and r['recovery']['cleanup_status']=='UNKNOWN'
  r['old_display_exit']=old_display._process.poll();assert r['old_display_exit'] is not None
  try:conn.close()
  except Exception as e:r['expected_closed_old_connection']=type(e).__name__
  conn=None
  new_display=PrivateDisplayOwner('/tmp/r153-new');ns=new_display.start(timeout_s=4);r['new_display']=ns.display
  assert ns.display==s.display
  probe_code="""import sys
from Xlib import display
try:
 d=display.Display();d.sync();d.close();print('connected')
except Exception as e:
 print(type(e).__name__);sys.exit(1)
"""
  def auth_probe(authority):
   p=subprocess.run(['python3','-B','-c',probe_code],env=dict(os.environ,DISPLAY=ns.display,XAUTHORITY=str(authority)),capture_output=True,text=True,timeout=3)
   return {'returncode':p.returncode,'stdout':p.stdout.strip()}
  r['old_authority_probe']=auth_probe(s.authority);r['new_authority_probe']=auth_probe(ns.authority)
  assert r['old_authority_probe']['returncode']!=0 and r['new_authority_probe']=={'returncode':0,'stdout':'connected'}
  new_target,nxid=open_target(ns,out/'new-target');conn2,window2=connect(ns,nxid)
  new_owner=OwnedGuardedSessionOwner({'app':nxid},out/'new',ns.display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,xauthority=str(ns.authority));new_owner.get()
  (out/'new-observe').mkdir();nob=new_owner.invoke_guarded('guarded_observe',{},out/'new-observe');ng=nob['source']['pointer_binding']['geometry'];(out/'new-mint').mkdir();nm=new_owner.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':nob['source']['sequence'],'point':[ng[0]+20,ng[1]+20],'region_size':[12,12]},out/'new-mint')
  (out/'new-action').mkdir();na=new_owner.invoke_guarded('guarded_input',{'alias':'field','offset':nm['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'new-action');r['new_action']=na
  end=time.monotonic()+2
  while time.monotonic()<end:
   try:e=json.loads((out/'new-target'/'target-events.json').read_text())
   except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01);continue
   if e['value']=='a' and any(x['type']=='release' and x['key']=='a' for x in e['events']):break
   time.sleep(.01)
  else:raise RuntimeError('fresh target effect/release absent')
  r['new_target_result']=e;r['new_close']=new_owner.close();new_owner=None;assert na['status']=='completed' and r['new_close']['release_confirmed']
  delayed=json.loads((out/'old'/'xvfb-delayed-request-queued.json').read_text());horizon=delayed['flushed_ns']+8_500_000_000
  while time.monotonic_ns()<horizon:time.sleep(.01)
  r['horizon_observed_ns']=time.monotonic_ns();r['delay_flushed_ns']=delayed['flushed_ns']
  r['new_target_horizon']=json.loads((out/'new-target'/'target-events.json').read_text())
  keymap=bytes(conn2.query_keymap());codes={k:conn2.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('a','b')};r['new_horizon_keys']={k:bool(keymap[v//8] & (1<<(v%8))) for k,v in codes.items()}
  assert not any(r['new_horizon_keys'].values()) and not any(x['key']=='b' and x['type']=='press' for x in r['new_target_horizon']['events'])
  r['status']='passed'
 except BaseException as e:r.update(status='failed',error=repr(e),traceback=traceback.format_exc())
 finally:
  if action_thread is not None:action_thread.join(3)
  for name,obj in [('old_owner',old_owner),('new_owner',new_owner)]:
   if obj:
    try:r[name+'_cleanup']=obj.close()
    except Exception as e:r[name+'_cleanup_error']=repr(e)
  for name,proc,folder in [('old',old_target,out/'old-target'),('new',new_target,out/'new-target')]:
   if proc:
    if proc.poll() is None:
     (folder/'target-stop').write_text('stop')
     try:proc.wait(timeout=2)
     except subprocess.TimeoutExpired:proc.terminate();proc.wait()
    r[name+'_target_exit']=proc.returncode
  for d in (conn,conn2):
   if d:
    try:d.close()
    except Exception:pass
  for name,obj in [('old_display',old_display),('new_display',new_display)]:
   if obj:
    try:r[name+'_close']=obj.close(timeout_s=3)
    except Exception as e:r[name+'_close_error']=repr(e)
  (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
 return 0 if r['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
