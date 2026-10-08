import ctypes, json, os, subprocess, tempfile, time
from pathlib import Path
lib=ctypes.CDLL('libX11.so.6')
lib.XOpenDisplay.argtypes=[ctypes.c_char_p]; lib.XOpenDisplay.restype=ctypes.c_void_p
lib.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]; lib.XSetInputFocus.restype=ctypes.c_int
lib.XFlush.argtypes=[ctypes.c_void_p]
DISPLAY=':145'; root=Path(tempfile.mkdtemp(prefix='lo3046-direct-')); auth=root/'Xauthority'; auth.touch(mode=0o600)
env=os.environ.copy(); env.update(DISPLAY=DISPLAY,XAUTHORITY=str(auth))
def run(a):
 q=subprocess.run(a,env=env,text=True,capture_output=True); return {'rc':q.returncode,'out':q.stdout.strip(),'err':q.stderr.strip()}
procs=[]
try:
 xv=subprocess.Popen(['Xvfb',DISPLAY,'-screen','0','1600x1000x24','-auth',str(auth)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(xv); time.sleep(.6)
 wm=subprocess.Popen(['openbox','--sm-disable'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(wm); time.sleep(.7)
 lo=subprocess.Popen(['libreoffice','--norestore','--nodefault','--nolockcheck','--calc'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(lo); time.sleep(2.5)
 wins=run(['xdotool','search','--onlyvisible','--name','.*'])['out'].splitlines(); target=next((w for w in wins if run(['xdotool','getwindowname',w])['out']!='Openbox'),None)
 d=lib.XOpenDisplay(DISPLAY.encode()); before=run(['xdotool','getwindowfocus']); direct_rc=lib.XSetInputFocus(d,int(target),2,0) if d and target else -1; lib.XFlush(d) if d else None; time.sleep(.4); after=run(['xdotool','getwindowfocus']); active=run(['xdotool','getactivewindow'])
 print(json.dumps({'decision':'PASS_DIRECT_CORE_FOCUS' if target and after['rc']==0 and after['out']==target else 'HOLD_DIRECT_FOCUS_NOT_OBSERVED','target':target,'before':before,'xsetinputfocus_rc':direct_rc,'after':after,'active':active,'model_calls':0,'network_calls':0},sort_keys=True))
finally:
 for p in reversed(procs):
  if p.poll() is None: p.terminate()
