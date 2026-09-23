import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
from openpyxl import Workbook

SCHEMA='agent-interface/motor-state-calc-effect-rung-v1'
SCENARIOS=('stable','focus_transferred','observer_unavailable')
POLICIES=('naive_command','observed_guard')

def descendants(root):
 out=[]; stack=[root]
 while stack:
  w=stack.pop()
  try: cs=w.query_tree().children
  except Exception: cs=[]
  out.extend(cs); stack.extend(cs)
 return out

def win_name(w):
 try:return str(w.get_wm_name() or '')
 except Exception:return ''

def find_window(d,needles,timeout=10):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  for w in descendants(d.screen().root):
   n=win_name(w).lower()
   try:c=' '.join(w.get_wm_class() or ()).lower()
   except Exception:c=''
   if any(x in n or x in c for x in needles):
    try:
     if w.get_attributes().map_state==X.IsViewable:return w
    except Exception:pass
  time.sleep(.05)
 raise RuntimeError('WINDOW_NOT_FOUND:'+','.join(needles))

def start_xvfb(n,root):
 xa=root/'empty.Xauthority'; xa.write_bytes(b'')
 env=os.environ.copy(); env['DISPLAY']=f':{n}'; env['XAUTHORITY']=str(xa); os.environ['XAUTHORITY']=str(xa)
 p=subprocess.Popen(['Xvfb',f':{n}','-ac','-screen','0','1280x800x24','-nolisten','tcp'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True)
 for _ in range(160):
  if p.poll() is not None: raise RuntimeError('XVFB_EXIT')
  try:
   d=display.Display(env['DISPLAY']); d.close(); return p,env
  except Exception: time.sleep(.025)
 raise RuntimeError('XVFB_NOT_READY')

def stop(p):
 if not p:return None
 try: os.killpg(p.pid,signal.SIGTERM); return p.wait(timeout=2)
 except Exception:
  try: os.killpg(p.pid,signal.SIGKILL); return p.wait(timeout=1)
  except Exception:return None

def center(w):
 g=w.get_geometry(); t=w.translate_coords(w.query_tree().root,0,0)
 return int(t.x+max(20,g.width//2)),int(t.y+max(20,g.height//2))

def motion(d,x,y):xtest.fake_input(d,X.MotionNotify,x=x,y=y); d.sync()
def button(d,down):xtest.fake_input(d,X.ButtonPress if down else X.ButtonRelease,1); d.sync()
def click(d,w):
 x,y=center(w); motion(d,x,y); button(d,True); button(d,False); time.sleep(.12)

def keycode(d,name):
 k=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not k: raise RuntimeError('NO_KEY:'+name)
 return k

def key(d,name,mods=()):
 ms=[keycode(d,m) for m in mods]
 for m in ms:xtest.fake_input(d,X.KeyPress,m)
 k=keycode(d,name); xtest.fake_input(d,X.KeyPress,k); xtest.fake_input(d,X.KeyRelease,k)
 for m in reversed(ms):xtest.fake_input(d,X.KeyRelease,m)
 d.sync(); time.sleep(.06)

def focus_id(d):
 f=d.get_input_focus().focus; return int(getattr(f,'id',0) or 0)

def keydown(d,k):
 raw=d.query_keymap(); return bool(raw[k//8]&(1<<(k%8)))

def helper_source():
 return """import tkinter as tk,sys
from pathlib import Path
out=Path(sys.argv[1]); r=tk.Tk(); r.title('MotorStateHelper'); e=tk.Entry(r,width=30); e.pack(padx=20,pady=20)
def dump(ev=None): out.write_text(e.get())
e.bind('<KeyRelease>',dump)
r.after(300,lambda:(r.focus_force(),e.focus_force()))
r.mainloop()
"""

def uno_read(port,script):
 p=subprocess.run(['/usr/bin/python3',str(script),str(port)],capture_output=True,text=True,timeout=4)
 if p.returncode: raise RuntimeError('UNO_READ:'+p.stderr.strip())
 return json.loads(p.stdout)

def run_case(scenario,policy,rep,display_num,outroot,uno_script):
 cid=f'{scenario}-{policy}-r{rep}'; root=outroot/cid; root.mkdir(parents=True)
 xv=calc=helper=None; controller=observer=scorer=None
 r={'schema':SCHEMA,'case_id':cid,'scenario':scenario,'policy':policy,'rep':rep,'authority':'none'}
 try:
  xv,env=start_xvfb(display_num,root)
  book=root/'book.xlsx'; wb=Workbook(); wb.active['A1']=''; wb.save(book)
  profile=(root/'lo-profile').resolve(); profile.mkdir(); port=22000+(display_num%1000)
  calc=subprocess.Popen(['libreoffice',f'--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ServiceManager',f'-env:UserInstallation=file://{profile}','--calc','--norestore','--nolockcheck','--nofirststartwizard',str(book)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True)
  controller=display.Display(env['DISPLAY']); observer=display.Display(env['DISPLAY']); scorer=display.Display(env['DISPLAY'])
  cw=find_window(controller,['libreoffice calc','calc']); click(controller,cw); key(controller,'Home',mods=('Control_L',)); time.sleep(.1)
  r['commanded_focus']=focus_id(scorer)
  sh=keycode(controller,'Shift_L'); xtest.fake_input(controller,X.KeyPress,sh); controller.sync(); time.sleep(.03); r['held_observed']=keydown(scorer,sh)
  xtest.fake_input(controller,X.KeyRelease,sh); controller.sync(); time.sleep(.03); r['release_observed']=not keydown(scorer,sh)
  helper_file=root/'helper.txt'
  if scenario=='focus_transferred':
   hp=root/'helper.py'; hp.write_text(helper_source())
   helper=subprocess.Popen([sys.executable,str(hp),str(helper_file)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True)
   hw=find_window(controller,['motorstatehelper']); time.sleep(.45); click(controller,hw); time.sleep(.1)
  if scenario=='observer_unavailable': observer.close(); observer=None
  if policy=='observed_guard':
   try:
    obs=focus_id(observer); r['observed_focus']=obs; r['decision']='ACT' if obs==r['commanded_focus'] else 'REFUSE_MISMATCH'
   except Exception as e:
    r['observer_error']=type(e).__name__; r['decision']='REFUSE_UNKNOWN'
  else:r['decision']='ACT'
  r['pre_action_focus']=focus_id(scorer)
  if r['decision']=='ACT': key(controller,'7'); key(controller,'Return'); r['task_input_dispatched']=True
  else:r['task_input_dispatched']=False
  time.sleep(.15); r['post_action_focus']=focus_id(scorer)
  r['app_effect']=uno_read(port,uno_script); r['helper_effect']=helper_file.read_text() if helper_file.exists() else ''
  r['neutral_final']=not keydown(scorer,sh); r['status']='ok'
 except Exception as e:
  r['status']='error'; r['error']=f'{type(e).__name__}: {e}'
 finally:
  for d in (observer,scorer,controller):
   try:
    if d:d.close()
   except Exception:pass
  r['helper_exit']=stop(helper); r['calc_exit']=stop(calc); r['xvfb_exit']=stop(xv)
 return r

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--rep',type=int,required=True); ap.add_argument('--out',required=True); ap.add_argument('--display-base',type=int,required=True); a=ap.parse_args()
 out=Path(a.out)
 if out.exists(): raise SystemExit('output exists')
 out.mkdir(parents=True); uno=Path(__file__).with_name('uno_read.py')
 rows=[]; i=0
 for s in SCENARIOS:
  for p in POLICIES:
   rows.append(run_case(s,p,a.rep,a.display_base+i,out,uno)); i+=1
 raw={'schema':SCHEMA,'rep':a.rep,'rows':rows}; (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n')
 ok=all(x.get('status')=='ok' and x.get('held_observed') and x.get('release_observed') and x.get('neutral_final') for x in rows)
 print(json.dumps({'rows':len(rows),'integrity':ok,'statuses':[x.get('status') for x in rows]},sort_keys=True)); return 0 if ok else 2
if __name__=='__main__':raise SystemExit(main())
