import json,os,select,subprocess,tempfile,time
from Xlib import X
from Xlib.display import Display
from Xlib.ext import xtest
from Xlib import error

out={"physical_input":False,"tcp_enabled":False,"arms":[]}
with tempfile.TemporaryDirectory() as td:
 auth=os.path.join(td,'Xauthority');open(auth,'wb').close();env=dict(os.environ,XAUTHORITY=auth)
 xv=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
 try:
  if not select.select([xv.stdout],[],[],5)[0]:raise TimeoutError('displayfd')
  name=':'+xv.stdout.readline().strip(); ctrl=Display(name);root=ctrl.screen().root
  win=root.create_window(20,20,300,180,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent)
  win.map();ctrl.set_input_focus(win,X.RevertToParent,X.CurrentTime);win.warp_pointer(100,100);ctrl.sync()
  first=Display(name); second=Display(name)
  first.create_resource_object('window',win.id).change_attributes(event_mask=X.KeyReleaseMask|X.ButtonPressMask)
  first.sync(); second.create_resource_object('window',win.id).change_attributes(event_mask=X.ButtonReleaseMask)
  try:second.sync();out['second_focus_select']='ok'
  except error.XError as e:out['second_focus_select']=type(e).__name__+':'+str(e)
  rootc=Display(name);rootc.screen().root.change_attributes(event_mask=X.ButtonReleaseMask)
  try:rootc.sync();out['root_select']='ok'
  except error.XError as e:out['root_select']=type(e).__name__+':'+str(e)
  xtest.fake_input(ctrl,X.ButtonPress,1);ctrl.sync();xtest.fake_input(ctrl,X.ButtonRelease,1);ctrl.sync()
  events={'first_focus':[],'second_focus':[],'root':[]};end=time.monotonic()+.3
  while time.monotonic()<end:
   for label,c in [('first_focus',first),('second_focus',second),('root',rootc)]:
    while c.pending_events():
     e=c.next_event()
     if e.type in (X.ButtonPress,X.ButtonRelease):events[label].append(e.type)
   time.sleep(.002)
  out['arms'].append({'client1_mask':'KeyRelease|ButtonPress','client2_mask':'ButtonRelease','events':events,
    'pointer_mask_after':root.query_pointer().mask})
  out['xvfb_rc']=None
  for c in (first,second,rootc,ctrl):c.close()
 finally:
  xv.terminate()
  try:out['xvfb_rc']=xv.wait(timeout=3)
  except subprocess.TimeoutExpired:xv.kill();out['xvfb_rc']=xv.wait(timeout=3)
  out['stderr']=xv.stderr.read();xv.stdout.close();xv.stderr.close()
print(json.dumps(out,indent=2,sort_keys=True))
