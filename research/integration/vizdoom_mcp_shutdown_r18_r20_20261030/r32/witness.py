import json,os,sys,time
from Xlib import X,display
d=display.Display(os.environ['DISPLAY'])
w=d.screen().root.create_window(20,20,120,100,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
w.set_wm_name('Witness');w.map();d.sync()
open(sys.argv[1],'w').write(str(w.id))
while True:
 e=d.next_event()
 if e.type in (X.KeyPress,X.KeyRelease):
  with open(sys.argv[2],'a') as f:f.write(json.dumps({'type':e.type,'detail':e.detail,'ns':time.monotonic_ns()})+'\n')
