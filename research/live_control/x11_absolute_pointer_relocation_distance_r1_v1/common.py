from __future__ import annotations
import os, subprocess, time
from pathlib import Path
from Xlib import X, display
from Xlib.ext import xtest

WIDTH=800; HEIGHT=600; CX=400; CY=300
DISTANCES=(1,8,64,256)
BUTTON_MASK = X.Button1Mask|X.Button2Mask|X.Button3Mask|X.Button4Mask|X.Button5Mask

def pick_display(start=90,end=120):
    sock=Path('/tmp/.X11-unix')
    for n in range(start,end):
        if not (sock/f'X{n}').exists(): return n
    raise RuntimeError('no free X display')

def start_xvfb():
    auth=Path('/tmp/ai1684-empty.Xauthority'); auth.write_bytes(b''); os.environ['XAUTHORITY']=str(auth)
    n=pick_display(); name=f':{n}'
    p=subprocess.Popen(['Xvfb',name,'-screen','0',f'{WIDTH}x{HEIGHT}x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    deadline=time.time()+3
    last=None
    while time.time()<deadline:
        if p.poll() is not None: raise RuntimeError('Xvfb exited: '+(p.stderr.read() if p.stderr else ''))
        try:
            d=display.Display(name); d.close(); return p,name
        except Exception as e:
            last=e; time.sleep(.03)
    p.terminate(); p.wait(timeout=2); raise RuntimeError(f'Xvfb readiness: {last!r}')

def stop_xvfb(p):
    if p.poll() is None:
        p.terminate()
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            p.kill();p.wait(timeout=2)

def move_sync(d,x,y):
    t0=time.perf_counter_ns(); xtest.fake_input(d,X.MotionNotify,x=int(x),y=int(y)); d.sync(); t1=time.perf_counter_ns(); return t0,t1

def read_pointer(d):
    q=d.screen().root.query_pointer(); return int(q.root_x),int(q.root_y),int(q.mask)

def reset(actor,observer):
    move_sync(actor,CX,CY)
    x,y,mask=read_pointer(observer)
    if (x,y)!=(CX,CY) or (mask&BUTTON_MASK): raise RuntimeError(f'reset readback {(x,y,mask)}')

def stepwise(actor,distance):
    reset_actor_start=time.perf_counter_ns()
    for dx in range(1,distance+1): xtest.fake_input(actor,X.MotionNotify,x=CX+dx,y=CY)
    actor.sync(); return time.perf_counter_ns()-reset_actor_start
