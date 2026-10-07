import subprocess,time,json,os,traceback
from Xlib import display
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
raw={'native_runs':1,'model_calls':0};server=None;backend=None;observer=None
try:
    server=subprocess.Popen(['Xvfb',':264','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for i in range(50):
        if server.poll() is not None:raise RuntimeError('Xvfb exited before connection')
        try:observer=display.Display(':264');break
        except Exception:time.sleep(.02)
    if observer is None:raise RuntimeError('private Xvfb connection unavailable')
    backend=X11Backend(':264',{})
    program=dict(schema='agent-interface/program-v1',program_id='no-ordinary-input-units',source=dict(observation_seq=1,binding_revision=1),authority=dict(lease_id='private-units-fixture',expires_at_ns=time.monotonic_ns()+5_000_000_000),terminal=dict(release_all_required=True),ops=[dict(op='wait_update',timeout_ms=1),dict(op='release_all')])
    raw['program']=program;raw['receipt']=X11RuntimeSession(backend).dispatch(program,current_observation_seq=1,current_binding_revision=1)
    raw['independent_keymap']=list(observer.query_keymap());raw['result']='NATIVE_RETURNED'
except Exception:raw['error']=traceback.format_exc()
finally:
    if backend is not None:backend.close()
    if observer is not None:observer.close()
    if server is not None:
        server.terminate()
        try:raw['xvfb_exit']=server.wait(timeout=2)
        except subprocess.TimeoutExpired:server.kill();raw['xvfb_exit']=server.wait();raw['cleanup_forced']=True
print(json.dumps(raw,indent=2))
raise SystemExit(bool(raw.get('error')) or raw.get('cleanup_forced',False))
