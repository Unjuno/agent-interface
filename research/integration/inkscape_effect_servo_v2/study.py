from __future__ import annotations
import argparse, hashlib, json, os, secrets, signal, subprocess, time, traceback
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import ImageGrab
from Xlib import X, XK, display
from Xlib.ext import xtest

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="r" x="50" y="50" width="40" height="30" fill="red"/></svg>\n'
POLICIES=('OPEN_LOOP','MID_EFFECT_SERVO','SERVO_OBSERVER_UNAVAILABLE')

def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def parse_svg(raw):
    root=ET.fromstring(raw); r=root.find('{http://www.w3.org/2000/svg}rect')
    if r is None: raise RuntimeError('RECT_MISSING')
    return {k:r.attrib.get(k) for k in ('id','x','y','width','height','transform')}

def red_components(im):
    arr=np.asarray(im.convert('RGB')); m=(arr[:,:,0]>200)&(arr[:,:,1]<70)&(arr[:,:,2]<70)
    m[:150,:]=False; m[680:,:]=False; m[:,:100]=False; m[:,1100:]=False
    seen=np.zeros(m.shape,dtype=bool); out=[]
    for sy,sx in zip(*np.where(m)):
        if seen[sy,sx]: continue
        q=[(int(sy),int(sx))]; seen[sy,sx]=True; xs=[]; ys=[]
        for yy,xx in q:
            xs.append(xx); ys.append(yy)
            for yn,xn in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                if 0<=yn<m.shape[0] and 0<=xn<m.shape[1] and m[yn,xn] and not seen[yn,xn]:
                    seen[yn,xn]=True; q.append((yn,xn))
        bb=[min(xs),min(ys),max(xs)+1,max(ys)+1]
        if 36<=bb[2]-bb[0]<=44 and 26<=bb[3]-bb[1]<=34 and len(xs)>850: out.append(bb)
    return out

def run_case(root:Path, policy:str, first_dx:int, first_dy:int, rep:int, phase:str)->int:
    root.mkdir(parents=True,exist_ok=False)
    events=[]; processes=[]; d=None; exit_code=2
    env=os.environ.copy()
    for k in ('DBUS_SESSION_BUS_ADDRESS','SESSION_MANAGER','WAYLAND_DISPLAY'): env.pop(k,None)
    sandbox=root/'session'; sandbox.mkdir(mode=0o700)
    for key,sub in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_RUNTIME_DIR','run')]:
        p=sandbox/sub; p.mkdir(mode=0o700); env[key]=str(p)
    display_num=next(n for n in range(24000,25000) if not Path(f'/tmp/.X{n}-lock').exists() and not Path(f'/tmp/.X11-unix/X{n}').exists())
    disp=f':{display_num}'; auth=sandbox/'Xauthority'; auth.touch(mode=0o600)
    cookie=secrets.token_hex(16)
    a=subprocess.run(['xauth','-f',str(auth),'add',disp,'MIT-MAGIC-COOKIE-1',cookie],capture_output=True,timeout=3)
    if a.returncode: raise RuntimeError('XAUTH_SETUP_FAILED')
    env.update(DISPLAY=disp,XAUTHORITY=str(auth),GDK_BACKEND='x11',QT_QPA_PLATFORM='xcb',LANG='C.UTF-8',LC_ALL='C.UTF-8',NO_AT_BRIDGE='1')
    os.environ.update({k:env[k] for k in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR','GDK_BACKEND','QT_QPA_PLATFORM','LANG','LC_ALL')})
    rec={'schema':'inkscape-effect-servo-v1','policy':policy,'first_step':[first_dx,first_dy],'rep':rep,'phase':phase,'display':disp,
         'authority':'none','public_runtime_exercised':False,'model_calls':0,'status':'started','events':events,'correction_count':0}
    def event(kind,**kw):
        x={'index':len(events),'ns':time.monotonic_ns(),'kind':kind,**kw}; events.append(x)
        with (root/'EVENTS.jsonl').open('a') as f: f.write(json.dumps(x,sort_keys=True)+'\n')
        return x
    def launch(name,args):
        out=(root/f'{name}.stdout').open('wb'); err=(root/f'{name}.stderr').open('wb')
        p=subprocess.Popen(args,env=env,stdout=out,stderr=err,start_new_session=True);processes.append((name,p,out,err));event('process_start',name=name,pid=p.pid,argv=args);return p
    def key(name,down,role):
        kc=d.keysym_to_keycode(XK.string_to_keysym(name));
        if not kc: raise RuntimeError('UNMAPPED_KEY_'+name)
        xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc);d.sync();event('key',name=name,down=down,role=role);time.sleep(.02)
    def tap(name,role): key(name,True,role);key(name,False,role)
    def chord(name,role): key('Control_L',True,role);tap(name,role);key('Control_L',False,role)
    def move(x,y,role): xtest.fake_input(d,X.MotionNotify,x=int(x),y=int(y));d.sync();event('motion',x=int(x),y=int(y),role=role);time.sleep(.05)
    def button(down,role): xtest.fake_input(d,X.ButtonPress if down else X.ButtonRelease,1);d.sync();event('button',down=down,role=role);time.sleep(.05)
    def state(label):
        q=d.screen().root.query_pointer(); f=d.get_input_focus().focus; keys=bytes(d.query_keymap())
        s={'x':int(q.root_x),'y':int(q.root_y),'mask':int(q.mask),'button1':bool(q.mask&X.Button1Mask),'focus':int(f.id if hasattr(f,'id') else f),'keymap_hex':keys.hex()}
        event('state',label=label,observed=s); return s
    def capture(name):
        im=ImageGrab.grab(xdisplay=disp).convert('RGB'); p=root/f'{name}.png';im.save(p)
        comps=red_components(im); event('image',name=p.name,sha256=sha(p.read_bytes()),pixel_sha256=sha(im.tobytes()),components=comps); return im,comps
    def stop_proc(p):
        if p is None:return None
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); p.wait(timeout=1)
        return p.returncode
    try:
        xv=launch('xvfb',['Xvfb',disp,'-screen','0','1280x800x24','-nolisten','tcp','-auth',str(auth),'-noreset'])
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            if xv.poll() is not None: raise RuntimeError('XVFB_EXIT')
            try:d=display.Display(disp);break
            except Exception:time.sleep(.05)
        if d is None: raise RuntimeError('XVFB_NOT_READY')
        ob=launch('openbox',['openbox']);time.sleep(.2)
        svg=sandbox/'servo.svg';svg.write_bytes(SVG);(root/'before.svg').write_bytes(SVG);rec['before_svg']=parse_svg(SVG)
        app=launch('inkscape',['inkscape','--app-id-tag=servop'+str(os.getpid()),str(svg)])
        win=None;deadline=time.monotonic()+7
        while time.monotonic()<deadline:
            if app.poll() is not None: raise RuntimeError('INKSCAPE_EXIT')
            prop=d.screen().root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'),X.AnyPropertyType)
            for wid in ([] if prop is None else prop.value):
                w=d.create_resource_object('window',int(wid))
                if 'Inkscape' in str(w.get_wm_class()) and w.get_attributes().map_state==X.IsViewable: win=w;break
            if win is not None:break
            time.sleep(.05)
        if win is None: raise RuntimeError('WINDOW_NOT_READY')
        subprocess.run(['wmctrl','-ia',hex(win.id)],env=env,capture_output=True,timeout=3);time.sleep(1.25)
        tap('F1','setup');time.sleep(.2);tap('1','setup');time.sleep(.3);chord('a','setup');time.sleep(.3)
        _,source_comps=capture('source')
        if len(source_comps)!=1: raise RuntimeError('SOURCE_TARGET_AMBIGUOUS_'+repr(source_comps))
        source_bb=source_comps[0]; source_center=[(source_bb[0]+source_bb[2])//2,(source_bb[1]+source_bb[3])//2];rec['source_bbox']=source_bb;rec['source_center']=source_center
        x,y=source_center;move(x,y,'setup');initial=state('initial')
        if initial['button1'] or any(bytes.fromhex(initial['keymap_hex'])):raise RuntimeError('INITIAL_NOT_NEUTRAL')
        rec['desired_effect_delta']=[50,30]; rec['authored_pointer_endpoint']=[x+50,y+30]; rec['observation_pointer_delta']=[30,18]
        # same hold prefix for all arms
        prefix=[[first_dx,first_dy],[15,9],[20,12],[25,15],[30,18]]
        button(True,'task'); held=state('held');
        if not held['button1']: raise RuntimeError('HOLD_NOT_OBSERVED')
        for dx,dy in prefix: move(x+dx,y+dy,'task_prefix')
        mid_state=state('mid_hold'); rec['mid_pointer_delta']=[mid_state['x']-x,mid_state['y']-y]
        if policy=='SERVO_OBSERVER_UNAVAILABLE':
            rec['mid_observation']='UNAVAILABLE'; rec['decision']='YIELD_OBSERVER_UNAVAILABLE'; rec['corrected_endpoint']=None
        else:
            _,mid_comps=capture('mid_hold')
            if len(mid_comps)!=1: raise RuntimeError('MID_TARGET_AMBIGUOUS_'+repr(mid_comps))
            mid_bb=mid_comps[0]; mid_center=[(mid_bb[0]+mid_bb[2])//2,(mid_bb[1]+mid_bb[3])//2]
            observed=[mid_center[0]-source_center[0],mid_center[1]-source_center[1]]; rec['mid_bbox']=mid_bb;rec['observed_effect_delta']=observed
            residual=[50-observed[0],30-observed[1]];rec['observed_residual']=residual
            if policy=='MID_EFFECT_SERVO':
                endpoint=[mid_state['x']+residual[0],mid_state['y']+residual[1]];rec['corrected_endpoint']=endpoint;rec['correction_count']=1;rec['decision']='CORRECT_ONCE';move(endpoint[0],endpoint[1],'task_correction')
            elif policy=='OPEN_LOOP':
                rec['corrected_endpoint']=[x+50,y+30];rec['decision']='OPEN_LOOP';move(x+50,y+30,'task_open_loop')
            else: raise RuntimeError('UNKNOWN_POLICY')
        button(False,'task_release');time.sleep(.25);rec['posttask']=state('posttask');capture('after_task')
        chord('s','scorer_save');time.sleep(.45);after=svg.read_bytes();(root/'after.svg').write_bytes(after);rec['after_svg']=parse_svg(after)
        rec['saved_effect_delta']=[float(rec['after_svg']['x'])-50.0,float(rec['after_svg']['y'])-50.0]
        rec['saved_effect_error']=[50.0-rec['saved_effect_delta'][0],30.0-rec['saved_effect_delta'][1]]
        rec['pointer_delta_final']=[rec['posttask']['x']-x,rec['posttask']['y']-y]
        rec['final']=state('final')
        rec['neutral']=not rec['final']['button1'] and not any(bytes.fromhex(rec['final']['keymap_hex']))
        rec['status']='complete';exit_code=0
    except Exception as e:
        rec['status']='STOP';rec['error']=repr(e);rec['traceback']=traceback.format_exc();event('failure',error=repr(e))
    finally:
        if d:
            try:
                for b in (1,2,3): xtest.fake_input(d,X.ButtonRelease,b)
                for i,byt in enumerate(bytes(d.query_keymap())):
                    for bit in range(8):
                        if byt&(1<<bit):xtest.fake_input(d,X.KeyRelease,i*8+bit)
                d.sync();rec['cleanup']=state('cleanup');d.close()
            except Exception as e:rec['cleanup_error']=repr(e);exit_code=2
        rec['process_exits']={}
        for name,p,out,err in reversed(processes):
            rc=stop_proc(p);rec['process_exits'][name]=rc;event('process_exit',name=name,returncode=rc);out.close();err.close()
        if auth.exists():auth.unlink()
        import shutil; shutil.rmtree(sandbox,ignore_errors=True)
        rec['worker_returncode']=exit_code;dump(root/'CASE.json',rec)
    print(json.dumps({k:rec.get(k) for k in ('policy','status','observed_effect_delta','observed_residual','pointer_delta_final','saved_effect_delta','saved_effect_error','decision')},sort_keys=True),flush=True)
    return exit_code

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('policy',choices=POLICIES);ap.add_argument('first_dx',type=int);ap.add_argument('first_dy',type=int);ap.add_argument('rep',type=int);ap.add_argument('--phase',default='construction')
    a=ap.parse_args();raise SystemExit(run_case(a.out.resolve(),a.policy,a.first_dx,a.first_dy,a.rep,a.phase))
