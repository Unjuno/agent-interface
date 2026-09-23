#!/usr/bin/env python3
import argparse,hashlib,json,os,re,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
from Xlib import X,XK,display as xdisplay
from Xlib.ext import xtest
HERE=Path(__file__).resolve().parent
PKG=Path('/tmp/atspi-022/root')
SVG='<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200"><rect id="A" x="50" y="50" width="40" height="30" fill="red"/><rect id="B" x="220" y="50" width="40" height="30" fill="blue"/></svg>\n'
def shab(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def call(args,env=None,**kw): return subprocess.run(args,env=env,text=True,capture_output=True,**kw)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--display',type=int,required=True);a=ap.parse_args()
 root=Path(a.out);root.mkdir(parents=True,exist_ok=False); procs=[]; oldcfg=None; cfg=Path('/etc/at-spi2/accessibility.conf');service=root/'services';service.mkdir();runtime=root/'runtime';runtime.mkdir();os.chmod(runtime,0o700);auth=root/'Xauthority';auth.touch()
 def spawn(name,args,env):
  f1=open(root/(name+'.out'),'wb');f2=open(root/(name+'.err'),'wb');p=subprocess.Popen(args,env=env,stdout=f1,stderr=f2,start_new_session=True);procs.append((p,f1,f2));return p
 try:
  if cfg.exists(): oldcfg=cfg.read_bytes()
  cfg.parent.mkdir(parents=True,exist_ok=True)
  default=(PKG/'usr/share/defaults/at-spi2/accessibility.conf').read_text();cfg.write_text(re.sub(r'<servicedir>.*?</servicedir>',f'<servicedir>{service}</servicedir>',default))
  (service/'org.a11y.atspi.Registry.service').write_text('[D-BUS Service]\nName=org.a11y.atspi.Registry\nExec='+str(PKG/'usr/libexec/at-spi2-registryd')+'\n')
  env=os.environ.copy();env.update({'DISPLAY':f':{a.display}','XAUTHORITY':str(auth),'XDG_RUNTIME_DIR':str(runtime),'NO_AT_BRIDGE':'0'});env.pop('AT_SPI_BUS_ADDRESS',None);os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
  xv=spawn('xvfb',['Xvfb',f':{a.display}','-screen','0','1280x800x24','-ac','-nolisten','tcp'],env)
  for _ in range(100):
   if Path(f'/tmp/.X11-unix/X{a.display}').exists(): break
   time.sleep(.02)
  spawn('openbox',['openbox','--config-file','/etc/xdg/openbox/rc.xml'],env);time.sleep(.25)
  sb=call(['dbus-daemon','--session','--fork','--print-address=1','--print-pid=1'],env=env,check=True).stdout.splitlines();env['DBUS_SESSION_BUS_ADDRESS']=sb[0];sesspid=int(sb[1])
  launch=spawn('launcher',[str(PKG/'usr/libexec/at-spi-bus-launcher'),'--launch-immediately','--a11y=1'],env)
  addr=''
  for _ in range(100):
   q=call(['dbus-send','--session','--dest=org.a11y.Bus','--print-reply','--reply-timeout=150','/org/a11y/bus','org.a11y.Bus.GetAddress'],env=env)
   m=re.search(r'string "(.*)"',q.stdout)
   if q.returncode==0 and m: addr=m.group(1);break
   time.sleep(.03)
  if not addr: raise RuntimeError('org.a11y.Bus unavailable')
  sbown=call(['dbus-send','--session','--dest=org.freedesktop.DBus','--print-reply','--reply-timeout=1000','/org/freedesktop/DBus','org.freedesktop.DBus.NameHasOwner','string:org.a11y.Bus'],env=env); session_bus_owner=('boolean true' in sbown.stdout)
  # activate official Registry
  q=call(['dbus-send','--bus='+addr,'--dest=org.a11y.atspi.Registry','--print-reply','--reply-timeout=2000','/org/a11y/atspi/registry','org.a11y.atspi.Registry.GetRegisteredEvents'],env=env)
  if q.returncode: raise RuntimeError('Registry activation failed '+q.stderr)
  rgown=call(['dbus-send','--bus='+addr,'--dest=org.freedesktop.DBus','--print-reply','--reply-timeout=1000','/org/freedesktop/DBus','org.freedesktop.DBus.NameHasOwner','string:org.a11y.atspi.Registry'],env=env); registry_owner=('boolean true' in rgown.stdout)
  if not session_bus_owner or not registry_owner: raise RuntimeError(f'owner gate failed session={session_bus_owner} registry={registry_owner}')
  # persistent focused listener + monitor before app start
  mon=spawn('monitor',['dbus-monitor','--address',addr,"type='signal',interface='org.a11y.atspi.Event.Object',member='StateChanged',arg0='focused'"],env)
  listener=spawn('listener',[sys.executable,str(HERE/'register_listener.py'),addr,'20','object:state-changed:focused'],env)
  for _ in range(100):
   if (root/'listener.out').exists() and (root/'listener.out').stat().st_size: break
   time.sleep(.03)
  listener_line=(root/'listener.out').read_text(errors='replace').splitlines()[0]
  listener_obj=json.loads(listener_line)
  # launch app
  svg=root/'fixture.svg';svg.write_text(SVG);before=shab(svg)
  ink=spawn('inkscape',['inkscape',str(svg)],env)
  win=''
  for _ in range(200):
   w=call(['wmctrl','-lp'],env=env).stdout
   for ln in w.splitlines():
    parts=ln.split(maxsplit=4)
    if len(parts)>=5 and parts[2]==str(ink.pid): win=parts[0]
   if win: break
   time.sleep(.05)
  if not win: raise RuntimeError('Inkscape window unavailable')
  call(['wmctrl','-ia',win],env=env);time.sleep(2.0)
  # public named widget positive control
  wd=call([sys.executable,str(HERE/'discover_widget.py'),addr,str(ink.pid)],env={**env,'PYTHONPATH':str(HERE)},timeout=25)
  (root/'widget.json').write_text(wd.stdout); widget=json.loads(wd.stdout); 
  if not widget.get('pass'): raise RuntimeError('widget positive control failed '+wd.stdout+wd.stderr)
  # map app bus, then establish quiet pre-operation point
  app_bus=widget['app_bus'];time.sleep(.5)
  op_start=time.time_ns()/1e9
  # benign File menu focus transitions, no document effect
  d=xdisplay.Display(env['DISPLAY'])
  def raw(k,down):
   kc=d.keysym_to_keycode(XK.string_to_keysym(k));xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc);d.sync()
  def chord(m,k): raw(m,1);raw(k,1);raw(k,0);raw(m,0)
  def key(k): raw(k,1);raw(k,0)
  chord('Alt_L','f');time.sleep(.25);key('Down');time.sleep(.25);key('Escape');time.sleep(.35)
  op_end=time.time_ns()/1e9;d.close();time.sleep(.4)
  # stop monitor before app teardown to avoid defunct noise
  os.killpg(mon.pid,signal.SIGTERM);mon.wait(timeout=2);time.sleep(.05)
  text=(root/'monitor.out').read_text(errors='replace')
  blocks=re.split(r'(?=^signal time=)',text,flags=re.M);ev=[]
  for b in blocks:
   if not b.startswith('signal time='): continue
   h=b.splitlines()[0];m=re.search(r'^signal time=([0-9.]+) sender=([^ ]+).*path=([^;]+); interface=([^;]+); member=([^\n]+)',h)
   if not m: continue
   t=float(m.group(1)); strings=re.findall(r'^\s*string "(.*)"$',b,flags=re.M); ints=[int(x) for x in re.findall(r'^\s*int32 (-?\d+)$',b,flags=re.M)]
   ev.append({'time':t,'sender':m.group(2),'path':m.group(3),'interface':m.group(4),'member':m.group(5).strip(),'strings':strings,'ints':ints})
  inwin=[e for e in ev if op_start-0.05 <= e['time'] <= op_end+0.2 and e['sender']==app_bus and e['strings'] and e['strings'][0]=='focused']
  # final physical keymap
  d=xdisplay.Display(env['DISPLAY']); keymap=list(d.query_keymap());d.close()
  after=shab(svg)
  result={'task':'ATSPI-STANDARD-STACK-20260916-022','display':a.display,'package_sha256':shab('/tmp/atspi-022/at-spi2-core_2.56.2-1+deb13u1_amd64.deb'),'a11y_address':addr,'listener':listener_obj,'inkscape_pid':ink.pid,'app_bus':app_bus,'widget':widget,'op_start_epoch':op_start,'op_end_epoch':op_end,'focused_events_all':len(ev),'focused_events_operation_window':inwin,'focused_operation_event_count':len(inwin),'svg_before_sha256':before,'svg_after_sha256':after,'svg_unchanged':before==after,'final_keymap_hex':bytes(keymap).hex(),'final_keymap_empty':all(x==0 for x in keymap),'registry_get_events_rc':q.returncode,'session_a11y_bus_owner':session_bus_owner,'registry_owner':registry_owner,'pass': bool(inwin) and before==after and all(x==0 for x in keymap) and widget.get('pass') and listener_obj.get('registered') and session_bus_owner and registry_owner}
  (root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
 finally:
  for p,f1,f2 in reversed(procs):
   try:
    if p.poll() is None: os.killpg(p.pid,signal.SIGTERM)
   except Exception: pass
  time.sleep(.1)
  for p,f1,f2 in reversed(procs):
   try:
    if p.poll() is None: os.killpg(p.pid,signal.SIGKILL)
   except Exception: pass
   try:f1.close();f2.close()
   except Exception:pass
  try:
   if 'sesspid' in locals(): os.kill(sesspid,signal.SIGTERM)
  except Exception:pass
  if oldcfg is None:
   try: cfg.unlink()
   except FileNotFoundError:pass
  else: cfg.write_bytes(oldcfg)
if __name__=='__main__': main()
