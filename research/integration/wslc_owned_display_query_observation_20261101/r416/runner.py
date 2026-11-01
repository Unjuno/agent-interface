import json, os, select, subprocess, sys, tempfile, threading, traceback
from pathlib import Path
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
from runtime.guarded_x11_v1.owned_xlib_connector import OwnedXlibConnector
from runtime.guarded_x11_v1.target_queries import X11TargetQueries
from runtime.guarded_x11_v1.observation_worker import open_readonly_backend
r={'cases':{},'cleanup':[]}; replacement=None; guard=None
with tempfile.TemporaryDirectory() as td:
    a=PrivateDisplayOwner(Path(td)/'a')
    try:
        s=a.start(timeout_s=5); os.environ['XAUTHORITY']=str(s.authority)
        fd,pid=a.duplicate_server_pidfd(timeout_s=1)
        try: guard=OwnedXlibConnector(fd,pid,disposable=True)
        finally: os.close(fd)
        def worker(label, kind):
            try:
                x=X11TargetQueries(s.display) if kind=='query' else open_readonly_backend(s.display,{})
                x.close(); r['cases'][label]='connected'
            except Exception as e: r['cases'][label]=type(e).__name__+': '+str(e)
        def trial(label,kind):
            t=threading.Thread(target=worker,args=(label,kind)); t.start(); t.join(5)
            if t.is_alive(): raise RuntimeError('thread timed out: '+label)
        trial('query_before','query'); trial('observation_before','observation')
        r['old_retire']=a.retire(timeout_s=3)
        if r['old_retire'].get('status')!='retired': raise RuntimeError('old server not retired')
        read_fd,write_fd=os.pipe()
        try:
            replacement=subprocess.Popen(['Xvfb',s.display,'-displayfd',str(write_fd),'-screen','0','640x480x24','-nolisten','tcp','-auth',str(s.authority)],pass_fds=(write_fd,),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            os.close(write_fd); write_fd=None
            if not select.select([read_fd],[],[],5)[0]: raise RuntimeError('replacement startup timeout')
            r['replacement_number']=os.read(read_fd,32).decode().strip()
        finally:
            os.close(read_fd)
            if write_fd is not None: os.close(write_fd)
        if r['replacement_number'] != s.display[1:] or replacement.poll() is not None: raise RuntimeError('replacement not live at same number')
        env=os.environ.copy(); env['DISPLAY']=s.display
        cp=subprocess.run([sys.executable,'-c','from Xlib import display; d=display.Display(); d.sync(); d.close()'],env=env,capture_output=True,text=True,timeout=5)
        r['control']={'exit':cp.returncode,'stderr':cp.stderr}
        trial('query_after','query'); trial('observation_after','observation')
        c=r['cases']; r['pass']=(cp.returncode==0 and c.get('query_before')==c.get('observation_before')=='connected' and all('owned display unavailable' in c.get(x,'') for x in ('query_after','observation_after')) and replacement.poll() is None)
    except BaseException:
        r['exception']=traceback.format_exc(); r['pass']=False
    finally:
        if guard:
            try: r['cleanup'].append(['guard',guard.close()])
            except Exception as e: r['cleanup'].append(['guard_error',repr(e)])
        if replacement:
            try:
                replacement.terminate(); replacement.wait(timeout=3)
                r['cleanup'].append(['replacement_exit',replacement.returncode])
            except Exception as e:
                r['cleanup'].append(['replacement_error',repr(e)])
                try: replacement.kill(); replacement.wait(timeout=3)
                except Exception as k: r['cleanup'].append(['replacement_kill_error',repr(k)])
        try: r['cleanup'].append(['old',a.retire(timeout_s=3)])
        except Exception as e: r['cleanup'].append(['old_error',repr(e)])
print(json.dumps(r,indent=2),flush=True)
raise SystemExit(0 if r.get('pass') and not any('error' in x[0] for x in r['cleanup']) else 1)
