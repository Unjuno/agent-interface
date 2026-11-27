import ctypes as C, ctypes.util, subprocess, time, json, hashlib, pathlib, os
out={'formal_cases':0,'scope':'private Xvfb construction only','pid':os.getpid(),'start_ns':time.monotonic_ns(),'states':[]}
p=subprocess.Popen(['Xvfb',':77','-screen','0','64x64x24','-nolisten','tcp','-noreset','+extension','XTEST'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
d=None
try:
 x=C.CDLL(ctypes.util.find_library('X11')); t=C.CDLL(ctypes.util.find_library('Xtst'))
 x.XOpenDisplay.argtypes=[C.c_char_p]; x.XOpenDisplay.restype=C.c_void_p
 x.XStringToKeysym.argtypes=[C.c_char_p]; x.XStringToKeysym.restype=C.c_ulong
 x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong]; x.XKeysymToKeycode.restype=C.c_ubyte
 x.XQueryKeymap.argtypes=[C.c_void_p,C.c_void_p]; x.XQueryKeymap.restype=C.c_int
 x.XSync.argtypes=[C.c_void_p,C.c_int]; x.XCloseDisplay.argtypes=[C.c_void_p]
 t.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]; t.XTestFakeKeyEvent.restype=C.c_int
 deadline=time.monotonic()+2
 while not d and time.monotonic()<deadline:
  d=x.XOpenDisplay(b':77')
  if not d: time.sleep(.02)
 assert d,'display startup failed'
 k=x.XKeysymToKeycode(d,x.XStringToKeysym(b'Shift_L')); assert k
 def state(label):
  b=(C.c_ubyte*32)(); rc=x.XQueryKeymap(d,b); held=bool(b[k//8]&(1<<(k%8))); out['states'].append({'label':label,'query_rc':rc,'keymap_hex':bytes(b).hex(),'held':held,'ns':time.monotonic_ns()}); return held
 assert not state('initial')
 assert t.XTestFakeKeyEvent(d,k,1,0); x.XSync(d,0); assert state('pressed')
 assert t.XTestFakeKeyEvent(d,k,0,0); x.XSync(d,0); assert not state('released')
 out['keycode']=k; out['result']='PASS_CONSTRUCTION'
except BaseException as e:
 out['result']='FAIL_CONSTRUCTION'; out['error']=repr(e)
finally:
 if d:
  t.XTestFakeKeyEvent(d,k,0,0); x.XSync(d,0); x.XCloseDisplay(d)
 p.terminate(); so,se=p.communicate(timeout=2); out['server_exit']=p.returncode; out['server_stdout']=so.decode(); out['server_stderr']=se.decode()
 out['end_ns']=time.monotonic_ns(); out['packages']=subprocess.check_output(['dpkg-query','-W','xvfb','libxtst6','libx11-6']).decode()
 out['cgroup']={n:pathlib.Path('/sys/fs/cgroup/'+n).read_text().strip() for n in ['cpu.max','memory.max','memory.swap.max','pids.max']}
 print(json.dumps(out,sort_keys=True)); pathlib.Path('/out/CONSTRUCTION.json').write_text(json.dumps(out,indent=2)+'\n')
assert out['result']=='PASS_CONSTRUCTION'
