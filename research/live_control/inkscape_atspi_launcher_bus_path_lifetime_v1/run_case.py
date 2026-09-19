from __future__ import annotations
import argparse,json,os,re,selectors,shutil,subprocess,sys,time,signal,traceback,uuid
from collections import deque
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT='/org/a11y/atspi/accessible/root'; ACC='org.a11y.atspi.Accessible'; PROP='org.freedesktop.DBus.Properties'
SVG='''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="300" height="200" viewBox="0 0 300 200"><rect id="object-a" inkscape:label="AI_Target_A" x="40" y="60" width="50" height="40" fill="#ff0000"><title>AI_Target_A</title></rect><rect id="object-b" inkscape:label="AI_Target_B" x="180" y="60" width="50" height="40" fill="#0000ff"><title>AI_Target_B</title></rect></svg>'''
def save(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--launcher',action='store_true'); a=ap.parse_args(); root=Path(a.out).resolve(); root.mkdir(parents=True,exist_ok=False)
 deps=Path('/mnt/data/atspi_restore_work/release/inkscape_atspi_direct_observation_v1/deps'); sys.path[:0]=[str(p) for p in sorted(deps.glob('*.whl'))]
 from Xlib import X,XK,display
 from Xlib.ext import xtest
 from native_dbus import Client
 env=os.environ.copy()
 for n in ['home','home/config','home/cache','home/data','runtime']:(root/n).mkdir(parents=True,exist_ok=True,mode=0o700)
 auth=root/'Xauthority';auth.touch();env.update(HOME=str(root/'home'),XDG_CONFIG_HOME=str(root/'home/config'),XDG_CACHE_HOME=str(root/'home/cache'),XDG_DATA_HOME=str(root/'home/data'),XDG_RUNTIME_DIR=str(root/'runtime'),XAUTHORITY=str(auth),NO_AT_BRIDGE='0',GTK_MODULES='gail:atk-bridge',LANG='C.UTF-8')
 procs=[];files=[];clients={};d=None; chroot_root=None
 def spawn(label,argv,pipe=False,custom_env=None):
  f=(root/(label+'.log')).open('w');files.append(f);p=subprocess.Popen(argv,env=custom_env or env,stdout=subprocess.PIPE if pipe else f,stderr=f,text=True,start_new_session=True);procs.append((label,p));return p
 def line(p,timeout=6):
  s=selectors.DefaultSelector();s.register(p.stdout,selectors.EVENT_READ)
  if not s.select(timeout):s.close();raise RuntimeError('startup timeout')
  ans=p.stdout.readline().strip();s.close()
  if not ans:raise RuntimeError('empty startup')
  return ans
 def rpc(dest,path,iface,method,signature=None,vals=()):
  address=env['AT_SPI_BUS_ADDRESS']
  if address not in clients:clients[address]=Client(address)
  return clients[address].call(dest,path,iface,method,signature,vals)
 def key(name):
  kc=d.keysym_to_keycode(XK.string_to_keysym(name));
  for typ in [X.KeyPress,X.KeyRelease]:xtest.fake_input(d,typ,kc);d.sync()
 def chord(names):
  codes=[d.keysym_to_keycode(XK.string_to_keysym(k)) for k in names]
  for kc in codes:xtest.fake_input(d,X.KeyPress,kc);d.sync()
  for kc in reversed(codes):xtest.fake_input(d,X.KeyRelease,kc);d.sync()
 def app_bus_for(pid):
  names=rpc('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames')['response']['data'][0]
  for n in names:
   if n.startswith(':'):
    r=rpc('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID','s',(n,))
    if r['rc']==0 and r['response']['data'][0]==pid:return n
  return None
 def discover(app_bus):
  q=deque([ROOT]);seen=set();found={};start=time.monotonic()
  while q and len(seen)<6000 and time.monotonic()-start<25:
   p=q.popleft()
   if p in seen:continue
   seen.add(p);r=rpc(app_bus,p,PROP,'GetAll','s',(ACC,))
   if r['rc']!=0:continue
   pp=r['response']['data'][0];nm=pp.get('Name',{}).get('data')
   if nm in ('AI_Target_A','AI_Target_B'):found[nm[-1]]=p
   role=rpc(app_bus,p,ACC,'GetRoleName');role_name=role['response']['data'][0] if role['rc']==0 else None
   if role_name in {'menu bar','menu','menu item','check menu item','radio menu item'}:continue
   ch=rpc(app_bus,p,ACC,'GetChildren')
   if ch['rc']==0:
    for bus,cp in ch['response']['data'][0]:
     if bus==app_bus and cp not in seen:q.append(cp)
   if len(found)==2:return found,len(seen)
  return found,len(seen)
 def probe(app_bus,path):
  out={}
  for k,iface,method,sig,vals in [('props',PROP,'GetAll','s',(ACC,)),('role',ACC,'GetRoleName',None,()),('state',ACC,'GetState',None,())]:
   r=rpc(app_bus,path,iface,method,sig,vals);out[k]={'rc':r['rc'],'data':None if r['response'] is None else r['response']['data'],'error':r['error']}
  return out
 result={'task':'INKSCAPE-ATSPI-LAUNCHER-BUS-PATH-LIFETIME-CONSTRUCTION','arm':'launcher_bus' if a.launcher else 'direct_bus','finished':False,'model_calls':0,'game_calls':0,'task_edits':0}
 try:
  env['DISPLAY']=':'+line(spawn('xvfb',['Xvfb','-displayfd','1','-screen','0','1280x800x24','-ac','-nolisten','tcp'],True));os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
  spawn('openbox',['openbox']);time.sleep(.3)
  if not a.launcher:
   env['DBUS_SESSION_BUS_ADDRESS']=line(spawn('session-bus',['dbus-daemon','--session','--nofork','--nopidfile','--print-address=1'],True))
   env['AT_SPI_BUS_ADDRESS']=line(spawn('accessibility-bus',['dbus-daemon','--session','--nofork','--nopidfile','--print-address=1'],True))
   spawn('registry',['/tmp/atspi-022/root/usr/libexec/at-spi2-registryd','--dbus-name','org.a11y.atspi.Registry']);time.sleep(.35)
   result['launcher_session_owner']=False
  else:
   chroot_root=root/'chroot';shutil.copytree(HERE/'chroot_template',chroot_root,symlinks=True)
   tag='ai-'+uuid.uuid4().hex[:12]; sess='unix:abstract='+tag+'-session'
   launcher_session=line(spawn('launcher-session-bus',['dbus-daemon','--session','--nofork','--nopidfile','--address='+sess,'--print-address=1'],True))
   cenv={'PATH':'/usr/bin:/usr/libexec','DBUS_SESSION_BUS_ADDRESS':launcher_session,'XDG_RUNTIME_DIR':'/run'}
   spawn('launcher',['/usr/sbin/chroot',str(chroot_root),'/usr/libexec/at-spi-bus-launcher','--launch-immediately','--a11y=1'],custom_env=cenv)
   get=None
   for _ in range(100):
    q=subprocess.run(['dbus-send','--bus='+launcher_session,'--dest=org.a11y.Bus','--print-reply','--reply-timeout=200','/org/a11y/bus','org.a11y.Bus.GetAddress'],text=True,capture_output=True)
    m=re.search(r'string "(.*)"',q.stdout)
    if q.returncode==0 and m:get=m.group(1);break
    time.sleep(.05)
   if not get:raise RuntimeError('launcher GetAddress unavailable')
   result['launcher_reported_address']=get
   m=re.match(r'unix:path=([^,]+)(,.*)?$',get)
   if not m:raise RuntimeError('unexpected launcher address '+get)
   inside=m.group(1);suffix=m.group(2) or ''
   host_path=str(chroot_root)+inside
   env['AT_SPI_BUS_ADDRESS']='unix:path='+host_path+suffix
   result['launcher_host_mapped_address']=env['AT_SPI_BUS_ADDRESS']
   ok=False
   for _ in range(60):
    q=subprocess.run(['dbus-send','--bus='+env['AT_SPI_BUS_ADDRESS'],'--dest=org.a11y.atspi.Registry','--print-reply','--reply-timeout=500','/org/a11y/atspi/registry','org.a11y.atspi.Registry.GetRegisteredEvents'],env=env,text=True,capture_output=True)
    if q.returncode==0:ok=True;break
    time.sleep(.05)
   if not ok:raise RuntimeError('chroot Registry activation failed '+q.stderr)
   result['launcher_session_owner']=True
   env['DBUS_SESSION_BUS_ADDRESS']=line(spawn('app-session-bus',['dbus-daemon','--session','--nofork','--nopidfile','--print-address=1'],True))
  own=subprocess.run(['dbus-send','--bus='+env['AT_SPI_BUS_ADDRESS'],'--dest=org.freedesktop.DBus','--print-reply','/org/freedesktop/DBus','org.freedesktop.DBus.NameHasOwner','string:org.a11y.atspi.Registry'],env=env,text=True,capture_output=True)
  result['registry_owner']=bool(own.returncode==0 and 'boolean true' in own.stdout)
  if not result['registry_owner']:raise RuntimeError('registry owner missing')
  svg=root/'document.svg';svg.write_text(SVG);app=spawn('inkscape',['inkscape',str(svg)])
  win=None
  for _ in range(80):
   w=subprocess.run(['wmctrl','-lp'],env=env,text=True,capture_output=True,timeout=2)
   for ln in w.stdout.splitlines():
    parts=ln.split(maxsplit=4)
    if len(parts)>=5 and parts[2]==str(app.pid):win=parts[0]
   if win:break
   time.sleep(.1)
  if not win:raise RuntimeError('window unavailable')
  subprocess.run(['wmctrl','-ir',win,'-b','add,maximized_vert,maximized_horz'],env=env,check=True);subprocess.run(['wmctrl','-ia',win],env=env,check=True);time.sleep(1.4)
  d=display.Display(env['DISPLAY']);key('5');time.sleep(.4);chord(['Control_L','Shift_L','l']);time.sleep(.8)
  app_bus=app_bus_for(app.pid)
  result['app_bus_resolution']='pid'
  if not app_bus and a.launcher:
   candidates=[]; diag=[]
   names=rpc('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames')['response']['data'][0]
   for n in names:
    if not n.startswith(':'): continue
    rr=rpc('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID','s',(n,))
    pr=rpc(n,ROOT,PROP,'GetAll','s',(ACC,)); nm=None
    if pr['rc']==0:
     try:nm=pr['response']['data'][0].get('Name',{}).get('data')
     except Exception:pass
    diag.append({'name':n,'pid_rc':rr['rc'],'pid_error':rr.get('error'),'root_name':nm})
    if nm=='org.inkscape.Inkscape': candidates.append(n)
   result['bus_resolution_diag']=diag; result['expected_app_pid']=app.pid
   if len(candidates)==1:
    app_bus=candidates[0]; result['app_bus_resolution']='unique_private_bus_root_name'; result['pid_attribution_available']=False
  if not app_bus:raise RuntimeError('app bus missing')
  first,n1=discover(app_bus)
  if len(first)!=2:raise RuntimeError(f'first labels missing {first} seen={n1}')
  before={k:probe(app_bus,p) for k,p in first.items()};chord(['Control_L','Shift_L','l']);time.sleep(.6);closed={k:probe(app_bus,p) for k,p in first.items()};chord(['Control_L','Shift_L','l']);time.sleep(.8)
  second,n2=discover(app_bus)
  if len(second)!=2:raise RuntimeError(f'second labels missing {second} seen={n2}')
  old_after={k:probe(app_bus,p) for k,p in first.items()};equality={k:first[k]==second[k] for k in ('A','B')};old_names={k:(old_after[k]['props']['data'][0].get('Name',{}).get('data') if old_after[k]['props']['rc']==0 else None) for k in ('A','B')}
  result.update(app_pid=app.pid,app_bus=app_bus,first_paths=first,second_paths=second,path_equal=equality,probe_before=before,probe_closed=closed,probe_old_after_reopen=old_after,old_name_after_reopen=old_names,final_keymap_empty=all(v==0 for v in d.query_keymap()),finished=True)
  save(root/'result.json',result);print(json.dumps(result,sort_keys=True))
 except BaseException as e:
  result['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};save(root/'result.json',result);traceback.print_exc()
 finally:
  if d is not None:
   try:d.close()
   except:pass
  for c in clients.values():c.close()
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
