#!/usr/bin/env python3
"""Construction-ready successor runner; one row may be used as excluded probe."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from Xlib import X,display
from Xlib.ext import xtest

CASES={
"valid":[{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}],
"true_then_revoke":[{"kind":"obs","gen":1,"seq":1,"target":"A","value":True},{"kind":"revoke","gen":1,"seq":2,"target":"A"}],
"revoke_first":[{"kind":"revoke","gen":1,"seq":1,"target":"A"},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
"replacement_delayed_old":[{"kind":"replace","gen":2,"seq":1,"target":"B"},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
"out_of_order_false":[{"kind":"obs","gen":1,"seq":3,"target":"A","value":True},{"kind":"obs","gen":1,"seq":2,"target":"A","value":False}],
"duplicate_true":[{"kind":"obs","gen":1,"seq":1,"target":"A","value":False},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
"restart_replay":[{"kind":"obs","gen":1,"seq":1,"target":"A","value":True},{"kind":"restart","gen":2,"seq":0,"target":"A"},{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}],
"effect_off":[{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}]}
POLICIES=("RESIDENT_INCREMENTAL","LAST_MESSAGE","MESSAGE_COUNT","RESTART_REPLAY_UNGUARDED")

def apply(policy,events):
 actions=[];gen=1;target="A";lastseq={};prev=False;revoked=False
 for i,e in enumerate(events):
  if policy=="RESIDENT_INCREMENTAL":
   if e["kind"] in ("restart","replace"):
    gen=e["gen"];lastseq={};prev=False;revoked=False
    if e["kind"]=="replace":target=e["target"]
   elif e["kind"]=="revoke":
    if e["gen"]==gen and e["target"]==target:revoked=True;prev=False
   elif e["kind"]=="obs" and e["gen"]==gen and e["target"]==target and e["seq"]>lastseq.get(e["gen"],-1):
    lastseq[e["gen"]]=e["seq"]
    if not revoked and e["value"] and not prev:actions.append(i)
    prev=bool(e["value"])
  elif policy=="MESSAGE_COUNT":
   if e["kind"]=="obs" and e["value"]:actions.append(i)
  elif policy=="RESTART_REPLAY_UNGUARDED":
   if e["kind"]=="obs" and e["value"]:actions.append(i)
 if policy=="LAST_MESSAGE" and events and events[-1]["kind"]=="obs" and events[-1].get("value"):actions=[len(events)-1]
 return actions

def proc_start(pid):
 try:return Path(f"/proc/{pid}/stat").read_text().split()[21]
 except FileNotFoundError:return None

def find_window(root):
 for _ in range(200):
  for w in root.query_tree().children:
   try:
    if (w.get_wm_name() or "").startswith("resident-fixture:"):return w
   except Exception:pass
  time.sleep(.02)
 raise RuntimeError("fixture window missing")

def image_bytes(w,conn):
 g=w.get_geometry();conn.sync()
 b=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff).data
 return g.width,g.height,b

def run_row(policy,case,events,effect,frames):
 d=":201";env={**os.environ,"DISPLAY":d,"EFFECT_MODE":"on" if effect else "off"}
 xvfb=subprocess.Popen(["/usr/bin/Xvfb",d,"-screen","0","640x480x24","-nolisten","tcp"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 app=None;conn=None;record={"policy":policy,"case":case,"events":events,"effect_enabled":effect}
 try:
  record["xvfb_pid"]=xvfb.pid;record["xvfb_start_ticks"]=proc_start(xvfb.pid);time.sleep(.12)
  conn=display.Display(d);root=conn.screen().root
  app=subprocess.Popen(["python3","/src/fixture.py"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  record["fixture_pid"]=app.pid;record["fixture_start_ticks"]=proc_start(app.pid)
  w=find_window(root)
  until=time.monotonic()+2
  while w.get_attributes().map_state!=X.IsViewable and time.monotonic()<until:time.sleep(.02)
  if w.get_attributes().map_state!=X.IsViewable:raise RuntimeError("fixture not viewable")
  w.set_input_focus(X.RevertToParent,X.CurrentTime);conn.sync();time.sleep(.1)
  focus=conn.get_input_focus().focus
  if focus not in (w,w.id):raise RuntimeError(f"fixture focus not acquired: {focus}")
  action_ix=apply(policy,events);record["action_event_indices"]=action_ix;record["transport_count"]=len(action_ix)
  ww,hh,before=image_bytes(w,conn);code=conn.keysym_to_keycode(0x20)
  for _ in action_ix:
   xtest.fake_input(conn,X.KeyPress,code);conn.sync();xtest.fake_input(conn,X.KeyRelease,code);conn.sync()
  expected=f"resident-fixture:{len(action_ix) if effect else 0}";deadline=time.monotonic()+2
  prev=None;stable=0;after=b""
  while time.monotonic()<deadline:
   if w.get_wm_name()==expected:
    _,_,frame=image_bytes(w,conn)
    if frame==prev:stable+=1
    else:stable=0
    prev=frame
    if stable>=3:after=frame;break
   time.sleep(.03)
  if not after:after=prev or b""
  record.update(width=ww,height=hh,bytes_per_frame=len(before),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),window_pixels_changed=before!=after,gui_title=w.get_wm_name(),task_effect_count=int(w.get_wm_name().split(":")[-1]))
  if w.get_wm_name()!=expected:raise RuntimeError(f"fixture title did not reach expected state: {w.get_wm_name()} != {expected}")
  stem=f"{policy}__{case}"
  (frames/(stem+"__before.raw")).write_bytes(before);(frames/(stem+"__after.raw")).write_bytes(after)
  record["frame_paths"]=[stem+"__before.raw",stem+"__after.raw"]
  km=conn.query_keymap();record["key_release_verified"]=not bool(km[code//8]&(1<<(code%8)))
  return record
 finally:
  if conn:conn.close()
  if app:
   app.terminate();app.wait(timeout=3);record["fixture_exit_code"]=app.returncode;record["fixture_reaped"]=app.poll() is not None
  xvfb.terminate();xvfb.wait(timeout=3);record["xvfb_exit_code"]=xvfb.returncode;record["xvfb_reaped"]=xvfb.poll() is not None

def main():
 out=Path("/evidence");frames=out/"frames";frames.mkdir(parents=True,exist_ok=True)
 only=os.getenv("PROBE_CASE");rows=[]
 for c,events in CASES.items():
  if only and c!=only:continue
  for p in POLICIES:rows.append(run_row(p,c,events,c!="effect_off",frames))
 (out/"rows.json").write_text(json.dumps({"allocation":os.environ.get("ALLOCATION_ID"),"rows":rows},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"allocation":os.environ.get("ALLOCATION_ID"),"rows":len(rows),"releases":all(r["key_release_verified"] for r in rows),"cleanup":all(r.get("fixture_reaped") and r.get("xvfb_reaped") for r in rows)},sort_keys=True))

if __name__=="__main__":main()
