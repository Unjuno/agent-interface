from __future__ import annotations
import argparse, json, os, subprocess, sys, time, hashlib
from pathlib import Path
from PIL import ImageGrab
from Xlib import X, display
from Xlib.ext import xtest

RADIUS=5; MAX_PIXEL_ERROR=8.0
p=argparse.ArgumentParser(); p.add_argument('--case-id',required=True); p.add_argument('--arm',choices=['stable','swap'],required=True); p.add_argument('--display-num',type=int,required=True); p.add_argument('--out',required=True)
a=p.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
name=f':{a.display_num}'; xauth=out/'empty.Xauthority'; xauth.write_bytes(b'')
env=os.environ.copy(); env['DISPLAY']=name; env['XAUTHORITY']=str(xauth); os.environ.update({'DISPLAY':name,'XAUTHORITY':str(xauth)})
xvlog=(out/'xvfb.log').open('wb'); xv=subprocess.Popen(['Xvfb',name,'-screen','0','640x480x24','-ac'],stdout=xvlog,stderr=subprocess.STDOUT,env=env)

def wait_display():
    end=time.monotonic()+3; last=None
    while time.monotonic()<end:
        try:return display.Display(name)
        except Exception as exc:last=exc;time.sleep(.02)
    raise RuntimeError(f'display unavailable: {last!r}')

def rgb_sha(im): return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()

d=wait_display(); control=out/'control'; ready=out/'ready.json'; mutated=out/'mutated.json'; events=out/'events.jsonl'
app_out=(out/'app.stdout').open('wb'); app_err=(out/'app.stderr').open('wb')
app=subprocess.Popen([sys.executable,str(Path(__file__).with_name('app.py')),'--control',str(control),'--ready',str(ready),'--mutated',str(mutated),'--events',str(events)],env=env,stdout=app_out,stderr=app_err)
try:
    end=time.monotonic()+4
    while not ready.exists() and time.monotonic()<end:
        if app.poll() is not None:raise RuntimeError('app exited before ready')
        time.sleep(.01)
    if not ready.exists(): raise RuntimeError('ready timeout')
    info=json.loads(ready.read_text()); ax,ay=info['A']
    time.sleep(.05)
    ref_started=time.perf_counter_ns(); ref=ImageGrab.grab(xdisplay=name).convert('RGB'); ref_done=time.perf_counter_ns(); ref.save(out/'reference.png')
    time.sleep(.03)
    pre_started=time.perf_counter_ns(); pre=ImageGrab.grab(xdisplay=name).convert('RGB'); pre_done=time.perf_counter_ns(); pre.save(out/'pre.png')
    r=RADIUS; rb=ref.crop((ax-r,ay-r,ax+r+1,ay+r+1)).tobytes(); pb=pre.crop((ax-r,ay-r,ax+r+1,ay+r+1)).tobytes(); diff=max(abs(x-y) for x,y in zip(rb,pb)); eligible=diff<=MAX_PIXEL_ERROR
    gated_ns=time.perf_counter_ns()
    if not eligible:raise RuntimeError(f'pre-action gate false: {diff}')
    mutation=None
    if a.arm=='swap':
        control.write_text('swap')
        end=time.monotonic()+3
        while not mutated.exists() and time.monotonic()<end:time.sleep(.005)
        if not mutated.exists(): raise RuntimeError('mutation receipt timeout')
        mutation=json.loads(mutated.read_text())
    click_started=time.perf_counter_ns(); xtest.fake_input(d,X.MotionNotify,x=ax,y=ay); d.sync(); xtest.fake_input(d,X.ButtonPress,1); d.sync(); xtest.fake_input(d,X.ButtonRelease,1); d.sync(); click_done=time.perf_counter_ns()
    time.sleep(.08)
    final_started=time.perf_counter_ns(); final=ImageGrab.grab(xdisplay=name).convert('RGB'); final_done=time.perf_counter_ns(); final.save(out/'final.png')
    fb=final.crop((ax-r,ay-r,ax+r+1,ay+r+1)).tobytes(); finaldiff=max(abs(x-y) for x,y in zip(pb,fb))
    rows=[json.loads(x) for x in events.read_text().splitlines() if x.strip()]; clicks=[x for x in rows if x['event']=='click']; mask=d.screen().root.query_pointer().mask
    result={'case_id':a.case_id,'arm':a.arm,'gate_contract':{'radius':RADIUS,'max_pixel_error_le':MAX_PIXEL_ERROR},'gate_eligible':eligible,'gate_diff':diff,'gated_ns':gated_ns,'mutation':mutation,'click_started_ns':click_started,'click_done_ns':click_done,'captures':{'reference':[ref_started,ref_done,rgb_sha(ref)],'pre':[pre_started,pre_done,rgb_sha(pre)],'final':[final_started,final_done,rgb_sha(final)]},'events':rows,'clicks':clicks,'final_patch_diff_from_gated':finaldiff,'button1_down_terminal':bool(mask & X.Button1Mask),'A':[ax,ay]}
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'case_id':a.case_id,'arm':a.arm,'role':clicks[0]['role'] if len(clicks)==1 else None,'gate':eligible,'final_patch_diff':finaldiff},sort_keys=True))
finally:
    if app.poll() is None: app.terminate()
    try:app.wait(timeout=1)
    except:app.kill()
    d.close(); xv.terminate()
    try:xv.wait(timeout=1)
    except:xv.kill()
    app_out.close();app_err.close();xvlog.close()
