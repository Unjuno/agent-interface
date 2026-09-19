#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys, time, tempfile, socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any
import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest

W,H=800,600

def emit(path: Path, row: dict):
    row=dict(row); row.setdefault('ns', time.monotonic_ns())
    with path.open('a',encoding='utf-8') as f: f.write(json.dumps(row,sort_keys=True)+'\n')

def wait_path(path: Path, timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists() and path.stat().st_size: return
        time.sleep(.02)
    raise TimeoutError(path)

def xconn():
    d=display.Display(); return d,d.screen().root

def root_rgb(root,x,y):
    im=root.get_image(x,y,1,1,X.ZPixmap,0xffffffff)
    b=im.data
    # Xvfb is BGRX on this environment.
    return (b[2],b[1],b[0])

def fake_key(d, keysym_name:str, down:bool):
    ks=XK.string_to_keysym(keysym_name)
    code=d.keysym_to_keycode(ks)
    xtest.fake_input(d, X.KeyPress if down else X.KeyRelease, code)
    d.sync()

def hold_key(name, ms):
    d,_=xconn(); fake_key(d,name,True); time.sleep(ms/1000); fake_key(d,name,False); d.close()

def click(x,y):
    d,_=xconn();
    xtest.fake_input(d,X.MotionNotify,x=x,y=y); d.sync()
    xtest.fake_input(d,X.ButtonPress,1); d.sync(); time.sleep(.025)
    xtest.fake_input(d,X.ButtonRelease,1); d.sync(); d.close()

def type_text(text):
    d,_=xconn()
    for ch in text:
        name=ch
        ks=XK.string_to_keysym(name)
        if ks==0: raise ValueError(ch)
        code=d.keysym_to_keycode(ks)
        xtest.fake_input(d,X.KeyPress,code); d.sync(); time.sleep(.008)
        xtest.fake_input(d,X.KeyRelease,code); d.sync(); time.sleep(.008)
    d.close()

def focus_mapped_window(width:int, height:int):
    d,root=xconn()
    candidates=[]
    def walk(w,depth=0):
        if depth>3: return
        try:
            for c in w.query_tree().children:
                try:
                    g=c.get_geometry(); a=c.get_attributes()
                    if a.map_state==X.IsViewable:
                        if g.width==width and g.height==height: candidates.append(c)
                        walk(c,depth+1)
                except Exception: pass
        except Exception: pass
    walk(root)
    if not candidates:
        d.close(); return False
    candidates[-1].set_input_focus(X.RevertToParent, X.CurrentTime); d.sync(); d.close(); return True

def release_all():
    # release our bounded primitive keys/buttons only
    d,_=xconn()
    for name in ['Left','Right']:
        code=d.keysym_to_keycode(XK.string_to_keysym(name)); xtest.fake_input(d,X.KeyRelease,code)
    xtest.fake_input(d,X.ButtonRelease,1); d.sync(); d.close()

@dataclass(frozen=True)
class Contract:
    name: str
    max_transitions: int
    expiry_s: float
    terminal: frozenset[str]
    invalid: frozenset[str]
    rules: dict[str, dict]

class GenericExecutor:
    def __init__(self, contract:Contract, observe:Callable[[],str], log:Path):
        self.contract=contract; self.observe=observe; self.log=log
    def run(self):
        start=time.monotonic(); transitions=0; actions=0; status='UNKNOWN'
        try:
            while transitions < self.contract.max_transitions and time.monotonic()-start < self.contract.expiry_s:
                label=self.observe(); transitions += 1
                emit(self.log, {'kind':'observe','label':label,'transition':transitions})
                if label in self.contract.terminal:
                    status='COMPLETED'; break
                if label in self.contract.invalid:
                    status='INVALIDATED'; break
                rule=self.contract.rules.get(label)
                if rule is None:
                    status='UNKNOWN'; break
                self._act(rule); actions += 1
                emit(self.log, {'kind':'action','label':label,'action':rule,'action_index':actions})
            else:
                status='EXPIRED' if time.monotonic()-start >= self.contract.expiry_s else 'BUDGET'
        finally:
            release_all(); emit(self.log,{'kind':'release_all','status':status})
        result={'status':status,'transitions':transitions,'actions':actions,'elapsed_s':time.monotonic()-start}
        emit(self.log,{'kind':'terminal',**result}); return result
    def _act(self, a:dict):
        k=a['kind']
        if k=='hold': hold_key(a['key'], a['ms'])
        elif k=='click': click(a['x'],a['y'])
        elif k=='click_type': click(a['x'],a['y']); type_text(a['text'])
        elif k=='line':
            click(a.get('x',400),a.get('y',300)); type_text(a['text']); hold_key('Return',20)
        elif k=='sleep': time.sleep(a['ms']/1000)
        else: raise ValueError(k)

# ---------- tracker domain ----------

def tracker_app(score:Path, inp:Path, variant:str):
    root=tk.Tk(); root.overrideredirect(True); root.geometry(f'{W}x220+0+0')
    c=tk.Canvas(root,width=W,height=220,bg='#101010',highlightthickness=0); c.pack()
    center=400; c.create_rectangle(360,80,440,140,outline='#00ff00',width=3)
    x=[690.0]; left=[False]; right=[False]; start=time.monotonic(); vanished=[False]
    marker=c.create_rectangle(x[0]-9,95,x[0]+9,125,fill='#ff0000',outline='')
    def kd(e):
        if e.keysym=='Left': left[0]=True
        if e.keysym=='Right': right[0]=True
        emit(inp,{'kind':'key','event':'down','key':e.keysym})
    def ku(e):
        if e.keysym=='Left': left[0]=False
        if e.keysym=='Right': right[0]=False
        emit(inp,{'kind':'key','event':'up','key':e.keysym})
    root.bind('<KeyPress>',kd); root.bind('<KeyRelease>',ku); root.after(120, lambda: (root.focus_force(), root.focus_set()))
    def tick():
        t=time.monotonic()-start
        # exogenous right drift + actual key response
        vel=18.0
        if left[0]: vel-=250.0
        if right[0]: vel+=250.0
        x[0]+=vel*0.016; x[0]=max(20,min(780,x[0]))
        if variant=='vanish' and t>0.34 and not vanished[0]:
            c.itemconfigure(marker, state='hidden'); vanished[0]=True
        if not vanished[0]: c.coords(marker,x[0]-9,95,x[0]+9,125)
        emit(score,{'kind':'sample','x':x[0],'left':left[0],'right':right[0],'visible':not vanished[0]})
        if t<3.2: root.after(16,tick)
        else: root.destroy()
    root.after(80,tick); root.mainloop()

def tracker_observer():
    d,root=xconn();
    # find red pixels in tracker ROI
    im=root.get_image(0,70,W,90,X.ZPixmap,0xffffffff); data=im.data
    xs=[]
    # BGRA 4 bytes
    for yy in range(90):
        row=yy*W*4
        for xx in range(0,W,2):
            i=row+xx*4; b,g,r=data[i],data[i+1],data[i+2]
            if r>220 and g<70 and b<70: xs.append(xx)
    d.close()
    if not xs: return 'MISSING'
    mx=sum(xs)/len(xs)
    if mx>445: return 'RIGHT'
    if mx<355: return 'LEFT'
    return 'GOAL'

def tracker_controller(out:Path):
    # focus tracker by mapped X window identity
    if not focus_mapped_window(W,220):
        click(400,110)
    stable=[0]
    def obs():
        label=tracker_observer()
        if label=='GOAL':
            stable[0]+=1
            if stable[0]>=3: return 'SUCCESS'
        else: stable[0]=0
        return label
    contract=Contract('cross-domain-reactive-v1',24,2.2,frozenset({'SUCCESS'}),frozenset({'MISSING'}),{
        'RIGHT':{'kind':'hold','key':'Left','ms':90},
        'LEFT':{'kind':'hold','key':'Right','ms':90},
        'GOAL':{'kind':'sleep','ms':45},
    })
    res=GenericExecutor(contract,obs,out).run(); print(json.dumps(res))
    return 0 if res['status'] in ('COMPLETED','INVALIDATED') else 2

# ---------- terminal/xterm domain ----------

def terminal_app(score:Path, variant:str):
    def bg(hexv):
        sys.stdout.write(f'\x1b]11;{hexv}\x07\x1b[2J\x1b[H'); sys.stdout.flush()
    bg('#cc0000'); print('TOKEN> ',end='',flush=True)
    token=sys.stdin.readline().strip()
    if variant=='changed':
        bg('#cccc00'); print('STATE CHANGED - STOP',flush=True); time.sleep(2); return 0
    if token!='agent42':
        bg('#cccc00'); print('BAD TOKEN',flush=True); time.sleep(2); return 0
    bg('#0000cc'); print('CONFIRM> ',end='',flush=True)
    conf=sys.stdin.readline().strip().lower()
    if conf=='yes':
        emit(score,{'kind':'terminal_result','token':token,'confirmed':True}); bg('#00aa00'); print('DONE',flush=True)
    else:
        bg('#cccc00'); print('NOT CONFIRMED',flush=True)
    time.sleep(1); return 0

def screen_color_label():
    d,root=xconn(); im=root.get_image(0,0,W,H,X.ZPixmap,0xffffffff); data=im.data; d.close()
    counts={'RED':0,'BLUE':0,'GREEN':0,'YELLOW':0}
    for yy in range(100,H,20):
        for xx in range(80,W,20):
            i=(yy*W+xx)*4; b,g,r=data[i],data[i+1],data[i+2]
            if r>130 and g<80 and b<80: counts['RED']+=1
            elif b>130 and r<80 and g<80: counts['BLUE']+=1
            elif g>90 and r<80 and b<80: counts['GREEN']+=1
            elif r>130 and g>130 and b<80: counts['YELLOW']+=1
    label=max(counts,key=counts.get)
    return label if counts[label]>=5 else 'UNKNOWN'

def terminal_controller(out:Path):
    contract=Contract('cross-domain-reactive-v1',7,2.3,frozenset({'GREEN'}),frozenset({'YELLOW','UNKNOWN'}),{
        'RED':{'kind':'line','text':'agent42','x':300,'y':260},
        'BLUE':{'kind':'line','text':'yes','x':300,'y':260},
    })
    res=GenericExecutor(contract,screen_color_label,out).run(); print(json.dumps(res))
    return 0 if res['status'] in ('COMPLETED','INVALIDATED') else 2

def run_terminal(root:Path,variant:str,idx:int):
    d=root/f'terminal-{variant}'; d.mkdir(); score=d/'score.jsonl'; ctl=d/'controller.jsonl'
    disp,env,xvfb,wm=start_x(200+idx)
    # real xterm transport; child is a tiny stateful TUI fixture.
    app=subprocess.Popen(['xterm','-fullscreen','-bg','#cc0000','-fg','white','-e',sys.executable,__file__,'--terminal-app',str(score),variant],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    old_display=os.environ.get('DISPLAY'); old_xauth=os.environ.get('XAUTHORITY'); os.environ['DISPLAY']=disp; os.environ['XAUTHORITY']=env['XAUTHORITY']
    ready=False
    for _ in range(80):
        try:
            if screen_color_label()=='RED': ready=True; break
        except Exception: pass
        time.sleep(.04)
    if not ready:
        app.terminate(); wm.terminate(); xvfb.terminate(); raise RuntimeError('xterm not ready')
    ctrl=subprocess.run([sys.executable,__file__,'--terminal-controller',str(ctl)],env=env,capture_output=True,text=True,timeout=4)
    time.sleep(.08)
    for p in (app,wm,xvfb): p.terminate()
    if old_display is None: os.environ.pop('DISPLAY',None)
    else: os.environ['DISPLAY']=old_display
    if old_xauth is None: os.environ.pop('XAUTHORITY',None)
    else: os.environ['XAUTHORITY']=old_xauth
    cr=read_rows(ctl); sr=read_rows(score); terminal=[r for r in cr if r.get('kind')=='terminal'][-1]
    success=[r for r in sr if r.get('kind')=='terminal_result']
    return {'domain':'terminal','variant':variant,'controller_status':terminal['status'],'actions':terminal['actions'],'transitions':terminal['transitions'],
            'score_success':len(success)==1 and success[0].get('token')=='agent42' and success[0].get('confirmed') is True,
            'score_rows':len(success),'expected':'COMPLETED' if variant=='positive' else 'INVALIDATED'}

# ---------- orchestration ----------

def start_x(display_num:int):
    disp=f':{display_num}'
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0',f'{W}x{H}x24','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    env=os.environ.copy(); env['DISPLAY']=disp; xauth=f'/tmp/cross-domain-xauth-{display_num}'; Path(xauth).touch(); env['XAUTHORITY']=xauth
    time.sleep(.12); wm=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.12)
    return disp,env,xvfb,wm

def read_rows(p):
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def run_tracker(root:Path,variant:str,idx:int):
    d=root/f'tracker-{variant}'; d.mkdir(); score=d/'score.jsonl'; inp=d/'input.jsonl'; ctl=d/'controller.jsonl'
    disp,env,xvfb,wm=start_x(220+idx)
    app=subprocess.Popen([sys.executable,__file__,'--tracker-app',str(score),str(inp),variant],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(.28)
    ctrl=subprocess.run([sys.executable,__file__,'--tracker-controller',str(ctl)],env=env,capture_output=True,text=True,timeout=4)
    time.sleep(.08); app.terminate(); app.wait(timeout=2)
    for p in (wm,xvfb): p.terminate()
    sr=read_rows(score); ir=read_rows(inp); cr=read_rows(ctl); terminal=[r for r in cr if r.get('kind')=='terminal'][-1]; last=sr[-1]
    downs=sum(r.get('event')=='down' for r in ir); ups=sum(r.get('event')=='up' for r in ir)
    return {'domain':'tracker','variant':variant,'controller_status':terminal['status'],'actions':terminal['actions'],'transitions':terminal['transitions'],
            'final_x':last['x'],'final_visible':last['visible'],'key_downs':downs,'key_ups':ups,'balanced':downs==ups}

def run_terminal(root:Path,variant:str,idx:int):
    d=root/f'terminal-{variant}'; d.mkdir(); score=d/'score.jsonl'; ctl=d/'controller.jsonl'
    disp,env,xvfb,wm=start_x(230+idx)
    app=subprocess.Popen(['xterm','-fullscreen','-bg','#cc0000','-fg','white','-e',sys.executable,__file__,'--terminal-app',str(score),variant],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    old_display=os.environ.get('DISPLAY'); old_xauth=os.environ.get('XAUTHORITY'); os.environ['DISPLAY']=disp; os.environ['XAUTHORITY']=env['XAUTHORITY']
    ready=False
    for _ in range(80):
        try:
            if screen_color_label()=='RED': ready=True; break
        except Exception: pass
        time.sleep(.04)
    if not ready: raise RuntimeError('xterm not ready')
    subprocess.run([sys.executable,__file__,'--terminal-controller',str(ctl)],env=env,capture_output=True,text=True,timeout=4)
    time.sleep(.08)
    for p in (app,wm,xvfb): p.terminate()
    if old_display is None: os.environ.pop('DISPLAY',None)
    else: os.environ['DISPLAY']=old_display
    if old_xauth is None: os.environ.pop('XAUTHORITY',None)
    else: os.environ['XAUTHORITY']=old_xauth
    cr=read_rows(ctl); sr=read_rows(score); terminal=[r for r in cr if r.get('kind')=='terminal'][-1]; success=[r for r in sr if r.get('kind')=='terminal_result']
    return {'domain':'terminal','variant':variant,'controller_status':terminal['status'],'actions':terminal['actions'],'transitions':terminal['transitions'],
            'score_success':len(success)==1 and success[0].get('token')=='agent42' and success[0].get('confirmed') is True,'score_rows':len(success)}

def orchestrate(out:Path):
    if out.exists(): raise FileExistsError(out)
    out.mkdir(parents=True)
    results=[run_tracker(out,'positive',1),run_tracker(out,'vanish',2),run_terminal(out,'positive',1),run_terminal(out,'changed',2)]
    gates={
      'tracker_positive_complete':results[0]['controller_status']=='COMPLETED',
      'tracker_missing_invalidates':results[1]['controller_status']=='INVALIDATED',
      'tracker_release_balanced':results[0]['balanced'] and results[1]['balanced'],
      'terminal_positive_complete':results[2]['controller_status']=='COMPLETED' and results[2]['score_success'],
      'terminal_changed_invalidates_without_score':results[3]['controller_status']=='INVALIDATED' and results[3]['score_rows']==0,
      'positive_multi_transition':results[0]['actions']>=2 and results[2]['actions']>=2,
    }
    summary={'schema':'cross-domain-reactive-method-container-v1','core_contract_name':'cross-domain-reactive-v1','results':results,'gates':gates,'pass':all(gates.values())}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,indent=2)); return 0 if summary['pass'] else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tracker-app',nargs=3); ap.add_argument('--tracker-controller'); ap.add_argument('--terminal-app',nargs=2); ap.add_argument('--terminal-controller'); ap.add_argument('--out'); a=ap.parse_args()
    if a.tracker_app: return tracker_app(Path(a.tracker_app[0]),Path(a.tracker_app[1]),a.tracker_app[2]) or 0
    if a.tracker_controller: return tracker_controller(Path(a.tracker_controller))
    if a.terminal_app: return terminal_app(Path(a.terminal_app[0]),a.terminal_app[1])
    if a.terminal_controller: return terminal_controller(Path(a.terminal_controller))
    if a.out: return orchestrate(Path(a.out))
    ap.error('mode required')
if __name__=='__main__': raise SystemExit(main())
