from __future__ import annotations
import argparse,json,os,re,selectors,shutil,subprocess,sys,time,signal,traceback,uuid
from collections import deque
from pathlib import Path
HERE=Path(__file__).resolve().parent
TEMPLATE=Path('/mnt/data/atspi_launcher_path_lifetime_lab/chroot_template')
ROOT='/org/a11y/atspi/accessible/root'; ACC='org.a11y.atspi.Accessible'; PROP='org.freedesktop.DBus.Properties'
SVG='''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="300" height="200" viewBox="0 0 300 200"><rect id="object-a" inkscape:label="AI_Target_A" x="40" y="60" width="50" height="40" fill="#ff0000"><title>AI_Target_A</title></rect><rect id="object-b" inkscape:label="AI_Target_B" x="180" y="60" width="50" height="40" fill="#0000ff"><title>AI_Target_B</title></rect></svg>'''
def save(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--selection-transition',action='store_true');a=ap.parse_args();root=Path(a.out).resolve();root.mkdir(parents=True,exist_ok=False)
 deps=Path('/mnt/data/atspi_restore_work/release/inkscape_atspi_direct_observation_v1/deps');sys.path[:0]=[str(p) for p in sorted(deps.glob('*.whl'))]
 from Xlib import X,XK,display
 from Xlib.ext import xtest
 from PIL import ImageGrab
 import numpy as np
 from native_dbus import Client
 env=os.environ.copy()
 for n in ['home','home/config','home/cache','home/data','runtime']:(root/n).mkdir(parents=True,exist_ok=True,mode=0o700)
 auth=root/'Xauthority';auth.touch();env.update(HOME=str(root/'home'),XDG_CONFIG_HOME=str(root/'home/config'),XDG_CACHE_HOME=str(root/'home/cache'),XDG_DATA_HOME=str(root/'home/data'),XDG_RUNTIME_DIR=str(root/'runtime'),XAUTHORITY=str(auth),NO_AT_BRIDGE='0',GTK_MODULES='gail:atk-bridge',LANG='C.UTF-8')
 procs=[];files=[];clients={};d=None
 def spawn(label,argv,pipe=False,custom_env=None):
  f=(root/(label+'.log')).open('w');files.append(f);p=subprocess.Popen(argv,env=custom_env or env,stdout=subprocess.PIPE if pipe else f,stderr=f,text=True,start_new_session=True);procs.append((label,p));return p
 def line(p,timeout=8):
  s=selectors.DefaultSelector();s.register(p.stdout,selectors.EVENT_READ)
  if not s.select(timeout):s.close();raise RuntimeError('startup timeout')
  ans=p.stdout.readline().strip();s.close()
  if not ans:raise RuntimeError('empty startup')
  return ans
 def rpc(address,dest,path,iface,method,signature=None,vals=()):
  if address not in clients:clients[address]=Client(address)
  return clients[address].call(dest,path,iface,method,signature,vals)
 def key(name):
  kc=d.keysym_to_keycode(XK.string_to_keysym(name))
  for typ in [X.KeyPress,X.KeyRelease]:xtest.fake_input(d,typ,kc);d.sync()
 def chord(names):
  codes=[d.keysym_to_keycode(XK.string_to_keysym(k)) for k in names]
  for kc in codes:xtest.fake_input(d,X.KeyPress,kc);d.sync()
  for kc in reversed(codes):xtest.fake_input(d,X.KeyRelease,kc);d.sync()
 def click(x,y):
  xtest.fake_input(d,X.MotionNotify,x=x,y=y);d.sync()
  xtest.fake_input(d,X.ButtonPress,1);d.sync();xtest.fake_input(d,X.ButtonRelease,1);d.sync()
 def capture(name):
  im=ImageGrab.grab(xdisplay=env['DISPLAY']).convert('RGB');im.save(root/name);return im
 def boxes(im):
  aa=np.asarray(im);area=np.zeros(aa.shape[:2],bool);area[150:730,20:1000]=True;out={}
  for tg,ch in [('A',0),('B',2)]:
   o=[c for c in range(3) if c!=ch];m=(aa[:,:,ch]>=240)&(aa[:,:,o[0]]<=20)&(aa[:,:,o[1]]<=20)&area;ys,xs=np.nonzero(m)
   if len(xs)<500:raise RuntimeError('target pixels unavailable '+tg)
   xc=np.bincount(xs,minlength=aa.shape[1]);yc=np.bincount(ys,minlength=aa.shape[0]);xx=np.flatnonzero(xc>=max(20,xc.max()*.7));yy=np.flatnonzero(yc>=max(20,yc.max()*.7));out[tg]=[int(xx[0]),int(yy[0]),int(xx[-1]+1),int(yy[-1]+1)]
  return out
 def handles(im,box):
  l,t,r,b=box;zs={'top':(l,t-18,r,t),'right':(r,t,r+18,b),'bottom':(l,b,r,b+18),'left':(l-18,t,l,b)};o={}
  for k,(x0,y0,x1,y1) in zs.items():
   c=0
   for yy in range(max(0,y0),min(im.height,y1)):
    for xx in range(max(0,x0),min(im.width,x1)):
     if max(im.getpixel((xx,yy)))<=60:c+=1
   o[k]=c
  return o
 def discover(address,app_bus):
  q=deque([ROOT]);seen=set();found={};start=time.monotonic()
  while q and len(seen)<7000 and time.monotonic()-start<28:
   p=q.popleft()
   if p in seen:continue
   seen.add(p);r=rpc(address,app_bus,p,PROP,'GetAll','s',(ACC,))
   if r['rc']!=0:continue
   pp=r['response']['data'][0];nm=pp.get('Name',{}).get('data')
   if nm in ('AI_Target_A','AI_Target_B'):found[nm[-1]]=p
   role=rpc(address,app_bus,p,ACC,'GetRoleName');role_name=role['response']['data'][0] if role['rc']==0 else None
   if role_name in {'menu bar','menu','menu item','check menu item','radio menu item'}:continue
   ch=rpc(address,app_bus,p,ACC,'GetChildren')
   if ch['rc']==0:
    for bus,cp in ch['response']['data'][0]:
     if bus==app_bus and cp not in seen:q.append(cp)
   if len(found)==2:return found,len(seen)
  return found,len(seen)
 def probe(address,app_bus,path):
  out={}
  for k,iface,method,sig,vals in [('props',PROP,'GetAll','s',(ACC,)),('role',ACC,'GetRoleName',None,()),('state',ACC,'GetState',None,())]:
   r=rpc(address,app_bus,path,iface,method,sig,vals);out[k]={'rc':r['rc'],'data':None if r['response'] is None else r['response']['data'],'error':r['error']}
  return out
 def resolve_unique_app(address):
  names=rpc(address,'org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames')['response']['data'][0];c=[];diag=[]
  for n in names:
   if not n.startswith(':'):continue
   pr=rpc(address,n,ROOT,PROP,'GetAll','s',(ACC,));nm=None
   if pr['rc']==0:
    try:nm=pr['response']['data'][0].get('Name',{}).get('data')
    except Exception:pass
   diag.append({'name':n,'root_name':nm})
   if nm=='org.inkscape.Inkscape':c.append(n)
  return (c[0] if len(c)==1 else None),diag
 result={'task':'INKSCAPE-ATSPI-SELECTION-TRANSITION-PATH-LIFETIME-20260917-031','arm':'selection_transition' if a.selection_transition else 'matched_no_transition','finished':False,'model_calls':0,'game_calls':0,'task_edits':0}
 try:
  env['DISPLAY']=':'+line(spawn('xvfb',['Xvfb','-displayfd','1','-screen','0','1280x800x24','-ac','-nolisten','tcp'],True));os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY'];spawn('openbox',['openbox']);time.sleep(.3)
  cr=root/'chroot';shutil.copytree(TEMPLATE,cr,symlinks=True)
  tag='ai-'+uuid.uuid4().hex[:12];sess='unix:abstract='+tag+'-session';a11y_expected='unix:abstract='+tag+'-a11y'
  for conf in [cr/'etc/at-spi2/accessibility.conf',cr/'usr/share/defaults/at-spi2/accessibility.conf']:
   if conf.exists():
    txt=conf.read_text();txt=re.sub(r'<listen>.*?</listen>',f'<listen>{a11y_expected}</listen>',txt);conf.write_text(txt)
  launcher_session=line(spawn('session-bus',['dbus-daemon','--session','--nofork','--nopidfile','--address='+sess,'--print-address=1'],True))
  long_runtime='/run/'+('r'*88);(cr/long_runtime.lstrip('/')).mkdir(parents=True,exist_ok=True,mode=0o700)
  cenv={'PATH':'/usr/bin:/usr/libexec','DBUS_SESSION_BUS_ADDRESS':launcher_session,'XDG_RUNTIME_DIR':long_runtime}
  spawn('launcher',['/usr/sbin/chroot',str(cr),'/usr/libexec/at-spi-bus-launcher','--launch-immediately','--a11y=1'],custom_env=cenv)
  a11y=None
  for _ in range(120):
   q=subprocess.run(['dbus-send','--bus='+launcher_session,'--dest=org.a11y.Bus','--print-reply','--reply-timeout=200','/org/a11y/bus','org.a11y.Bus.GetAddress'],text=True,capture_output=True)
   m=re.search(r'string "(.*)"',q.stdout)
   if q.returncode==0 and m:a11y=m.group(1);break
   time.sleep(.05)
  if not a11y:raise RuntimeError('launcher GetAddress unavailable')
  result['reported_address']=a11y;result['address_matches_case_prefix']=(a11y.split(',guid=')[0]==a11y_expected)
  if not result['address_matches_case_prefix']:raise RuntimeError('launcher address mismatch')
  ok=False
  for _ in range(80):
   q=subprocess.run(['dbus-send','--bus='+a11y,'--dest=org.a11y.atspi.Registry','--print-reply','--reply-timeout=500','/org/a11y/atspi/registry','org.a11y.atspi.Registry.GetRegisteredEvents'],text=True,capture_output=True)
   if q.returncode==0:ok=True;break
   time.sleep(.05)
  if not ok:raise RuntimeError('Registry activation failed')
  result['listeners']=[]
  for j,event in enumerate(['object:state-changed','object:selection-changed']):
   lp=spawn(f'listener-{j}',[sys.executable,str(HERE/'register_listener.py'),a11y,'40',event],True,env);obj=json.loads(line(lp,5));result['listeners'].append(obj)
   if not obj.get('registered'):raise RuntimeError('listener registration failed '+repr(obj))
  result['listener_registration_count']=len(result['listeners'])
  env['DBUS_SESSION_BUS_ADDRESS']=launcher_session;env.pop('AT_SPI_BUS_ADDRESS',None)
  result['app_env_has_at_spi_bus_address']=False
  svg=root/'document.svg';svg.write_text(SVG);app=spawn('inkscape',['inkscape',str(svg)])
  win=None
  for _ in range(100):
   w=subprocess.run(['wmctrl','-lp'],env=env,text=True,capture_output=True,timeout=2)
   for ln in w.stdout.splitlines():
    parts=ln.split(maxsplit=4)
    if len(parts)>=5 and parts[2]==str(app.pid):win=parts[0]
   if win:break
   time.sleep(.1)
  if not win:raise RuntimeError('window unavailable')
  subprocess.run(['wmctrl','-ir',win,'-b','add,maximized_vert,maximized_horz'],env=env,check=True);subprocess.run(['wmctrl','-ia',win],env=env,check=True);time.sleep(1.5)
  d=display.Display(env['DISPLAY']);key('5');time.sleep(.4);chord(['Control_L','Shift_L','l']);time.sleep(.9);key('F1');key('Escape');time.sleep(.25)
  # independent witness that app-side session discovery points to same accessibility bus
  q=subprocess.run(['dbus-send','--bus='+launcher_session,'--dest=org.a11y.Bus','--print-reply','--reply-timeout=500','/org/a11y/bus','org.a11y.Bus.GetAddress'],env=env,text=True,capture_output=True);m=re.search(r'string "(.*)"',q.stdout);result['session_getaddress_match']=bool(m and m.group(1)==a11y)
  app_bus,diag=resolve_unique_app(a11y);result['bus_resolution_diag']=diag;result['app_bus_resolution']='unique_private_bus_root_name';result['pid_attribution_available']=False
  if not app_bus:raise RuntimeError('unique Inkscape accessible root missing')
  im0=capture('initial.png');bb=boxes(im0);result['boxes']=bb
  first,n1=discover(a11y,app_bus);result['first_discovery_seen']=n1
  if len(first)!=2:raise RuntimeError('first labels missing '+repr(first))
  result['first_paths']=first;result['probe_initial']={k:probe(a11y,app_bus,p) for k,p in first.items()}
  # choose an empty white canvas point below targets, and verify it is visually white-ish
  ex=(bb['A'][2]+bb['B'][0])//2;ey=min(im0.height-80,max(bb['A'][3],bb['B'][3])+100);pix=im0.getpixel((ex,ey));result['empty_point']=[ex,ey];result['empty_pixel']=list(pix)
  if min(pix)<180: raise RuntimeError('empty control point not white '+repr(pix))
  phases=[]
  seq=['A','B','none'] if a.selection_transition else ['empty','empty','none']
  expected=['A','B','none'] if a.selection_transition else ['none','none','none']
  for idx,(op,exp) in enumerate(zip(seq,expected),1):
   if op in ('A','B'):
    l,t,r,b=bb[op];click((l+r)//2,(t+b)//2)
   elif op=='empty': click(ex,ey)
   else:key('Escape')
   time.sleep(.55);im=capture(f'phase-{idx}.png');hc={k:handles(im,v) for k,v in bb.items()};selected=[k for k,v in hc.items() if min(v.values())>=40]
   if exp=='none' and selected:raise RuntimeError(f'phase {idx} expected none got {selected}')
   if exp!='none' and selected!=[exp]:raise RuntimeError(f'phase {idx} expected {exp} got {selected}')
   phases.append({'index':idx,'operation':op,'expected':exp,'visual_selected':selected,'handles':hc,'probes':{k:probe(a11y,app_bus,p) for k,p in first.items()}})
  second,n2=discover(a11y,app_bus);result['second_discovery_seen']=n2
  if len(second)!=2:raise RuntimeError('second labels missing '+repr(second))
  result['second_paths']=second;result['path_equal']={k:first[k]==second[k] for k in ('A','B')};result['phases']=phases;result['probe_old_final']={k:probe(a11y,app_bus,p) for k,p in first.items()};result['final_keymap_empty']=all(v==0 for v in d.query_keymap());result['finished']=True
  save(root/'result.json',result);print(json.dumps(result,sort_keys=True))
 except BaseException as e:
  result['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};save(root/'result.json',result);traceback.print_exc()
 finally:
  if d is not None:
   try:d.close()
   except:pass
  for c in clients.values():
   try:c.close()
   except:pass
  for label,p in reversed(procs):
   try:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
   except:pass
  time.sleep(.1)
  for label,p in reversed(procs):
   try:
    if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
   except:pass
  for f in files:f.close()
 return 0 if result.get('finished') else 1
if __name__=='__main__':raise SystemExit(main())
