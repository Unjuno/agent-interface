import json, os, re, subprocess, tempfile, time
from pathlib import Path

DISPLAY=':142'
root=Path(tempfile.mkdtemp(prefix='lo3042-'))
env=os.environ.copy(); env.update(DISPLAY=DISPLAY, XAUTHORITY=str(root/'Xauthority'))
(root/'Xauthority').touch(mode=0o600)
def run(argv, timeout=4):
    try:
        q=subprocess.run(argv,env=env,text=True,capture_output=True,timeout=timeout)
        return {'argv':argv,'rc':q.returncode,'out':q.stdout.strip(),'err':q.stderr.strip()}
    except subprocess.TimeoutExpired as e:
        return {'argv':argv,'rc':124,'out':str(e.stdout or ''),'err':str(e.stderr or 'timeout')}
def visible():
    q=run(['xdotool','search','--onlyvisible','--name','.*'])
    return [x for x in q['out'].splitlines() if x.strip()]
def inspect(wid):
    name=run(['xdotool','getwindowname',wid]); cls=run(['xprop','-id',wid,'WM_CLASS'])
    geo=run(['xdotool','getwindowgeometry',wid]); return {'window':wid,'name':name['out'],'class':cls['out'],'geometry':geo['out']}
def active(): return run(['xdotool','getactivewindow'])
procs=[]; events=[]
try:
    xv=subprocess.Popen(['Xvfb',DISPLAY,'-screen','0','1600x1000x24','-auth',env['XAUTHORITY']],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(xv); time.sleep(.7)
    wm=subprocess.Popen(['openbox','--sm-disable'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(wm); time.sleep(.7)
    lo=subprocess.Popen(['libreoffice','--norestore','--nodefault','--nolockcheck','--calc'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(lo)
    time.sleep(3); events.append({'kind':'initial','windows':[inspect(w) for w in visible()],'active':active()})
    candidates=[w for w in visible() if inspect(w)['name'] != 'Openbox']
    target=candidates[0] if candidates else None
    if target:
        events.append({'kind':'activate','target':target,'result':run(['xdotool','windowactivate','--sync',target]),'active':active()})
        events.append({'kind':'focus','target':target,'result':run(['xdotool','windowfocus','--sync',target]),'active':active()})
        events.append({'kind':'net_active','result':run(['xprop','-root','_NET_ACTIVE_WINDOW']),'active':active()})
        events.append({'kind':'modal_open','result':run(['xdotool','key','ctrl+o']),'active':active()}); time.sleep(1)
        events.append({'kind':'after_modal','windows':[inspect(w) for w in visible()],'active':active()})
        events.append({'kind':'escape','result':run(['xdotool','key','Escape']),'active':active()}); time.sleep(.5)
        events.append({'kind':'return_activate','target':target,'result':run(['xdotool','windowactivate','--sync',target]),'active':active(),'net_active':run(['xprop','-root','_NET_ACTIVE_WINDOW'])})
    active_ok = any(e.get('kind') == 'net_active' and e['result']['out'] and 'not found' not in e['result']['out'] for e in events)
    decision = 'PASS_LO3042_ACTIVE_CONTRACT' if target and active_ok else ('HOLD_NO_ACTIVE_WINDOW_CONTRACT' if target else 'HOLD_NO_WINDOW')
    print(json.dumps({'decision':decision,'events':events,'model_calls':0,'network_calls':0},sort_keys=True))
finally:
    for p in reversed(procs):
        if p.poll() is None: p.terminate()
