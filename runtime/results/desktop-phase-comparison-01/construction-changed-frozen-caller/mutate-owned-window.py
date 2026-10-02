"""Independent benchmark mutation; no authority/target information for caller."""
import json,os,subprocess,sys,time
from pathlib import Path
from Xlib import display
case=Path(sys.argv[1]).resolve()
allocation=json.loads((case/'allocation.json').read_text())
if allocation['phase']!='changed_dependency':raise ValueError('not a changed allocation')
owner=json.loads((case/'owner.json').read_text())
os.kill(owner['pid'],0)
first=json.loads((case/'replies/001.json').read_text())
if first['request']['op']!='observe' or first['reply']['image_status']!='image':raise ValueError('original primary capture required')
target=owner['window'];env={**os.environ,'DISPLAY':owner['display']}
connection=display.Display(owner['display']);window=connection.create_resource_object('window',target)
def geometry():
 g=window.get_geometry();pos=connection.screen().root.translate_coords(window,0,0)
 return {'x':pos.x,'y':pos.y,'width':g.width,'height':g.height}
try:
 before=geometry();started=time.monotonic_ns()
 subprocess.run(['wmctrl','-ir',hex(target),'-b','remove,maximized_vert,maximized_horz'],env=env,check=True)
 subprocess.run(['wmctrl','-ir',hex(target),'-e',f"0,{before['x']+40},{before['y']+30},-1,-1"],env=env,check=True)
 deadline=time.monotonic()+2
 while True:
  connection.sync();after=geometry()
  if after!=before or time.monotonic()>deadline:break
  time.sleep(.02)
 row={'before':before,'after':after,'requested_delta':[40,30],'started_ns':started,'ended_ns':time.monotonic_ns(),'geometry_changed':after!=before,'controller_receives_replacement_target':False,'input_emitted':False}
 with (case/'external-mutation.json').open('x') as f:json.dump(row,f,indent=2)
 if after==before:raise RuntimeError('mutation inconclusive; no retry')
 print('Owned geometry changed; no new caller image or target supplied.')
finally:connection.close()
