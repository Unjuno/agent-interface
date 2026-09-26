import argparse, json, os, subprocess, time, signal
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

SCHEMA='agent-interface/motor-state-x11-first-rung-v2'
CASES=[('inkscape','stable'),('inkscape','pointer_displaced'),('inkscape','observer_unavailable'),('calc','stable'),('calc','focus_transferred'),('calc','observer_unavailable')]

def win_name(w):
    try: return str(w.get_wm_name() or '')
    except Exception: return ''
def descendants(root):
    out=[]; stack=[root]
    while stack:
        w=stack.pop()
        try: cs=w.query_tree().children
        except Exception: cs=[]
        out.extend(cs); stack.extend(cs)
    return out
def find_window(d, needles, timeout=8):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        for w in descendants(d.screen().root):
            n=win_name(w).lower()
            try: c=' '.join(w.get_wm_class() or ()).lower()
            except Exception: c=''
            if any(s in n or s in c for s in needles):
                try:
                    if w.get_attributes().map_state == X.IsViewable: return w
                except Exception: pass
        time.sleep(.05)
    raise RuntimeError('TARGET_WINDOW_NOT_FOUND')
def keycode(d,name):
    kc=d.keysym_to_keycode(XK.string_to_keysym(name))
    if not kc: raise RuntimeError('KEYCODE_NOT_FOUND:'+name)
    return kc
def key_down_in_map(d,kc):
    raw=d.query_keymap(); return bool(raw[kc//8] & (1 << (kc%8)))
def button1_down(d): return bool(d.screen().root.query_pointer().mask & X.Button1Mask)
def pointer_xy(d):
    q=d.screen().root.query_pointer(); return [int(q.root_x),int(q.root_y)]
def focus_id(d):
    f=d.get_input_focus().focus; return int(getattr(f,'id',0) or 0)
def fake_motion(d,x,y): xtest.fake_input(d,X.MotionNotify,x=x,y=y); d.sync()
def fake_button(d,down): xtest.fake_input(d,X.ButtonPress if down else X.ButtonRelease,1); d.sync()
def fake_key(d,kc,down): xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc); d.sync()

def window_center(w):
    g=w.get_geometry(); t=w.translate_coords(w.query_tree().root,0,0)
    return [int(t.x + max(20,g.width//2)), int(t.y + max(20,g.height//2))]

def normal_click(d,w):
    x,y=window_center(w); fake_motion(d,x,y); fake_button(d,True); fake_button(d,False); time.sleep(.08)

def start_xvfb(display_num, root):
    xa=root/'empty.Xauthority'; xa.write_bytes(b'')
    env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(xa); os.environ['XAUTHORITY']=str(xa)
    p=subprocess.Popen(['Xvfb',f':{display_num}','-ac','-screen','0','1280x800x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env,start_new_session=True)
    last_error=None
    for _ in range(120):
        if p.poll() is not None:
            err=(p.stderr.read() or b'').decode('utf-8','replace')[-1000:]
            raise RuntimeError('XVFB_EXITED:'+err)
        try:
            d=display.Display(env['DISPLAY']); d.close(); return p,env
        except Exception as e:
            last_error=repr(e); time.sleep(.025)
    try:
        os.killpg(p.pid, signal.SIGKILL); p.wait(timeout=1)
    except Exception: pass
    err=''
    try: err=(p.stderr.read() or b'').decode('utf-8','replace')[-1000:]
    except Exception: pass
    raise RuntimeError('XVFB_NOT_READY:'+str(last_error)+':'+err)

def launch_app(app, env, root, case_id):
    if app=='inkscape':
        svg=root/f'{case_id}.svg'; svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500"><rect x="100" y="100" width="120" height="80" fill="#ff0000"/></svg>')
        cmd=['inkscape',str(svg)]; needles=[case_id.lower(),'.svg - inkscape']
    else:
        profile=(root/'lo-profile').resolve(); profile.mkdir()
        cmd=['libreoffice',f'-env:UserInstallation=file://{profile}','--calc','--norestore','--nolockcheck','--nofirststartwizard']
        needles=['libreoffice calc','calc']
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env,start_new_session=True)
    d=display.Display(env['DISPLAY']); w=find_window(d,needles)
    normal_click(d,w)
    return p,d,w

def stop_proc(p, timeout=2):
    if not p: return None
    try:
        os.killpg(p.pid, signal.SIGTERM); return p.wait(timeout=timeout)
    except Exception:
        try: os.killpg(p.pid, signal.SIGKILL); return p.wait(timeout=1)
        except Exception: return None

def run_case(app,scenario,rep,display_num,outdir):
    case_id=f'{app}-{scenario}-r{rep}'
    work=outdir/'work'/case_id; work.mkdir(parents=True)
    xv=appp=controller=observer=scorer=actor=None
    rec={'schema':SCHEMA,'case_id':case_id,'app':app,'scenario':scenario,'rep':rep,'authority':'none','input_dispatched_for_feedback':False}
    started=time.monotonic_ns()
    try:
        xv,env=start_xvfb(display_num,work)
        appp,controller,target=launch_app(app,env,work,case_id)
        observer=display.Display(env['DISPLAY']); scorer=display.Display(env['DISPLAY']); actor=display.Display(env['DISPLAY'])
        rec['target_window_id']=int(target.id); rec['focus_after_normal_click']=focus_id(scorer)
        if app=='inkscape':
            start=window_center(target); end=[min(1100,start[0]+80),min(700,start[1]+40)]
            fake_motion(controller,*start); fake_button(controller,True); time.sleep(.025)
            rec['held_observed_during']=button1_down(scorer)
            fake_motion(controller,*end); fake_button(controller,False); time.sleep(.025)
            rec['commanded_pointer']=end; rec['release_observed_before_perturbation']=not button1_down(scorer)
            if scenario=='pointer_displaced': fake_motion(actor,760,520); time.sleep(.02)
            if scenario=='observer_unavailable': observer.close(); observer=None
            try:
                obs=pointer_xy(observer); neutral=not button1_down(observer)
                rec['candidate_observation']={'pointer':obs,'neutral':neutral}; rec['candidate_class']='MATCH' if obs==end and neutral else 'MISMATCH'
            except Exception as e:
                rec['candidate_observation_error']=type(e).__name__; rec['candidate_class']='UNKNOWN'
            actual=pointer_xy(scorer); rec['scorer_actual']={'pointer':actual,'neutral':not button1_down(scorer)}; rec['actual_match']=actual==end and rec['scorer_actual']['neutral']
        else:
            commanded_focus=focus_id(scorer)
            if not commanded_focus: raise RuntimeError('NO_FOCUS_AFTER_NORMAL_CLICK')
            rec['commanded_focus']=commanded_focus
            kc=keycode(controller,'a'); rec['keycode']=kc
            fake_key(controller,kc,True); time.sleep(.025); rec['held_observed_during']=key_down_in_map(scorer,kc)
            fake_key(controller,kc,False); time.sleep(.025); rec['release_observed_before_perturbation']=not key_down_in_map(scorer,kc)
            if scenario=='focus_transferred':
                root=actor.screen().root
                helper=root.create_window(20,20,160,100,0,root.get_geometry().depth,X.InputOutput,X.CopyFromParent,background_pixel=0xffffff,event_mask=0)
                helper.map(); actor.sync()
                for _ in range(20):
                    if helper.get_attributes().map_state == X.IsViewable: break
                    time.sleep(.01)
                helper.set_input_focus(X.RevertToPointerRoot,X.CurrentTime); actor.sync(); time.sleep(.03); rec['helper_window_id']=int(helper.id)
            if scenario=='observer_unavailable': observer.close(); observer=None
            try:
                obs=focus_id(observer); neutral=not key_down_in_map(observer,kc)
                rec['candidate_observation']={'focus':obs,'neutral':neutral}; rec['candidate_class']='MATCH' if obs==commanded_focus and neutral else 'MISMATCH'
            except Exception as e:
                rec['candidate_observation_error']=type(e).__name__; rec['candidate_class']='UNKNOWN'
            actual=focus_id(scorer); rec['scorer_actual']={'focus':actual,'neutral':not key_down_in_map(scorer,kc)}; rec['actual_match']=actual==commanded_focus and rec['scorer_actual']['neutral']
        rec['naive_command_only_class']='MATCH'; rec['cleanup_neutral']=bool(rec['scorer_actual']['neutral']); rec['status']='ok'
    except Exception as e:
        rec['status']='error'; rec['error']=f'{type(e).__name__}: {e}'
    finally:
        rec['elapsed_ms']=(time.monotonic_ns()-started)/1e6
        for d in (observer,scorer,actor,controller):
            try:
                if d: d.close()
            except Exception: pass
        rec['app_exit']=stop_proc(appp,2); rec['xvfb_exit']=stop_proc(xv,1)
    return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--app',choices=['inkscape','calc','all'],default='all'); ap.add_argument('--rep',type=int,default=0); ap.add_argument('--out',required=True); ap.add_argument('--display-base',type=int,default=170)
    a=ap.parse_args(); out=Path(a.out)
    if out.exists(): raise SystemExit('output exists')
    out.mkdir(parents=True)
    cases=[c for c in CASES if a.app=='all' or c[0]==a.app]
    rows=[]
    for i,(app,scenario) in enumerate(cases): rows.append(run_case(app,scenario,a.rep,a.display_base+i,out))
    raw={'schema':SCHEMA,'rep':a.rep,'rows':rows}; (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n')
    ok=all(r.get('status')=='ok' and r.get('held_observed_during') and r.get('release_observed_before_perturbation') and r.get('cleanup_neutral') for r in rows)
    print(json.dumps({'rows':len(rows),'construction_integrity':ok,'statuses':[r.get('status') for r in rows],'elapsed_ms':[round(r.get('elapsed_ms',0),1) for r in rows]},sort_keys=True)); return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
