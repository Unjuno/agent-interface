"""Private desktop + unchanged InputOwner v10; no game-state access here."""
from pathlib import Path
import os, sys, time, json, hashlib
from PIL import ImageGrab
from Xlib import display

def configure(source):
    root=Path(source).resolve()
    sys.path[:0]=[str(root/'research/observation_gating'),str(root/'research/live_control'),str(root/'research/doom')]
    return root

def desktop(source):
    configure(source)
    from gui_suite import Session as Original
    class Session(Original):
        def _wait(self,fn,timeout,label):
            if label=='Xvfb': os.environ['XAUTHORITY']=str(self.auth)
            return super()._wait(fn,timeout,label)
    s=Session()
    for k in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR','XDG_DATA_HOME'):
        if k in s.env: os.environ[k]=s.env[k]
    os.environ['SDL_VIDEODRIVER']='x11'
    os.environ.pop('WAYLAND_DISPLAY',None)
    return s

def context(s,word):
    lines=[r for r in s.windows().splitlines() if word.lower() in r.lower()]
    if len(lines)!=1: raise RuntimeError(f'expected one {word} surface: {lines}')
    row=lines[0]; s.focus(' '.join(row.split()[3:]));time.sleep(.15)
    wid=int(row.split()[0],16); win=s.d.create_resource_object('window',wid)
    geo=win.get_geometry();pos=s.d.screen().root.translate_coords(win,0,0)
    return dict(display=s.name,focus=s.d.get_input_focus().focus.id,surface=wid,geometry=[pos.x,pos.y,geo.width,geo.height])

def screenshot(name,box):
    x,y,w,h=box
    return ImageGrab.grab(xdisplay=name).convert('RGB').crop((x,y,x+w,y+h))

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Inputs:
    def __init__(self,source,ctx,events):
        configure(source)
        from input_owner_v10 import InputOwner
        from lease import Lease
        self.owner=InputOwner(ctx['display']);self.Lease=Lease;self.ctx=ctx;self.events=events
    def lease(self,seconds):
        l=self.Lease(time.perf_counter_ns()+int((seconds+.18)*1e9))
        l.expected_focus=self.ctx['focus'];l.expected_surface=self.ctx['surface'];l.expected_geometry=self.ctx['geometry']
        return l
    def release(self,l):
        r=self.owner.call('release',l)
        if not r.get('verified') or r.get('keys_down') or r.get('buttons_down'): raise RuntimeError('unverified release')
        return r
    def press(self,keys,seconds=.04,settle=.10,purpose='task'):
        if not 0<seconds<=.5:raise ValueError('key-pulse budget')
        if isinstance(keys,str): keys=[keys]
        l=self.lease(seconds);downs=[];up_ns=None
        try:
            for k in keys:downs.append(self.owner.call('down',l,k))
            time.sleep(seconds)
        finally:
            up_ns=time.perf_counter_ns()
            for k in reversed(keys):self.owner.call('up',l,k)
            released=self.release(l)
            self.events.append(dict(kind='input',purpose=purpose,keys=keys,requested_seconds=seconds,downs=downs,up_started_ns=up_ns,release=released))
        time.sleep(settle)
    def click(self,x,y,purpose='target'):
        l=self.lease(.12);receipts=[]
        try:
            receipts.append(self.owner.call('move',l,dict(x=int(round(x)),y=int(round(y)))))
            receipts.append(self.owner.call('button_down',l,1));time.sleep(.03)
        finally:
            up=time.perf_counter_ns();self.owner.call('button_up',l,1);r=self.release(l)
            self.events.append(dict(kind='pointer',purpose=purpose,receipts=receipts,up_started_ns=up,release=r))
        time.sleep(.12)
    def close(self):self.owner.close()
