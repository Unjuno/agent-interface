from __future__ import annotations
import hashlib,json,os,subprocess,tempfile,time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

def free_display(start=90,end=120):
    sock=Path('/tmp/.X11-unix')
    for n in range(start,end):
        if not (sock/f'X{n}').exists(): return n
    raise RuntimeError('no free display')

def launch(cmd,env):
    return subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def stop(p):
    if p and p.poll() is None:
        p.terminate()
        try:p.wait(timeout=3)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)

def run_session(session_id:int):
    n=free_display(); disp=f':{n}'; auth=Path(f'/tmp/ai-multiapp-{session_id}-{n}.Xauthority');auth.write_bytes(b'')
    env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=str(auth)
    os.environ['DISPLAY']=disp; os.environ['XAUTHORITY']=str(auth)
    xv=launch(['Xvfb',disp,'-screen','0','1280x800x24','-ac'],env);time.sleep(.25)
    wm=launch(['openbox'],env);time.sleep(.4)
    d=display.Display(disp);root=d.screen().root
    atom_clients=d.intern_atom('_NET_CLIENT_LIST'); atom_name=d.intern_atom('_NET_WM_NAME'); utf8=d.intern_atom('UTF8_STRING')
    ps=[]; events=[]
    def clients():
        p=root.get_full_property(atom_clients,X.AnyPropertyType);return list(p.value) if p else []
    def title(wid):
        w=d.create_resource_object('window',wid)
        try:
            p=w.get_full_property(atom_name,utf8)
            if p and p.value:return p.value.decode('utf-8','replace') if isinstance(p.value,bytes) else str(p.value)
        except Exception:pass
        try:return w.get_wm_name() or ''
        except Exception:return ''
    def wait_title(substr,timeout=12,exclude=None):
        end=time.time()+timeout
        while time.time()<end:
            for wid in clients():
                if exclude and wid in exclude:continue
                if substr.lower() in title(wid).lower():return wid
            time.sleep(.08)
        raise RuntimeError('window_not_found:'+substr)
    def geom(wid):
        g=d.create_resource_object('window',wid).get_geometry();return [int(g.x),int(g.y),int(g.width),int(g.height)]
    def focus(wid):
        d.create_resource_object('window',wid).set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.12)
    def focus_id():
        f=d.get_input_focus().focus;return int(f.id) if hasattr(f,'id') else int(f)
    def chord(wid,mods,key):
        focus(wid)
        for m in mods:xtest.fake_input(d,X.KeyPress,d.keysym_to_keycode(XK.string_to_keysym(m)))
        kc=d.keysym_to_keycode(XK.string_to_keysym(key));xtest.fake_input(d,X.KeyPress,kc);xtest.fake_input(d,X.KeyRelease,kc)
        for m in reversed(mods):xtest.fake_input(d,X.KeyRelease,d.keysym_to_keycode(XK.string_to_keysym(m)))
        d.sync()
    def framebuffer_hash():
        g=root.get_geometry();im=root.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff);raw=im.data.encode('latin1') if isinstance(im.data,str) else bytes(im.data);return hashlib.sha256(raw).hexdigest()
    def neutral():
        km=d.query_keymap(); q=root.query_pointer(); return (not any(km)) and int(q.mask)==0
    try:
        c1dir=tempfile.mkdtemp(prefix=f'ai-c1-{session_id}-')
        c1=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+c1dir,'--no-first-run','about:blank'],env);ps.append(c1)
        old=wait_title('Chromium',15)
        before=geom(old)
        subprocess.run(['wmctrl','-ir',hex(old),'-b','remove,maximized_vert,maximized_horz'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(['wmctrl','-ir',hex(old),'-e','0,80,60,900,650'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.45);after=geom(old);events.append({'event':'geometry_change','before':before,'after':after,'ok':before!=after})
        xt=launch(['xterm','-T',f'MultiAppPeer-{session_id}'],env);ps.append(xt); peer=wait_title('MultiAppPeer',8)
        focus(old);f0=focus_id();focus(peer);f1=focus_id();events.append({'event':'focus_drift','from':f0,'to':f1,'ok':f0!=f1})
        c2dir=tempfile.mkdtemp(prefix=f'ai-c2-{session_id}-')
        c2=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+c2dir,'--no-first-run','about:blank'],env);ps.append(c2)
        new=wait_title('Chromium',15,exclude={old});focus(new);stop(c1)
        end=time.time()+5
        while old in clients() and time.time()<end:time.sleep(.08)
        events.append({'event':'window_replacement','old':int(old),'new':int(new),'old_gone':old not in clients(),'ok':old!=new and old not in clients()})
        time.sleep(.3);h0=framebuffer_hash();chord(new,['Control_L','Shift_L'],'Delete');time.sleep(1.0);h1=framebuffer_hash()
        events.append({'event':'modal_transition','mechanism':'chromium_clear_browsing_data_dialog','before':h0,'after':h1,'ok':h0!=h1,'title':title(new)})
        chord(new,[],'Escape');time.sleep(.2)
        clean=neutral();events.append({'event':'input_neutral','ok':clean})
        gates={e['event']:bool(e['ok']) for e in events}
        return {'session_id':session_id,'display':disp,'events':events,'gates':gates,'pass':all(gates.values()),'apps':['Chromium','XTerm']}
    finally:
        for p in reversed(ps):stop(p)
        try:d.close()
        except Exception:pass
        stop(wm);stop(xv)
        try:auth.unlink()
        except Exception:pass
