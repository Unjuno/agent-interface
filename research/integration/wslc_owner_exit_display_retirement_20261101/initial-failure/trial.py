"""Experimental private display custody comparison; not production integration."""
import json, os, pathlib, signal, subprocess, sys, time, traceback
from Xlib import X, XK, display
from Xlib.ext import xtest
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.guarded_x11_v1.cancel_supervisor import x11_cancel_worker
import threading

def blocked_owner_factory(targets, directory, display_name, options):
    owner=GuardedSessionOwner(targets,directory,display_name,**options); original_get=owner.get
    def get():
        session=original_get(); original=xtest.fake_input; seen={'value':False}
        def block_after_press(connection,event_type,*args,**kwargs):
            result=original(connection,event_type,*args,**kwargs)
            if event_type==X.KeyPress and not seen['value']:
                seen['value']=True;connection.sync()
                (pathlib.Path(directory)/'press-observed.json').write_text(json.dumps({'ns':time.monotonic_ns(),'pid':os.getpid()}))
                time.sleep(8)
            return result
        xtest.fake_input=block_after_press
        return session
    owner.get=get;return owner

def authority_controlled_worker(request):
    root=pathlib.Path(request['owner_data_directory'])
    (root/'cleanup-worker-entered.json').write_text(json.dumps({'ns':time.monotonic_ns(),'mode':os.environ['CONTROL_MODE']}))
    if os.environ['CONTROL_MODE']=='wrong':os.environ['XAUTHORITY']=str(root/'missing-authority')
    return x11_cancel_worker(request)

def main():
    out=pathlib.Path('/out'); mode=os.environ['CONTROL_MODE']; r={'status':'started','mode':mode,'events':[]}
    def mark(name,**kw):r['events'].append({'name':name,'ns':time.monotonic_ns(),**kw})
    servers=[]; owners=[]; sessions={}; targets=[]; connections=[]; fresh=None; old=None; oldowner=None; oldthread=None; pidfd=None; held=False
    def start_server(number):
        owner=PrivateDisplayOwner(out/f'display-owner-{number}'); session=owner.start(timeout_s=5)
        owners.append(owner); sessions[number]=session; p=owner._process;servers.append(p)
        os.environ['XAUTHORITY']=str(session.authority)
        c=display.Display(session.display);connections.append(c);return p,c
    def start_target(number,name,conn):
        p=out/name;p.mkdir();t=subprocess.Popen(['python3','-B','/target.py'],env=dict(os.environ,TEST_DISPLAY=sessions[number].display, XAUTHORITY=str(sessions[number].authority),TARGET_OUT=str(p)),stdout=(p/'stdout').open('wb'),stderr=(p/'stderr').open('wb'));targets.append((t,p))
        until=time.monotonic()+4
        while not (p/'target-ready.json').exists():
            if t.poll() is not None or time.monotonic()>=until:raise RuntimeError('target unavailable')
            time.sleep(.01)
        ready=json.loads((p/'target-ready.json').read_text()); w=conn.create_resource_object('window',ready['xid']);conn.set_input_focus(w,X.RevertToParent,X.CurrentTime);conn.sync();return w,p
    try:
        if mode not in ('retire','keep'):raise RuntimeError('unknown mode')
        old,oc=start_server(194);pidfd=os.pidfd_open(old.pid);mark('old_server_started',pid=old.pid)
        os.environ['XAUTHORITY']=str(out/'invalid-parent-authority');r['parent_auth_before_owner']=os.environ['XAUTHORITY']
        oldwin,oldout=start_target(194,'old-target',oc)
        code=oc.keysym_to_keycode(XK.string_to_keysym('a'))
        def down(c,k):return bool(bytes(c.query_keymap())[k//8] & (1 << (k%8)))
        assert not down(oc,code);(out/'old-owner').mkdir();(out/'old-mint').mkdir();(out/'old-action').mkdir()
        oldowner=OwnedGuardedSessionOwner({'app':oldwin.id},out/'old-owner',sessions[194].display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,_owner_factory=blocked_owner_factory,xauthority=str(sessions[194].authority))
        oldowner.get();r['parent_auth_after_owner']=os.environ['XAUTHORITY'];assert r['parent_auth_after_owner']==r['parent_auth_before_owner'];(out/'old-observe').mkdir();oldobs=oldowner.invoke_guarded('guarded_observe',{},out/'old-observe')
        g=oldobs['source']['pointer_binding']['geometry'];oldmint=oldowner.invoke_guarded('guarded_mint',{'alias':'oldfield','source_sequence':oldobs['source']['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'old-mint')
        oldcall={}
        def old_action():
            try:oldcall['result']=oldowner.invoke_guarded('guarded_input',{'alias':'oldfield','offset':oldmint['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'old-action')
            except Exception as e:oldcall['error']=repr(e)
        oldthread=threading.Thread(target=old_action);oldthread.start()
        until=time.monotonic()+4
        while time.monotonic()<until:
            try:value=json.loads((oldout/'target-events.json').read_text())['value']
            except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01);continue
            if value=='a' and (out/'old-owner'/'press-observed.json').exists():break
            time.sleep(.01)
        else:raise RuntimeError('guarded old press not observed')
        r['old_key_down_before_stop']=down(oc,code);assert r['old_key_down_before_stop'];held=True;mark('old_effect_and_hold')
        oldowner._process.terminate();oldowner._process.join(3)
        assert not oldowner._process.is_alive();mark('old_owner_killed',exitcode=oldowner._process.exitcode)
        r['old_cancel']=oldowner.cancel_guarded('old-action',deadline_monotonic_ns=time.monotonic_ns()+4_000_000_000);mark('old_cancel_returned')
        conn=oc;conn.sync();r['a_down_after_cancel']=down(conn,code);r['old_target_before_fixture']=json.loads((oldout/'target-events.json').read_text())
        assert r['old_cancel']['status']=='cancel_unconfirmed' and r['old_cancel']['cleanup_status']=='UNKNOWN' and not r['old_cancel']['replay_allowed'] and r['old_cancel']['owner_input_obligations']['keys']['a']==code
        oldthread.join(3);r['old_call']=oldcall;r['old_thread_alive']=oldthread.is_alive()
        if oldthread.is_alive():raise RuntimeError('old guarded call did not retire')
        if mode=='retire':
            assert r['a_down_after_cancel'];r['old_display_retirement']=owners[0].retire(timeout_s=3)
            assert r['old_display_retirement']['status']=='retired';held=False;mark('old_display_retired')
            new,conn=start_server(195);mark('fresh_display_started',pid=new.pid)
            freshwin,freshout=start_target(195,'fresh-target',conn);fresh_session=sessions[195]
        else:
            if r['a_down_after_cancel']:
                xtest.fake_input(conn,X.KeyRelease,code);conn.sync();held=False;mark('fixture_release_old_hold')
            else:held=False
            assert not down(conn,code)
            freshwin,freshout=start_target(194,'fresh-target',conn);fresh_session=sessions[194]
        r['fresh_neutral_before_task']=not any(bytes(conn.query_keymap())) and not (conn.screen().root.query_pointer().mask & 0x1f00)
        assert r['fresh_neutral_before_task'];(out/'fresh-owner').mkdir()
        fresh=OwnedGuardedSessionOwner({'app':freshwin.id},out/'fresh-owner',fresh_session.display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,xauthority=str(fresh_session.authority))
        fresh.get();r['parent_auth_after_fresh']=os.environ['XAUTHORITY'];assert r['parent_auth_after_fresh']==r['parent_auth_before_owner'];(out/'fresh-observe').mkdir();obs=fresh.invoke_guarded('guarded_observe',{},out/'fresh-observe');g=obs['source']['pointer_binding']['geometry'];(out/'mint').mkdir();(out/'action').mkdir()
        minted=fresh.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'mint')
        action=fresh.invoke_guarded('guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'action');r['mint']=minted;r['action']=action;mark('fresh_action_returned')
        until=time.monotonic()+2
        while time.monotonic()<until:
            try: result=json.loads((freshout/'target-events.json').read_text())
            except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01);continue
            if result['value']=='a' and any(e['type']=='release' and e['key']=='a' for e in result['events']):break
            time.sleep(.01)
        else:raise RuntimeError('fresh target effect/release missing')
        r['fresh_target']=result;r['fresh_close']=fresh.close();fresh=None;conn.sync();r['fresh_neutral_after_task']=not any(bytes(conn.query_keymap())) and not (conn.screen().root.query_pointer().mask & 0x1f00)
        assert minted['status']=='minted' and action['status']=='completed' and action['result']['execution']['releases'][-1]['verified'] and r['fresh_neutral_after_task'];r['status']='passed'
    except BaseException as e:r.update(status='failed',error=repr(e),traceback=traceback.format_exc())
    finally:
        if held and old is not None and old.poll() is None:
            try:signal.pidfd_send_signal(pidfd,signal.SIGCONT);xtest.fake_input(oc,X.KeyRelease,code);oc.sync();r['fallback_release']=True
            except Exception as e:r['fallback_release_error']=repr(e);r['status']='failed'
        if oldowner is not None:
            try:r['old_owner_close']=oldowner.close()
            except Exception as e:r['old_owner_close_error']=repr(e);r['status']='failed'
        if oldthread is not None and oldthread.is_alive():oldthread.join(3)
        if fresh is not None:
            try:r['fresh_cleanup']=fresh.close()
            except Exception as e:r['fresh_cleanup_error']=repr(e);r['status']='failed'
        for t,p in targets:
            (p/'target-stop').write_text('stop')
            try:t.wait(timeout=3)
            except subprocess.TimeoutExpired:t.terminate();t.wait();r['status']='failed'
        r['target_exitcodes']=[t.returncode for t,_ in targets]
        for c in connections:
            try:c.close()
            except Exception:pass
        for owner in owners:
            try: owner.close()
            except Exception as e:r['display_close_error']=repr(e);r['status']='failed'
        r['server_exitcodes']=[p.returncode for p in servers]
        if pidfd is not None:os.close(pidfd)
        (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
    return 0 if r['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
