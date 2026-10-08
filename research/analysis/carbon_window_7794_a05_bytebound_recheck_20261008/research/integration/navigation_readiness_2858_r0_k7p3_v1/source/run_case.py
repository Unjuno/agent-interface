from __future__ import annotations
import argparse, json, os, signal, subprocess, sys, time, traceback, urllib.request
from pathlib import Path
from Xlib import X, XK, Xatom, display
from Xlib.ext import xtest
POLICIES={'NO_EXTRA_WAIT','FIXED_100MS','REOBSERVE_ACTIVE'}
LOADS={'IDLE','CONTENDED'}
PHASES={'FRESH','SEQUENTIAL'}

def atomic_json(path,obj):
 p=Path(path); q=p.with_suffix('.tmp'); q.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); os.replace(q,p)
def title_of(win):
 try:
  atom=win.display.intern_atom('_NET_WM_NAME'); prop=win.get_full_property(atom,win.display.intern_atom('UTF8_STRING'))
  if prop is not None:
   v=prop.value
   if hasattr(v,'tobytes'): v=v.tobytes()
   if isinstance(v,(bytes,bytearray)): return bytes(v).decode('utf-8','replace').rstrip('\x00')
 except Exception: pass
 try: return win.get_wm_name() or ''
 except Exception: return ''
def active_info(d):
 root=d.screen().root; p=root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'),Xatom.WINDOW)
 if not p or not len(p.value): return {'id':None,'title':'','wm_class':None}
 wid=int(p.value[0]); w=d.create_resource_object('window',wid)
 try: wc=w.get_wm_class()
 except Exception: wc=None
 title=title_of(w)
 try:
  cp=subprocess.run(['wmctrl','-l'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=1)
  for line in cp.stdout.splitlines():
   z=line.split(None,3)
   if len(z)>=4 and int(z[0],16)==wid: title=z[3]; break
 except Exception: pass
 return {'id':wid,'title':title,'wm_class':list(wc) if wc else None}
def is_chromium(info): return 'chromium' in ' '.join(info.get('wm_class') or []).lower()
def kc(d,name):
 x=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not x: raise RuntimeError('no keycode '+name)
 return x
def chord(d,mods,key):
 m=[kc(d,x) for x in mods]; k=kc(d,key)
 for x in m: xtest.fake_input(d,X.KeyPress,x)
 xtest.fake_input(d,X.KeyPress,k); xtest.fake_input(d,X.KeyRelease,k)
 for x in reversed(m): xtest.fake_input(d,X.KeyRelease,x)
 d.sync()
def tap(d,key):
 k=kc(d,key); xtest.fake_input(d,X.KeyPress,k); xtest.fake_input(d,X.KeyRelease,k); d.sync()
def type_text(d,s):
 simple={'.':'period','/':'slash','-':'minus',';':'semicolon',',':'comma','=':'equal'}; shift=kc(d,'Shift_L')
 for ch in s:
  if ch==':': base='semicolon'; use_shift=True
  elif ch=='+': base='equal'; use_shift=True
  elif ch=='_': base='minus'; use_shift=True
  elif ch=='%': base='5'; use_shift=True
  else: base=simple.get(ch,ch); use_shift=False
  k=kc(d,base)
  if use_shift: xtest.fake_input(d,X.KeyPress,shift)
  xtest.fake_input(d,X.KeyPress,k); xtest.fake_input(d,X.KeyRelease,k)
  if use_shift: xtest.fake_input(d,X.KeyRelease,shift)
 d.sync()
def devtools_page(port):
 try:
  tabs=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json',timeout=.5).read()); pages=[x for x in tabs if x.get('type')=='page']; return pages[0] if pages else {}
 except Exception as e: return {'error':repr(e)}
def wait_url(d,port,expected,timeout=3):
 start=time.monotonic_ns(); end=time.monotonic()+timeout; samples=[]
 while time.monotonic()<end:
  info=active_info(d); page=devtools_page(port); now=time.monotonic_ns(); samples.append({'ns':now,'active':info,'page_url':page.get('url'),'page_title':page.get('title'),'page_error':page.get('error')})
  if is_chromium(info) and page.get('url')==expected: return True,now,start,samples
  time.sleep(.01)
 return False,time.monotonic_ns(),start,samples
def wait_browser(d,port,timeout=10):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  a=active_info(d); p=devtools_page(port)
  if is_chromium(a) and p.get('url') is not None: return {'active':a,'page':p}
  time.sleep(.05)
 raise RuntimeError('browser readiness timeout')
def wait_socket(n,p,timeout=5):
 sock=Path(f'/tmp/.X11-unix/X{n}'); end=time.monotonic()+timeout
 while time.monotonic()<end:
  if p.poll() is not None: raise RuntimeError('Xvfb exited early')
  if sock.exists(): return
  time.sleep(.02)
 raise RuntimeError('Xvfb socket timeout')
def stop_group(p,sig=signal.SIGTERM):
 if p and p.poll() is None:
  try: os.killpg(p.pid,sig)
  except ProcessLookupError: pass

def navigate(d,port,url,policy):
 t0=time.monotonic_ns(); pre=active_info(d)
 if not is_chromium(pre): return {'ready':False,'failure':'browser_not_active','pre_active':pre,'url':url,'policy':policy,'t0_ns':t0}
 chord(d,['Control_L'],'l'); t1=time.monotonic_ns(); checks=[]
 if policy=='FIXED_100MS': time.sleep(.1)
 elif policy=='REOBSERVE_ACTIVE':
  a=active_info(d); checks.append({'phase':'after_ctrl_l','ns':time.monotonic_ns(),'active':a})
  if not is_chromium(a): return {'ready':False,'failure':'lost_active_after_ctrl_l','pre_active':pre,'checks':checks,'url':url,'policy':policy,'t0_ns':t0}
 type_text(d,url); t2=time.monotonic_ns()
 if policy=='FIXED_100MS': time.sleep(.1)
 elif policy=='REOBSERVE_ACTIVE':
  a=active_info(d); checks.append({'phase':'after_text','ns':time.monotonic_ns(),'active':a})
  if not is_chromium(a): return {'ready':False,'failure':'lost_active_after_text','pre_active':pre,'checks':checks,'url':url,'policy':policy,'t0_ns':t0}
 tap(d,'Return'); t3=time.monotonic_ns(); ok,td,tp,samples=wait_url(d,port,url,3); page=devtools_page(port)
 return {'ready':ok,'failure':None if ok else 'readiness_timeout','pre_active':pre,'checks':checks,'url':url,'policy':policy,'t0_ns':t0,'ctrl_l_done_ns':t1,'text_done_ns':t2,'enter_done_ns':t3,'poll_start_ns':tp,'ready_ns':td if ok else None,'elapsed_total_ms':(td-t0)/1e6,'enter_to_ready_ms':(td-t3)/1e6,'poll_samples':samples[-8:],'final_page':page}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--policy',choices=sorted(POLICIES),required=True); ap.add_argument('--load',choices=sorted(LOADS),required=True); ap.add_argument('--phase',choices=sorted(PHASES),required=True); ap.add_argument('--display',type=int,required=True); ap.add_argument('--cpu',type=int,default=0); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
 os.environ['XAUTHORITY']='/dev/null'; os.environ['DISPLAY']=f':{a.display}'
 rec={'case_id':a.case_id,'policy':a.policy,'load':a.load,'phase':a.phase,'display':a.display,'cpu':a.cpu,'started_ns':time.monotonic_ns()}; procs=[]; d=None
 profile=a.out/'profile'; profile.mkdir(); env=dict(os.environ); debug_port=10000+a.display
 try:
  def pop(name,cmd):
   so=open(a.out/f'{name}.stdout','w'); se=open(a.out/f'{name}.stderr','w'); p=subprocess.Popen(cmd,env=env,stdout=so,stderr=se,start_new_session=True,text=True); procs.append((name,p,so,se)); return p
  xv=pop('xvfb',['taskset','-c',str(a.cpu),'Xvfb',f':{a.display}','-screen','0','1024x768x24','-ac','-nolisten','tcp']); wait_socket(a.display,xv)
  ob=pop('openbox',['taskset','-c',str(a.cpu),'openbox'])
  if a.load=='CONTENDED': pop('hog',['taskset','-c',str(a.cpu),sys.executable,'-c','while True: pass'])
  cr=pop('chromium',['taskset','-c',str(a.cpu),'chromium',f'--remote-debugging-port={debug_port}','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disable-default-apps','--disable-extensions','--no-first-run','--no-default-browser-check','--no-proxy-server',f'--user-data-dir={profile}','about:blank'])
  d=display.Display(f':{a.display}'); rec['initial']=wait_browser(d,debug_port)
  if a.phase=='SEQUENTIAL':
   setup=navigate(d,debug_port,'chrome://settings/','FIXED_100MS'); rec['setup']=setup
   if not setup['ready']: raise RuntimeError('common setup navigation failed')
   target='chrome://downloads/'
  else: target='chrome://settings/'
  rec['measurement']=navigate(d,debug_port,target,a.policy); rec['status']='complete_measurement'
 except Exception as e:
  rec['status']='infrastructure_stop'; rec['error']=repr(e); rec['traceback']=traceback.format_exc()
 finally:
  if d:
   try: rec['final_active']=active_info(d); d.close()
   except Exception as e: rec['final_active_error']=repr(e)
  for name,p,so,se in reversed(procs):
   stop_group(p)
   try: p.wait(timeout=3)
   except subprocess.TimeoutExpired: stop_group(p,signal.SIGKILL); p.wait(timeout=2)
   so.close(); se.close(); rec.setdefault('processes',[]).append({'name':name,'pid':p.pid,'returncode':p.returncode})
  rec['ended_ns']=time.monotonic_ns(); atomic_json(a.out/'CASE.json',rec)
 return 0 if rec.get('status')=='complete_measurement' else 2
if __name__=='__main__': raise SystemExit(main())
