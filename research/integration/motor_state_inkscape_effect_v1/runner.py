#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, subprocess, tempfile, time, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from Xlib import X, XK, display
from Xlib.ext import xtest

CONDS=['STABLE_NAIVE','DISPLACED_NAIVE','DISPLACED_OBSERVED_GUARD','STABLE_OBSERVED_GUARD','OBSERVER_UNAVAILABLE_NAIVE','OBSERVER_UNAVAILABLE_GUARD']
SCHEMA='agent-interface/motor-state-inkscape-effect-v1'

def key(d,name,down=True):
    kc=d.keysym_to_keycode(XK.string_to_keysym(name)); xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc); d.sync(); time.sleep(.02)
def chord(d,mod,k):
    key(d,mod,True); key(d,k,True); key(d,k,False); key(d,mod,False)
def move(d,x,y): xtest.fake_input(d,X.MotionNotify,x=int(x),y=int(y)); d.sync(); time.sleep(.03)
def button(d,b,down=True): xtest.fake_input(d,X.ButtonPress if down else X.ButtonRelease,b); d.sync(); time.sleep(.03)
def qptr(d):
    q=d.screen().root.query_pointer(); return {'x':int(q.root_x),'y':int(q.root_y),'mask':int(q.mask),'button1':bool(q.mask & X.Button1Mask)}
def sha(b): return hashlib.sha256(b).hexdigest()
def parse_svg_bytes(raw):
    r=ET.fromstring(raw).find('{http://www.w3.org/2000/svg}rect')
    if r is None: raise ValueError('RECT_MISSING')
    return {k:r.attrib.get(k) for k in ('x','y','width','height','transform')}
def red_bbox(disp):
    im=ImageGrab.grab(xdisplay=disp).convert('RGB'); arr=np.asarray(im); mask=(arr[:,:,0]>180)&(arr[:,:,1]<100)&(arr[:,:,2]<100)
    h,w=mask.shape; seen=np.zeros_like(mask,bool); comps=[]; ys,xs=np.where(mask)
    for sy,sx in zip(ys,xs):
        if seen[sy,sx]: continue
        q=[(int(sy),int(sx))]; seen[sy,sx]=1; minx=maxx=int(sx); miny=maxy=int(sy); n=0
        for y,x in q:
            n+=1; minx=min(minx,x);maxx=max(maxx,x);miny=min(miny,y);maxy=max(maxy,y)
            for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=yy<h and 0<=xx<w and mask[yy,xx] and not seen[yy,xx]: seen[yy,xx]=1;q.append((yy,xx))
        if n>=300: comps.append((n,(minx,miny,maxx+1,maxy+1)))
    return max(comps,default=(0,None))[1]
def active_window(env):
    s=subprocess.run(['wmctrl','-l'],env=env,capture_output=True,text=True,timeout=2).stdout
    for line in s.splitlines():
        if 'shape.svg' in line: return line.split()[0]
    return None

def stop_proc(p, sigterm_expected=False):
    if p is None: return None
    if p.poll() is None:
        p.terminate()
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            p.kill();p.wait(timeout=1)
    return p.returncode

def run_case(cond, rep, idx):
    root=Path(tempfile.mkdtemp(prefix=f'ms-ink-r{rep}-{idx}-')); disp=f':{160+rep*10+idx}'; auth=root/'.Xauthority';auth.touch();auth.chmod(0o600)
    env=os.environ.copy(); env.update(DISPLAY=disp,XAUTHORITY=str(auth),HOME=str(root/'home'),XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'),XDG_DATA_HOME=str(root/'data'),XDG_RUNTIME_DIR=str(root/'run'),GDK_BACKEND='x11',QT_QPA_PLATFORM='xcb',LANG='C.UTF-8',LC_ALL='C.UTF-8')
    for k in ('HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR'): Path(env[k]).mkdir(parents=True,exist_ok=True)
    os.environ.update({k:env[k] for k in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR','GDK_BACKEND','QT_QPA_PLATFORM','LANG','LC_ALL')})
    xv=subprocess.Popen(['Xvfb',disp,'-screen','0','1280x800x24','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ob=app=None; d=None; svg=root/'shape.svg'
    rec={'schema':SCHEMA,'condition':cond,'rep':rep,'case_index':idx,'display':disp,'authority':'none','input_dispatched':False,
         'commands':{'xvfb':['Xvfb',disp,'-screen','0','1280x800x24','-ac'],'openbox':['openbox'],'app':['inkscape',str(svg)]}}
    try:
        time.sleep(.25); ob=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.15)
        before=b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="r" x="50" y="50" width="40" height="30" fill="red"/></svg>'
        svg.write_bytes(before); rec['before_svg_utf8']=before.decode(); rec['before_svg_sha256']=sha(before); rec['before_svg']=parse_svg_bytes(before)
        app=subprocess.Popen(['inkscape',str(svg)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); rec['pids']={'xvfb':xv.pid,'openbox':ob.pid,'inkscape':app.pid}
        for _ in range(100):
            if active_window(env): break
            time.sleep(.1)
        else: raise RuntimeError('INKSCAPE_WINDOW_TIMEOUT')
        subprocess.run(['wmctrl','-a','shape.svg'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2);time.sleep(.35)
        d=display.Display(disp); chord(d,'Control_L','a');time.sleep(.3)
        bbox=red_bbox(disp); rec['bbox']=bbox
        if not bbox: raise RuntimeError('RED_BBOX_MISSING')
        x=(bbox[0]+bbox[2])//2;y=(bbox[1]+bbox[3])//2; rec['commanded']={'x':x,'y':y}; move(d,x,y); rec['after_command']=qptr(d)
        displaced='DISPLACED' in cond; unavailable='OBSERVER_UNAVAILABLE' in cond; guard=('OBSERVED_GUARD' in cond or cond=='OBSERVER_UNAVAILABLE_GUARD')
        if displaced: move(d,min(820,x+260),min(620,y+180)); rec['after_external_displacement']=qptr(d)
        if unavailable: observed=None; disposition='UNKNOWN'
        else:
            observed=qptr(d); disposition='MATCH' if observed['x']==x and observed['y']==y else 'MISMATCH'
        rec['observed']=observed; rec['motor_disposition']=disposition; rec['guard_policy']='OBSERVED_GUARD' if guard else 'NAIVE_COMMAND_ONLY'
        should_dispatch=(not guard) or disposition=='MATCH'; rec['should_dispatch']=should_dispatch
        if should_dispatch:
            rec['input_dispatched']=True; start=qptr(d); rec['dispatch_start']=start; button(d,1,True); rec['held_observed']=qptr(d)
            sx,sy=start['x'],start['y']
            for j in range(1,11): move(d,sx+4*j,sy)
            button(d,1,False); rec['after_release']=qptr(d);time.sleep(.25)
        else: rec['held_observed']=None;rec['after_release']=qptr(d)
        chord(d,'Control_L','s');time.sleep(.45)
        after=svg.read_bytes(); rec['after_svg_utf8']=after.decode();rec['after_svg_sha256']=sha(after);rec['after_svg']=parse_svg_bytes(after)
        xval=float(rec['after_svg']['x']); rec['moved_x']=xval; rec['intended_effect']=xval>50.5 and abs(float(rec['after_svg']['y'])-50)<.1 and abs(float(rec['after_svg']['width'])-40)<.1 and abs(float(rec['after_svg']['height'])-30)<.1
        rec['neutral']=not qptr(d)['button1']; rec['app_window']=active_window(env); rec['status']='complete'
    except Exception as e: rec['status']='error';rec['error']=repr(e)
    finally:
        if d:
            try:d.close()
            except:pass
        rec['process_exits']={'inkscape':stop_proc(app),'openbox':stop_proc(ob),'xvfb':stop_proc(xv)}
        shutil.rmtree(root,ignore_errors=True)
    return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('rep',type=int); ap.add_argument('out',type=Path); args=ap.parse_args()
    if args.out.exists(): raise SystemExit('OUTPUT_EXISTS')
    if args.mode=='formal' and args.rep not in (0,1,2): raise SystemExit('INVALID_FORMAL_REP')
    args.out.mkdir(parents=True)
    rows=[]
    for i,c in enumerate(CONDS):
        r=run_case(c,args.rep,i); rows.append(r); print(json.dumps({k:r.get(k) for k in ('condition','status','motor_disposition','input_dispatched','intended_effect','neutral')},sort_keys=True),flush=True)
        with (args.out/'RAW.jsonl').open('a') as f:f.write(json.dumps(r,sort_keys=True)+'\n')
        if r.get('status')!='complete':
            (args.out/'STOP.json').write_text(json.dumps({'reason':'CASE_INCOMPLETE','condition':c},sort_keys=True)+'\n'); return 2
    (args.out/'END.json').write_text(json.dumps({'mode':args.mode,'rep':args.rep,'cases':len(rows),'exit':0},sort_keys=True)+'\n'); return 0
if __name__=='__main__': raise SystemExit(main())
