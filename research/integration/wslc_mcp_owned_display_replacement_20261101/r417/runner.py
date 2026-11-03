import asyncio,json,os,select,signal,subprocess,sys,tempfile,time,traceback
from pathlib import Path
from Xlib import X,display
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
OUT=Path('/out')
async def call(s,n,a): return _metadata(await asyncio.wait_for(s.call_tool(n,a),8))
async def ready(path,proc):
    end=time.monotonic()+5
    while time.monotonic()<end:
        if path.exists(): return json.loads(path.read_text())
        if proc.poll() is not None: raise RuntimeError('target exited before ready')
        await asyncio.sleep(.02)
    raise RuntimeError('target startup timeout')
async def main():
    r={'status':'ERROR','cleanup':[]}; owner=server=replacement=None; targets=[]; d=None
    try:
      with tempfile.TemporaryDirectory(prefix='r417-') as tmp:
        owner=PrivateDisplayOwner(Path(tmp)/'display'); sess=owner.start(timeout_s=5)
        os.environ['XAUTHORITY']=str(sess.authority)
        def target(name):
            path=OUT/name; path.mkdir(); env=dict(os.environ,DISPLAY=sess.display,TARGET_OUT=str(path))
            p=subprocess.Popen([sys.executable,'-B','/fixture/target.py'],env=env,stdout=subprocess.DEVNULL,stderr=(OUT/(name+'-stderr.txt')).open('w'))
            targets.append((name,p,os.pidfd_open(p.pid))); return path,p
        oldpath,old=target('old'); info=await ready(oldpath/'target-ready.json',old)
        d=display.Display(sess.display); d.create_resource_object('window',info['xid']).set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); d.close(); d=None
        server=create_server({'app':info['xid']},OUT/'mcp',display_name=sess.display,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,guarded_prestarted_cancel_supervisor=True,_guarded_xauthority=str(sess.authority),_guarded_display_owner=owner)
        r['observe']=await call(server,'interface_guarded_observe',{})
        if r['observe'].get('status')!='observed': raise RuntimeError('old observation failed')
        r['mint']=await call(server,'interface_guarded_mint',{'alias':'field','source_sequence':r['observe']['source']['sequence'],'point':[30,30],'region_size':[12,12]})
        if r['mint'].get('status')!='minted': raise RuntimeError('old alias mint failed')
        r['old_retire']=owner.retire(timeout_s=3)
        if r['old_retire'].get('status')!='retired': raise RuntimeError('old server not retired')
        rd,wr=os.pipe()
        try:
            replacement=subprocess.Popen(['Xvfb',sess.display,'-displayfd',str(wr),'-screen','0','640x480x24','-nolisten','tcp','-auth',str(sess.authority)],pass_fds=(wr,),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            os.close(wr); wr=None
            if not select.select([rd],[],[],5)[0]: raise RuntimeError('replacement timeout')
            number=os.read(rd,32).decode().strip()
        finally:
            os.close(rd)
            if wr is not None: os.close(wr)
        if number!=sess.display[1:] or replacement.poll() is not None: raise RuntimeError('replacement not live')
        newpath,new=target('new'); fresh=await ready(newpath/'target-ready.json',new)
        r['old_xid']=info['xid'];r['new_xid']=fresh['xid'];r['same_xid']=info['xid']==fresh['xid']
        d=display.Display(sess.display); w=d.create_resource_object('window',fresh['xid']); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); r['fresh_focus']=getattr(d.get_input_focus().focus,'id',None)==fresh['xid']; d.close(); d=None
        if not r['same_xid'] or not r['fresh_focus']: r['status']='INCONCLUSIVE'; raise RuntimeError('pre-input target control failed')
        try: r['stale_action']=await call(server,'interface_guarded_input',{'alias':'field','offset':r['mint']['offset'],'interaction':'keyboard','observe_after':False,'tail':[{'op':'key_chord','keys':['a']}],'wait_for_result_ms':5000})
        except BaseException as e: r['stale_error']=type(e).__name__+': '+str(e)
        await asyncio.sleep(2)
        r['fresh_state']=json.loads((newpath/'target-state.json').read_text()); ep=newpath/'target-events.json'; r['fresh_events']=json.loads(ep.read_text()) if ep.exists() else []
        status=r.get('stale_action',{}).get('status'); r['status']='PASS' if status!='completed' and r['fresh_state']=={'count':0} and not any(e.get('key')=='a' for e in r['fresh_events']) else 'FAIL'
    except BaseException as e:
      if r['status']!='INCONCLUSIVE': r['status']='ERROR'
      r['error']=type(e).__name__+': '+str(e); r['traceback']=traceback.format_exc()
    finally:
      if server:
        try:r['close']=await call(server,'interface_close',{})
        except BaseException as e:r['close_error']=type(e).__name__+': '+str(e)
      if d:
        try:d.close()
        except Exception as e:r['cleanup'].append(['display_client_error',repr(e)])
      for name,p,fd in reversed(targets):
        try:
          if p.poll() is None: signal.pidfd_send_signal(fd,signal.SIGKILL)
          p.wait(timeout=3);r['cleanup'].append([name,p.returncode])
        except Exception as e:r['cleanup'].append([name+'_error',repr(e)])
        finally:os.close(fd)
      if replacement:
        try:
          if replacement.poll() is None: replacement.terminate()
          replacement.wait(timeout=3);r['cleanup'].append(['replacement',replacement.returncode])
        except Exception as e:r['cleanup'].append(['replacement_error',repr(e)])
      if owner:
        try:r['cleanup'].append(['old_display',owner.close(timeout_s=3)])
        except Exception as e:r['cleanup'].append(['old_display_error',repr(e)])
      if any('error' in x[0] for x in r['cleanup']):r['status']='ERROR'
      (OUT/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'error':r.get('error')}),flush=True)
    return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
