from __future__ import annotations
import argparse, json, os, subprocess, sys, time, hashlib
from pathlib import Path
from PIL import ImageGrab
from Xlib import X, display
from Xlib.ext import xtest

RADIUS=5; MAX_PIXEL_ERROR=8.0
p=argparse.ArgumentParser(); p.add_argument('--case-id',required=True); p.add_argument('--mutation',choices=['stable','swap'],required=True); p.add_argument('--policy',choices=['single_gate','preinput_revalidate'],required=True); p.add_argument('--display-num',type=int,required=True); p.add_argument('--out',required=True)
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
def patch_diff(ref,cur,ax,ay):
    r=RADIUS; rb=ref.crop((ax-r,ay-r,ax+r+1,ay+r+1)).tobytes(); cb=cur.crop((ax-r,ay-r,ax+r+1,ay+r+1)).tobytes(); return max(abs(x-y) for x,y in zip(rb,cb))

d=wait_display(); control=out/'control'; ready=out/'ready.json'; mutated=out/'mutated.json'; events=out/'events.jsonl'
app_out=(out/'app.stdout').open('wb'); app_err=(out/'app.stderr').open('wb')
app=subprocess.Popen([sys.executable,str(Path(__file__).with_name('app.py')),'--control',str(control),'--ready',str(ready),'--mutated',str(mutated),'--events',str(events)],env=env,stdout=app_out,stderr=app_err)
try:
    end=time.monotonic()+4
    while not ready.exists() and time.monotonic()<end:
        if app.poll() is not None:raise RuntimeError('app exited before ready')
        time.sleep(.01)
    if not ready.exists(): raise RuntimeError('ready timeout')
    info=json.loads(ready.read_text()); ax,ay=info['A']; time.sleep(.05)
    ref_started=time.perf_counter_ns(); ref=ImageGrab.grab(xdisplay=name).convert('RGB'); ref_done=time.perf_counter_ns(); ref.save(out/'reference.png')
    time.sleep(.03)
    pre_started=time.perf_counter_ns(); pre=ImageGrab.grab(xdisplay=name).convert('RGB'); pre_done=time.perf_counter_ns(); pre.save(out/'pre.png')
    first_diff=patch_diff(ref,pre,ax,ay); first_eligible=first_diff<=MAX_PIXEL_ERROR; first_gated_ns=time.perf_counter_ns()
    if not first_eligible:raise RuntimeError(f'first gate false: {first_diff}')
    mutation=None
    if a.mutation=='swap':
        control.write_text('swap'); end=time.monotonic()+3
        while not mutated.exists() and time.monotonic()<end:time.sleep(.005)
        if not mutated.exists(): raise RuntimeError('mutation receipt timeout')
        mutation=json.loads(mutated.read_text())
    admission=None; admission_diff=None; admission_started=None; admission_done=None; admission_sha=None
    if a.policy=='preinput_revalidate':
        admission_started=time.perf_counter_ns(); adm=ImageGrab.grab(xdisplay=name).convert('RGB'); admission_done=time.perf_counter_ns(); adm.save(out/'admission.png'); admission_sha=rgb_sha(adm)
        admission_diff=patch_diff(ref,adm,ax,ay); admission='ADMITTED' if admission_diff<=MAX_PIXEL_ERROR else 'TARGET_EVIDENCE_CHANGED'
    else:
        admission='ADMITTED'
    click_started=click_done=None
    if admission=='ADMITTED':
        click_started=time.perf_counter_ns(); xtest.fake_input(d,X.MotionNotify,x=ax,y=ay); d.sync(); xtest.fake_input(d,X.ButtonPress,1); d.sync(); xtest.fake_input(d,X.ButtonRelease,1); d.sync(); click_done=time.perf_counter_ns()
    time.sleep(.08)
    final_started=time.perf_counter_ns(); final=ImageGrab.grab(xdisplay=name).convert('RGB'); final_done=time.perf_counter_ns(); final.save(out/'final.png')
    rows=[json.loads(x) for x in events.read_text().splitlines() if x.strip()] if events.exists() else []; clicks=[x for x in rows if x['event']=='click']; mask=d.screen().root.query_pointer().mask
    result={'case_id':a.case_id,'mutation':a.mutation,'policy':a.policy,'gate_contract':{'radius':RADIUS,'max_pixel_error_le':MAX_PIXEL_ERROR},'first_gate_eligible':first_eligible,'first_gate_diff':first_diff,'first_gated_ns':first_gated_ns,'mutation_receipt':mutation,'admission_capture':None if a.policy=='single_gate' else {'started_ns':admission_started,'done_ns':admission_done,'rgb_sha256':admission_sha,'diff':admission_diff},'admission_disposition':admission,'click_started_ns':click_started,'click_done_ns':click_done,'captures':{'reference':[ref_started,ref_done,rgb_sha(ref)],'pre':[pre_started,pre_done,rgb_sha(pre)],'final':[final_started,final_done,rgb_sha(final)]},'events':rows,'clicks':clicks,'button1_down_terminal':bool(mask & X.Button1Mask),'A':[ax,ay]}
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'case_id':a.case_id,'mutation':a.mutation,'policy':a.policy,'admission':admission,'clicks':len(clicks),'role':clicks[0]['role'] if len(clicks)==1 else None,'admission_diff':admission_diff},sort_keys=True))
finally:
    if app.poll() is None: app.terminate()
    try:app.wait(timeout=1)
    except:app.kill()
    d.close(); xv.terminate()
    try:xv.wait(timeout=1)
    except:xv.kill()
    app_out.close();app_err.close();xvlog.close()
