import json, os, select, subprocess, tempfile, time
from Xlib import X, Xatom
from Xlib.display import Display
from Xlib.ext import xtest

out={"display":"private Xvfb", "tcp_enabled":False, "physical_input":False}
with tempfile.TemporaryDirectory(prefix="xvfb-button-routing-") as td:
 auth=os.path.join(td,"Xauthority"); open(auth,"wb").close(); env=dict(os.environ,XAUTHORITY=auth)
 server=subprocess.Popen(["Xvfb","-displayfd","1","-screen","0","640x480x24","-nolisten","tcp","-ac"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
 try:
  if not select.select([server.stdout],[],[],5)[0]: raise TimeoutError("Xvfb did not allocate display")
  display=":"+server.stdout.readline().strip(); controller=Display(display); root=controller.screen().root
  win=root.create_window(20,20,300,180,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent)
  win.map(); controller.set_input_focus(win,X.RevertToParent,X.CurrentTime); win.warp_pointer(100,100); controller.sync()
  conns={"root":Display(display),"focus":Display(display),"surface":Display(display)}
  conns["root"].screen().root.change_attributes(event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
  conns["focus"].create_resource_object("window",win.id).change_attributes(event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
  conns["surface"].create_resource_object("window",win.id).change_attributes(event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
  for c in conns.values(): c.sync()
  out["window_id"]=win.id; xtest.fake_input(controller,X.ButtonPress,1); controller.sync()
  out["mask_after_press"]=bool(root.query_pointer().mask&X.Button1Mask); time.sleep(.05)
  xtest.fake_input(controller,X.ButtonRelease,1); controller.sync(); out["mask_after_release"]=bool(root.query_pointer().mask&X.Button1Mask)
  out["events"]={k:[] for k in conns}; deadline=time.monotonic()+.5
  while time.monotonic()<deadline:
   for name,c in conns.items():
    while c.pending_events():
     e=c.next_event()
     if e.type in (X.ButtonPress,X.ButtonRelease): out["events"][name].append({"type":e.type,"detail":e.detail,"event":getattr(e,"event",None)})
   time.sleep(.005)
  for c in conns.values(): c.close()
  out["result"]="button state released; recipients recorded"
 finally:
  controller.close()
  server.terminate()
  try: out["xvfb_rc"]=server.wait(timeout=3)
  except subprocess.TimeoutExpired: server.kill(); out["xvfb_rc"]=server.wait(timeout=3)
  out["stderr"]=server.stderr.read(); server.stdout.close(); server.stderr.close()
print(json.dumps(out,indent=2,sort_keys=True))
