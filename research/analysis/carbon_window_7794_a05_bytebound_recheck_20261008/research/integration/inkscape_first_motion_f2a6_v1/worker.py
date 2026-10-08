"""Owned private-X11 Inkscape first-motion comparison; never uses the user's display."""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, signal, struct, subprocess, sys, time, traceback
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from Xlib import X, XK, display
from Xlib.ext import xtest

HERE = Path(__file__).resolve().parent
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="r" x="50" y="50" width="40" height="30" fill="red"/></svg>\n'


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def dump(p: Path, value) -> None:
    p.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')

def run_case(root: Path, spec: dict) -> int:
    root.mkdir(parents=True, exist_ok=False)
    events = []
    processes = []
    d = None
    env = os.environ.copy()
    for k in ('DBUS_SESSION_BUS_ADDRESS','SESSION_MANAGER','WAYLAND_DISPLAY'):
        env.pop(k, None)
    sandbox = root/'session'
    sandbox.mkdir(mode=0o700)
    for key, sub in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_RUNTIME_DIR','run')]:
        p = sandbox/sub; p.mkdir(mode=0o700)
        env[key] = str(p)
    # No shared-display fallback. Refuse occupied names; no stale-lock deletion.
    display_num = next(n for n in range(21000,22000) if not Path(f'/tmp/.X{n}-lock').exists() and not Path(f'/tmp/.X11-unix/X{n}').exists())
    disp = f':{display_num}'
    auth = sandbox/'Xauthority'; auth.touch(mode=0o600)
    cookie = secrets.token_hex(16)
    auth_result = subprocess.run(['xauth','-f',str(auth),'add',disp,'MIT-MAGIC-COOKIE-1',cookie], capture_output=True, timeout=3)
    if auth_result.returncode:
        raise RuntimeError('XAUTH_SETUP_FAILED')
    # The ephemeral cookie is neither journaled nor published.
    env.update(DISPLAY=disp, XAUTHORITY=str(auth), GDK_BACKEND='x11', QT_QPA_PLATFORM='xcb', LANG='C.UTF-8', LC_ALL='C.UTF-8', NO_AT_BRIDGE='1')
    os.environ.update(env)
    rec = {'schema':'first-motion-case-v1', 'spec':spec, 'pid':os.getpid(), 'display':disp,
           'authority':'none', 'public_runtime_exercised':False, 'status':'started', 'events':events,
           'input_roles':'fixture setup; task drag; scorer Save; safety cleanup are distinct'}
    def event(kind, **kw):
        item={'index':len(events), 'ns':time.monotonic_ns(), 'kind':kind, **kw}; events.append(item)
        with (root/'EVENTS.jsonl').open('a') as f: f.write(json.dumps(item, sort_keys=True)+'\n')
        return item
    def launch(name, args):
        out=(root/f'{name}.stdout').open('wb'); err=(root/f'{name}.stderr').open('wb')
        p=subprocess.Popen(args,env=env,stdout=out,stderr=err,start_new_session=True)
        processes.append((name,p,out,err)); event('process_start',name=name,pid=p.pid,argv=args)
        return p
    def key(name, down, role):
        kc=d.keysym_to_keycode(XK.string_to_keysym(name))
        if not kc: raise RuntimeError('UNMAPPED_KEY_'+name)
        t0=time.monotonic_ns(); xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc);d.sync()
        event('key',name=name,keycode=kc,down=down,role=role,start_ns=t0);time.sleep(.025)
    def tap(name, role): key(name,True,role);key(name,False,role)
    def chord(name,role):
        key('Control_L',True,role);tap(name,role);key('Control_L',False,role)
    def move(x,y,role):
        t0=time.monotonic_ns();xtest.fake_input(d,X.MotionNotify,x=int(x),y=int(y));d.sync()
        event('motion',x=int(x),y=int(y),role=role,start_ns=t0);time.sleep(.035)
    def button(down,role):
        t0=time.monotonic_ns();xtest.fake_input(d,X.ButtonPress if down else X.ButtonRelease,1);d.sync()
        event('button',button=1,down=down,role=role,start_ns=t0);time.sleep(.045)
    def state(label):
        t0=time.monotonic_ns();q=d.screen().root.query_pointer();f=d.get_input_focus().focus
        keys=bytes(d.query_keymap())
        s={'x':int(q.root_x),'y':int(q.root_y),'mask':int(q.mask),'button1':bool(q.mask&X.Button1Mask),
           'focus':int(f.id if hasattr(f,'id') else f),'keymap_hex':keys.hex(),'start_ns':t0,'end_ns':time.monotonic_ns()}
        event('state',label=label,observed=s);return s
    def capture(name, box=None):
        im=ImageGrab.grab(xdisplay=disp).convert('RGB')
        if box is not None: im=im.crop(box)
        p=root/(name+'.png');im.save(p)
        event('image',name=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes()),pixel_sha256=sha(im.tobytes()),width=im.width,height=im.height)
        return im
    def comparable(s):return {k:s[k] for k in ('x','y','mask','focus','keymap_hex')}
    exit_code=2
    def interrupted(signum, frame):
        raise RuntimeError('SUPERVISOR_TERMINATED')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        xv=launch('xvfb',['Xvfb',disp,'-screen','0','1280x800x24','-nolisten','tcp','-auth',str(auth),'-noreset'])
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            if xv.poll() is not None:raise RuntimeError('XVFB_EXIT')
            try:d=display.Display(disp);break
            except Exception:time.sleep(.05)
        if d is None:raise RuntimeError('XVFB_NOT_READY')
        launch('openbox',['openbox']);time.sleep(.2)
        svg=sandbox/'f2a6-shape.svg';svg.write_bytes(SVG);(root/'before.svg').write_bytes(SVG)
        app=launch('inkscape',['inkscape','--app-id-tag=f2a6p'+str(os.getpid()),str(svg)])
        win=None;deadline=time.monotonic()+7
        while time.monotonic()<deadline:
            if app.poll() is not None:raise RuntimeError('INKSCAPE_EXIT')
            prop=d.screen().root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'),X.AnyPropertyType)
            for wid in ([] if prop is None else prop.value):
                w=d.create_resource_object('window',int(wid))
                if 'Inkscape' in str(w.get_wm_class()) and w.get_attributes().map_state==X.IsViewable:
                    win=w;break
            if win is not None:break
            time.sleep(.05)
        if win is None:raise RuntimeError('WINDOW_NOT_READY')
        r=subprocess.run(['wmctrl','-ia',hex(win.id)],env=env,capture_output=True,timeout=3)
        event('activate',window=win.id,exit=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'))
        time.sleep(.9)
        tap('F1','setup');tap('1','setup');chord('a','setup');time.sleep(.5)
        im=capture('source_selector');arr=np.asarray(im);m=(arr[:,:,0]>200)&(arr[:,:,1]<70)&(arr[:,:,2]<70)
        m[:150,:]=False;m[680:,:]=False;m[:,:100]=False;m[:,1100:]=False
        seen=np.zeros(m.shape,dtype=bool);candidates=[]
        for sy,sx in zip(*np.where(m)):
            if seen[sy,sx]:continue
            q=[(int(sy),int(sx))];seen[sy,sx]=True;xs=[];ys=[]
            for yy,xx in q:
                xs.append(xx);ys.append(yy)
                for yn,xn in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                    if 0<=yn<m.shape[0] and 0<=xn<m.shape[1] and m[yn,xn] and not seen[yn,xn]:
                        seen[yn,xn]=True;q.append((yn,xn))
            bb=[min(xs),min(ys),max(xs)+1,max(ys)+1]
            if 38<=bb[2]-bb[0]<=42 and 28<=bb[3]-bb[1]<=32 and len(xs)>900:candidates.append(bb)
        if len(candidates)!=1:raise RuntimeError('TARGET_COMPONENT_AMBIGUOUS_'+str(candidates))
        bbox=candidates[0]
        rec['bbox']=bbox;rec['target_center']=[(bbox[0]+bbox[2])//2,(bbox[1]+bbox[3])//2]
        x,y=rec['target_center'];move(x,y,'setup')
        rec['expected_motor']=state('expected_motor')
        if rec['expected_motor']['button1'] or any(bytes.fromhex(rec['expected_motor']['keymap_hex'])):raise RuntimeError('INITIAL_INPUT_NOT_NEUTRAL')
        # No app-mode or repair branch: only the first task motion changes.
        rec['observed_motor']=state('observed_motor')
        if comparable(rec['observed_motor'])!=comparable(rec['expected_motor']):
            raise RuntimeError('INITIAL_MOTOR_CHANGED')
        box=[bbox[0]-35,bbox[1]-35,bbox[2]+85,bbox[3]+65]
        rec['image_box']=box
        capture('pre_task',box)
        rec['decision']='DRAG'
        button(True,'task');rec['held_motor']=state('held_motor')
        if not rec['held_motor']['button1']:raise RuntimeError('BUTTON_DOWN_NOT_OBSERVED')
        offsets=[spec['first']]+[[5*i,3*i] for i in range(3,11)]
        rec['path_offsets']=offsets;rec['steps']=[]
        for j,(dx,dy) in enumerate(offsets):
            move(x+dx,y+dy,'task')
            obs=state('step'+str(j));capture('step'+str(j),box)
            rec['steps'].append(obs)
        button(False,'task');time.sleep(.2)
        rec['posttask_motor']=state('posttask_motor');capture('after_task',box)
        rec['save_pre_mtime_ns']=svg.stat().st_mtime_ns
        chord('s','scorer_save');time.sleep(.4)
        rec['save_post_mtime_ns']=svg.stat().st_mtime_ns
        after=svg.read_bytes();(root/'after.svg').write_bytes(after)
        rec['before_sha256']=sha(SVG);rec['after_sha256']=sha(after)
        rec['final_motor']=state('final_motor');capture('final',box)
        if rec['final_motor']['mask'] & (X.Button1Mask|X.Button2Mask|X.Button3Mask|X.Button4Mask|X.Button5Mask) or any(bytes.fromhex(rec['final_motor']['keymap_hex'])):raise RuntimeError('FINAL_NOT_NEUTRAL')
        rec['status']='complete';exit_code=0
    except Exception as e:
        rec['status']='STOP';rec['error']=repr(e);rec['traceback']=traceback.format_exc()
        event('failure',error=repr(e))
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if d:
            try:
                # Independent mandatory cleanup is not part of task success.
                for b in (1,2,3):xtest.fake_input(d,X.ButtonRelease,b)
                for i,byt in enumerate(bytes(d.query_keymap())):
                    for bit in range(8):
                        if byt&(1<<bit):xtest.fake_input(d,X.KeyRelease,i*8+bit)
                d.sync();rec['cleanup_motor']=state('cleanup_motor');d.close()
            except Exception as e:rec['cleanup_error']=repr(e);exit_code=2
        rec['process_exits']={}
        for name,p,out,err in reversed(processes):
            how='already_exited'
            if p.poll() is None:
                how='SIGTERM_owned_group';os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    how='SIGKILL_owned_group';os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=1)
            rec['process_exits'][name]={'pid':p.pid,'returncode':p.returncode,'termination':how}
            event('process_exit',name=name,pid=p.pid,returncode=p.returncode,termination=how)
            out.close();err.close()
        if auth.exists():auth.unlink()
        # Private generated app settings aren't evidence and may contain nondeterministic caches.
        import shutil
        shutil.rmtree(sandbox)
        rec['display_socket_absent']=not Path(f'/tmp/.X11-unix/X{display_num}').exists()
        rec['auth_removed']=not auth.exists();rec['worker_returncode']=exit_code
        dump(root/'CASE.json',rec)
    print(json.dumps({'case':spec,'status':rec['status'],'error':rec.get('error'),'returncode':exit_code},sort_keys=True),flush=True)
    return exit_code

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('spec')
    a=ap.parse_args();raise SystemExit(run_case(a.out.resolve(),json.loads(a.spec)))
