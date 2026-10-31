"""Test-only stale supervisor against a reused private X display."""
import json, os, pathlib, subprocess, sys, time, traceback
from Xlib import X, XK, display
from Xlib.ext import xtest
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner

def main():
    out=pathlib.Path('/out'); mode=os.environ['CONTROL_MODE']
    result={'status':'started','mode':mode,'synthetic_old_b_obligation':True}
    servers=[]; targets=[]; connections=[]; oldowner=None; fresh=None; conn=None; held=False; bcode=None
    def start_server(label):
        owner=PrivateDisplayOwner(out/('display-owner-'+label)); session=owner.start(timeout_s=5); servers.append(owner)
        previous=os.environ.get('XAUTHORITY');os.environ['XAUTHORITY']=str(session.authority)
        try: c=display.Display(session.display)
        finally:
            if previous is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=previous
        connections.append(c);return owner,session,c
    def target(label,session,c):
        p=out/label;p.mkdir(); proc=subprocess.Popen(['python3','-B','/target.py'],env=dict(os.environ,TEST_DISPLAY=session.display,XAUTHORITY=str(session.authority),TARGET_OUT=str(p)),stdout=(p/'stdout').open('wb'),stderr=(p/'stderr').open('wb')); targets.append((proc,p))
        end=time.monotonic()+4
        while not (p/'target-ready.json').exists():
            if proc.poll() is not None or time.monotonic()>end: raise RuntimeError('target unavailable')
            time.sleep(.01)
        win=c.create_resource_object('window',json.loads((p/'target-ready.json').read_text())['xid']);c.set_input_focus(win,X.RevertToParent,X.CurrentTime);c.sync();return win,p
    def down(c,k): return bool(bytes(c.query_keymap())[k//8] & (1 << (k%8)))
    def events(p,condition):
        end=time.monotonic()+2
        while time.monotonic()<end:
            try:
                row=json.loads((p/'target-events.json').read_text())
                if condition(row): return row
            except (FileNotFoundError,json.JSONDecodeError): pass
            time.sleep(.01)
        raise RuntimeError('target event missing')
    try:
        assert mode in ('keep','swap')
        oldserver,olds,oc=start_server('old'); oldwin,oldout=target('old-target',olds,oc)
        os.environ['XAUTHORITY']=str(out/'invalid-parent-auth'); (out/'old-owner').mkdir()
        oldowner=OwnedGuardedSessionOwner({'app':oldwin.id},out/'old-owner',olds.display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,xauthority=str(olds.authority));oldowner.get()
        snap=oldowner.snapshot();result['old_snapshot']=snap
        pid=snap['owner_process_pid'];base=snap['owner_x_client_resource_base']; assert type(pid) is int and type(base) is int
        retirement=oldowner.retire('test old owner retirement');result['owner_retirement']=retirement;assert retirement['retired']
        result['display_retirement']=oldserver.retire(timeout_s=3);assert result['display_retirement']['status']=='retired'
        newserver,news,conn=start_server('new');result['old_display']=olds.display;result['new_display']=news.display;assert olds.display==news.display
        win,p=target('fresh-target',news,conn);bcode=conn.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(conn,X.KeyPress,bcode);conn.sync();held=True
        result['fresh_b_before']=down(conn,bcode);assert result['fresh_b_before']
        events(p,lambda row:any(e['key']=='b' and e['type']=='press' for e in row['events']))
        if mode=='swap': pathlib.Path(olds.authority).write_bytes(pathlib.Path(news.authority).read_bytes())
        request={'operation_id':'synthetic-old-b','session_id':oldowner.session_id,'binding_revision':oldowner.binding_revision,'display_name':olds.display,'owner_process_retired':True,'owner_process_exitcode':retirement['exitcode'],'owner_pid':pid,'x_resource_base':base,'owner_generation':{'session_id':oldowner.session_id,'child_pid':pid,'x_resource_base':base,'binding_revision':oldowner.binding_revision},'keys':{'b':bcode},'buttons':[],'owner_data_directory':str(out/'old-owner')}
        result['supervisor']=oldowner._cleanup_supervisor.run(request,deadline_monotonic_ns=time.monotonic_ns()+3_000_000_000)
        conn.sync(); result['fresh_b_after']=down(conn,bcode)
        if not result['fresh_b_after']:
            result['fresh_target_after_supervisor']=events(p,lambda row:any(e['key']=='b' and e['type']=='release' for e in row['events']));held=False
        if held: xtest.fake_input(conn,X.KeyRelease,bcode);conn.sync();held=False
        assert not down(conn,bcode)
        (out/'fresh-owner').mkdir();fresh=OwnedGuardedSessionOwner({'app':win.id},out/'fresh-owner',news.display,process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True,xauthority=str(news.authority));fresh.get()
        (out/'observe').mkdir();obs=fresh.invoke_guarded('guarded_observe',{},out/'observe');g=obs['source']['pointer_binding']['geometry'];(out/'mint').mkdir();(out/'action').mkdir()
        minted=fresh.invoke_guarded('guarded_mint',{'alias':'field','source_sequence':obs['source']['sequence'],'point':[g[0]+20,g[1]+20],'region_size':[12,12]},out/'mint')
        action=fresh.invoke_guarded('guarded_input',{'alias':'field','offset':minted['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}]},out/'action');result['fresh_action']=action
        result['fresh_target_final']=events(p,lambda row:row['value']=='a' and any(e['key']=='a' and e['type']=='release' for e in row['events']))
        assert minted['status']=='minted' and action['status']=='completed' and action['result']['execution']['releases'][-1]['verified']
        result['status']='completed'
    except BaseException as exc: result.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    finally:
        if held and conn is not None:
            try: xtest.fake_input(conn,X.KeyRelease,bcode);conn.sync();result['fixture_final_release']=True
            except Exception as exc: result['fixture_final_release_error']=repr(exc);result['status']='failed'
        for name,owner in [('old',oldowner),('fresh',fresh)]:
            if owner is not None:
                try: result[name+'_close']=owner.close()
                except Exception as exc:result[name+'_close_error']=repr(exc);result['status']='failed'
        for proc,p in targets:
            (p/'target-stop').write_text('stop')
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.terminate();proc.wait();result['status']='failed'
        result['target_exitcodes']=[proc.returncode for proc,_ in targets]
        for c in connections:
            try:c.close()
            except Exception:pass
        for server in servers:
            try:server.close()
            except Exception as exc:result['display_close_error']=repr(exc);result['status']='failed'
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['status']=='completed' else 1
if __name__=='__main__':sys.exit(main())
