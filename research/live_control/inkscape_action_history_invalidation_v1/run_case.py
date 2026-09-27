from __future__ import annotations
import argparse,json,os,signal,subprocess,time,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import ImageGrab
from Xlib import X,XK,display as xdisplay
from Xlib.ext import xtest
W,H=1280,800; WAIT_MS=120; RIGHT_PRESSES=5
class XSession:
 def __init__(self,root,display_num):
  self.root=Path(root); self.name=f':{display_num}'; self.auth=self.root/'Xauthority'; self.auth.touch()
  self.env=os.environ.copy(); self.env.update(DISPLAY=self.name,XAUTHORITY=str(self.auth)); self.procs=[]
  self.xvfb=self._p(['Xvfb',self.name,'-screen','0',f'{W}x{H}x24','-ac','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  sock=Path(f'/tmp/.X11-unix/X{display_num}'); self._wait(lambda:sock.exists(),3,'xvfb')
  self.openbox=self._p(['openbox','--config-file','/etc/xdg/openbox/rc.xml'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.25)
  os.environ['DISPLAY']=self.name; os.environ['XAUTHORITY']=str(self.auth); self.d=xdisplay.Display(self.name)
 def _p(self,args,**kw):
  p=subprocess.Popen(args,env=self.env,start_new_session=True,**kw);self.procs.append(p);return p
 def spawn(self,args,**kw):return self._p(args,**kw)
 def _wait(self,fn,timeout,label):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   if fn():return
   time.sleep(.01)
  raise TimeoutError(label)
 def windows(self):return subprocess.run(['wmctrl','-l'],env=self.env,text=True,capture_output=True).stdout
 def wait_window(self,needle,timeout=10):self._wait(lambda:needle in self.windows(),timeout,'window')
 def focus(self,needle):
  for line in self.windows().splitlines():
   if needle in line:
    subprocess.run(['wmctrl','-ia',line.split()[0]],env=self.env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.08);return
  raise RuntimeError('window not found')
 def close(self):
  try:self.d.close()
  except Exception:pass
  for p in reversed(self.procs):
   try:os.killpg(p.pid,signal.SIGTERM)
   except Exception:pass
  time.sleep(.08)
  for p in reversed(self.procs):
   try:
    if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
   except Exception:pass

def kc(d,n):return d.keysym_to_keycode(XK.string_to_keysym(n))
def raw(d,n,down):xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc(d,n));d.sync()
def key(d,n):raw(d,n,1);raw(d,n,0)
def chord(d,m,n):raw(d,m,1);raw(d,n,1);raw(d,n,0);raw(d,m,0)
def capture(p): im=ImageGrab.grab();im.save(p);return im.convert('RGB')
def red_components(im):
 xcounts={};ysby={}
 for y in range(180,700):
  for x in range(40,1100):
   r,g,b=im.getpixel((x,y))
   if r>=240 and g<=20 and b<=20:xcounts[x]=xcounts.get(x,0)+1;ysby.setdefault(x,[]).append(y)
 xs=sorted(x for x,c in xcounts.items() if c>=8);runs=[]
 if xs:
  s=pr=xs[0]
  for x in xs[1:]:
   if x>pr+2:runs.append((s,pr));s=x
   pr=x
  runs.append((s,pr))
 comps=[]
 for a,b in runs:
  pts=[(x,y) for x in range(a,b+1) for y in ysby.get(x,[])]
  if len(pts)<200:continue
  xx=[p[0] for p in pts];yy=[p[1] for p in pts];comps.append([min(xx),min(yy),max(xx)+1,max(yy)+1,len(pts)])
 return sorted(comps,key=lambda c:c[0])[:2]
def center(b):return ((b[0]+b[2]-1)/2,(b[1]+b[3]-1)/2)
def handle_counts(im,a0):
 l,t,r,b=map(int,a0[:4]);ex=20
 def dark(box):
  x0,y0,x1,y1=box
  return sum(1 for y in range(max(0,y0),min(im.height,y1)) for x in range(max(0,x0),min(im.width,x1)) if max(im.getpixel((x,y)))<=60)
 return {'top':dark((l,t-ex,r,t)),'right':dark((r,t-ex,r+ex,b+ex)),'bottom':dark((l,b,r,b+ex))}
def handles_selected(c):return c['top']>=30 and c['right']>=80 and c['bottom']>=30
def select_score(im,a0,b0):
 cs=red_components(im)
 if len(cs)!=2:return {'success':False,'reason':'components','components':cs}
 a,b=cs;ac=center(a);bc=center(b);aa=center(a0);bb=center(b0)
 center_ok=abs(ac[0]-aa[0])<=5 and abs(ac[1]-aa[1])<=5 and abs(bc[0]-bb[0])<=5 and abs(bc[1]-bb[1])<=5
 counts=handle_counts(im,a0);selected=handles_selected(counts)
 return {'success':bool(center_ok and selected),'center_ok':center_ok,'selection_handles':selected,'handle_dark_pixels':counts,'components':cs}
def guard_selection_A(a0,out_path):
 l,t,r,b=map(int,a0[:4]);box=[l,t-20,r+20,b+20]
 ts=time.perf_counter_ns();roi=ImageGrab.grab(bbox=tuple(box)).convert('RGB');dt=time.perf_counter_ns()-ts; roi.save(out_path)
 w,h=roi.size; obj_w=r-l; obj_h=b-t
 def dark(x0,y0,x1,y1):
  return sum(1 for y in range(max(0,y0),min(h,y1)) for x in range(max(0,x0),min(w,x1)) if max(roi.getpixel((x,y)))<=60)
 counts={'top':dark(0,0,obj_w,20),'right':dark(obj_w,0,obj_w+20,obj_h+40),'bottom':dark(0,obj_h+20,obj_w,obj_h+40)}
 selected=handles_selected(counts)
 return {'available':True,'selection_A':selected,'dark_pixels':counts,'box':box,'capture_ns':dt,'pixels':w*h,'rgb_sha256':hashlib.sha256(roi.tobytes()).hexdigest()}
def parse_svg(p):
 root=ET.parse(p).getroot();ns='{http://www.w3.org/2000/svg}';out={}
 for r in root.findall('.//'+ns+'rect'):
  if r.attrib.get('id') in ('A','B'):out[r.attrib['id']]={'x':float(r.attrib['x']),'y':float(r.attrib['y'])}
 return out
def key_down(d,code):q=d.query_keymap();return bool(q[code//8]&(1<<(code%8)))
def run(out,context,policy,display_num):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);svg=out/'fixture.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200">\n<rect id="A" x="50" y="60" width="60" height="40" fill="#ff0000"/>\n<rect id="B" x="220" y="60" width="60" height="40" fill="#ff0000"/>\n</svg>\n')
 s=XSession(out,display_num);rec={'context':context,'policy':policy,'display':s.name,'wait_ms':WAIT_MS,'right_presses':RIGHT_PRESSES,'timestamps':{},'action_receipts':[]}
 try:
  p=s.spawn(['inkscape',str(svg)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);rec['pid']=p.pid;s.wait_window('fixture.svg');s.focus('fixture.svg');time.sleep(.8)
  im0=capture(out/'initial.png');cs=red_components(im0)
  if len(cs)!=2:raise RuntimeError(f'initial {cs}')
  A,B=cs;rec['initial_components']=cs;rec['initial_svg']=parse_svg(svg)
  key(s.d,'F1');time.sleep(.05);key(s.d,'Escape');time.sleep(.02);key(s.d,'Tab')
  rec['setup_selection_samples']=[]; im1=None
  for attempt in range(10):
   time.sleep(.05); pth=out/f'setup_select_{attempt:02d}.png'; imx=capture(pth); sc=select_score(imx,A,B); rec['setup_selection_samples'].append({'attempt':attempt,'score':sc})
   if sc['success']:im1=imx;break
  if im1 is None:raise RuntimeError('A selection not visibly established')
  rec['timestamps']['revalidate_start_ns']=time.monotonic_ns();im1=capture(out/'revalidated.png');rec['timestamps']['revalidate_end_ns']=time.monotonic_ns();rec['revalidation']=select_score(im1,A,B)
  if not rec['revalidation']['success']:raise RuntimeError('revalidation failed')
  phase=rec['timestamps']['revalidate_end_ns']; rec['timestamps']['phase_start_ns']=phase
  if context=='self_switch':
   t0=time.monotonic_ns();key(s.d,'Tab');t1=time.monotonic_ns();rec['action_receipts'].append({'kind':'selection_navigation','key':'Tab','start_ns':t0,'end_ns':t1})
  deadline=phase+WAIT_MS*1_000_000
  while time.monotonic_ns()<deadline:time.sleep(.001)
  rec['timestamps']['guard_start_ns']=time.monotonic_ns();rec['guard']=guard_selection_A(A,out/'guard_roi.png');rec['timestamps']['guard_end_ns']=time.monotonic_ns()
  relevant=[r for r in rec['action_receipts'] if r['kind']=='selection_navigation' and r['end_ns']>rec['timestamps']['revalidate_end_ns']]
  if not rec['guard']['available'] or not rec['guard']['selection_A']:
   rec['decision']='DEPENDENCY_UNAVAILABLE';rec['effect_input_sent']=False
  elif policy=='history_invalidate' and relevant:
   rec['decision']='STOP_HISTORY_INVALIDATED';rec['effect_input_sent']=False
  else:
   rec['decision']='ADMIT';rec['effect_input_sent']=True
  rec['relevant_history_count']=len(relevant)
  if rec['effect_input_sent']:
   rec['timestamps']['effect_input_start_ns']=time.monotonic_ns()
   for _ in range(RIGHT_PRESSES):key(s.d,'Right')
   rec['timestamps']['effect_input_end_ns']=time.monotonic_ns()
  chord(s.d,'Control_L','s');time.sleep(.25);rec['final_svg']=parse_svg(svg);rec['timestamps']['score_ns']=time.monotonic_ns()
  rec['keys_down']={n:key_down(s.d,kc(s.d,n)) for n in ['Right','Control_L','s','F1','Tab']};rec['pointer_mask']=int(s.d.screen().root.query_pointer().mask);rec['delta']={k:rec['final_svg'][k]['x']-rec['initial_svg'][k]['x'] for k in ('A','B')};rec['all_relevant_keys_empty']=not any(rec['keys_down'].values());rec['button_empty']=(rec['pointer_mask']&0x1f00)==0
  if context=='stable':rec['semantic_correct']=(rec['effect_input_sent'] and rec['delta']['A']>.5 and abs(rec['delta']['B'])<.5)
  else:
   if policy=='history_invalidate':rec['semantic_correct']=(not rec['effect_input_sent'] and rec['decision']=='STOP_HISTORY_INVALIDATED' and abs(rec['delta']['A'])<.5 and abs(rec['delta']['B'])<.5)
   else:rec['semantic_correct']=False
   rec['wrong_target_effect']=(policy=='current_guard_only' and rec['effect_input_sent'] and abs(rec['delta']['A'])<.5 and rec['delta']['B']>.5)
  (out/'result.json').write_text(json.dumps(rec,indent=2,sort_keys=True));return rec
 finally:s.close()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--context',choices=['stable','self_switch'],required=True);ap.add_argument('--policy',choices=['current_guard_only','history_invalidate'],required=True);ap.add_argument('--display',type=int,required=True);a=ap.parse_args();print(json.dumps(run(a.out,a.context,a.policy,a.display),sort_keys=True))
