import pathlib,json,hashlib,os,time,subprocess,signal,traceback
from Xlib import X,XK,display
from Xlib.ext import xtest
from runtime.backends.x11_v1.backend import X11Backend
R=pathlib.Path('/src');O=pathlib.Path('/out');P=json.loads((R/'PLAN.json').read_text());F=json.loads((R/'FREEZE.json').read_text());rows=[];errors=[]
def now():return time.monotonic_ns()
for p,h in F['source_hashes'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:raise RuntimeError('source pin '+p)
for i,name in enumerate(P['cells']):
 d=b=None;p=None;log=None;row=dict(cell=name,events=[],errors=[],started_ns=now())
 try:
  disp=':'+str(170+i);log=(O/(name+'.xvfb.log')).open('wb');p=subprocess.Popen(['Xvfb',disp,'-screen','0','640x480x24','-nolisten','tcp','-ac'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);row['server_pid']=p.pid
  end=now()+3_000_000_000
  while d is None:
   try:d=display.Display(disp)
   except Exception:
    if now()>end or p.poll() is not None:raise
    time.sleep(.02)
  b=X11Backend(disp,{})
  def observe(label):
   start=now();bits=d.query_keymap();r=dict(label=label,start_ns=start,end_ns=now(),keys=[n for n in range(256) if bits[n//8]&(1<<(n%8))]);row['events'].append(r);return r
  codes=dict(alt=d.keysym_to_keycode(XK.string_to_keysym('Alt_L')),a=d.keysym_to_keycode(XK.string_to_keysym('b')));row['codes']=codes
  if observe('initial')['keys']:raise RuntimeError('fresh display not neutral')
  if name in ('owned_alt','overlap_alt'):
   b.key_state('ALT',True);row['events'].append(dict(label='owned_down',time_ns=now(),tracking=dict(b.held_keycodes)))
  if name in ('foreign_b','overlap_alt'):
   code=codes['b' if name=='foreign_b' else 'alt'];xtest.fake_input(d,X.KeyPress,code);d.sync();row['foreign_keycode']=code;row['events'].append(dict(label='foreign_down',time_ns=now(),keycode=code))
  observe('before_release');start=now();row['release_receipt']=b.release_all();row['release_start_ns']=start;row['release_end_ns']=now();row['backend_tracking_after']=dict(b.held_keycodes);row['backend_emissions']=b.emissions;observe('after_release')
 except Exception:row['errors'].append(traceback.format_exc())
 finally:
  if d:
   try:
    for n in (row.get('codes') or {}).values():xtest.fake_input(d,X.KeyRelease,n)
    d.sync();row['cleanup_keymap']=[n for n in range(256) if (bits:=d.query_keymap())[n//8]&(1<<(n%8))];d.close()
   except Exception:row['errors'].append(traceback.format_exc())
  if b:
   try:b.close()
   except Exception:row['errors'].append(traceback.format_exc())
  if p:
   if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
   try:row['server_exit']=p.wait(3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);row['server_exit']=p.wait(3);row['errors'].append('required SIGKILL')
  if log:log.close()
  row['ended_ns']=now();rows.append(row);errors.extend(row['errors'])
  (O/'RAW.json').write_text(json.dumps(dict(rows=rows,errors=errors,source_hashes=F['source_hashes']),indent=2)+'\n')
 if row['errors']:break
print(json.dumps(dict(cells=len(rows),errors=errors)));raise SystemExit(bool(errors))
