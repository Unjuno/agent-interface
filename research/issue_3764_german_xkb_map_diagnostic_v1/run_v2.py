from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
import Xlib
from Xlib import XK,display

OUT=Path(sys.argv[1]); ALLOCATION="issue3733-german-xkb-map-diagnostic-formal-02"
IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
BASE="e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8"
def sha(b):return hashlib.sha256(b).hexdigest()
def cmd(argv,env):
 p=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=12)
 return {"argv":argv,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
def xmap(name):
 d=display.Display(name); info=d.display.info
 rows=[list(x) for x in d.get_keyboard_mapping(info.min_keycode,info.max_keycode-info.min_keycode+1)]
 selected={}
 for label,sym in (("y","y"),("z","z"),("equal","equal"),("asterisk","asterisk")):
  c=d.keysym_to_keycode(XK.string_to_keysym(sym)); selected[label]={"keycode":int(c),"level0":int(d.keycode_to_keysym(c,0)),"level1":int(d.keycode_to_keysym(c,1))}
 d.close(); return {"min_keycode":info.min_keycode,"max_keycode":info.max_keycode,"mapping":rows,"mapping_sha256":sha(json.dumps(rows,separators=(",",":")).encode()),"selected":selected}
def one(case,layout,number):
 root=OUT/case; root.mkdir(parents=True,exist_ok=False); disp=f":{number}"; env=os.environ.copy(); env["DISPLAY"]=disp
 log=(root/"xvfb.log").open("wb")
 xv=subprocess.Popen(["/usr/bin/Xvfb",disp,"-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST"],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
 row={"case":case,"layout":layout,"display":disp,"status":"STOP_SETUP"}
 try:
  deadline=time.monotonic()+8
  while time.monotonic()<deadline:
   if xv.poll() is not None:raise RuntimeError("XVFB_EXIT")
   try:d=display.Display(disp);break
   except Exception:time.sleep(.05)
  else:raise RuntimeError("XVFB_CONNECT_TIMEOUT")
  row["extensions"]={"XKEYBOARD":bool(d.query_extension("XKEYBOARD").present),"XTEST":bool(d.has_extension("XTEST"))};d.close()
  if not all(row["extensions"].values()):raise RuntimeError("X11_EXTENSION_MISSING")
  bq=cmd(["setxkbmap","-query"],env);bd=cmd(["xkbcomp","-xkb",disp,"-"],env);bm=xmap(disp)
  (root/"before.query.txt").write_text(bq["stdout"]);(root/"before.xkbcomp.txt").write_text(bd["stdout"]);(root/"before.xlib.json").write_text(json.dumps(bm,indent=2,sort_keys=True)+"\n")
  row["before"]={"query":bq,"xkbcomp":bd,"xlib":bm}
  if not(bq["returncode"]==0 and bd["returncode"]==0 and re.search(r"(?m)^layout:\s*us\s*$",bq["stdout"])):raise RuntimeError("BASELINE_NOT_US")
  if layout=="de":
   ap=cmd(["setxkbmap","-layout","de"],env);aq=cmd(["setxkbmap","-query"],env);ad=cmd(["xkbcomp","-xkb",disp,"-"],env);am=xmap(disp)
   (root/"apply.json").write_text(json.dumps(ap,indent=2,sort_keys=True)+"\n");(root/"after.query.txt").write_text(aq["stdout"]);(root/"after.xkbcomp.txt").write_text(ad["stdout"]);(root/"after.xlib.json").write_text(json.dumps(am,indent=2,sort_keys=True)+"\n")
   q=re.search(r"(?m)^layout:\s*(\S+)",aq["stdout"])
   row["apply"]=ap;row["after"]={"query":aq,"xkbcomp":ad,"xlib":am};row["query_layout"]=q.group(1) if q else None
   row["changed"]={"server_dump":bd["stdout"]!=ad["stdout"],"xlib_full_map":bm["mapping"]!=am["mapping"],"xlib_selected":bm["selected"]!=am["selected"]}
   row["status"]="OBSERVED" if ap["returncode"]==0 and aq["returncode"]==0 and ad["returncode"]==0 and row["query_layout"]=="de" else "STOP_LAYOUT_APPLY"
  else:
   row["query_layout"]="us";row["changed"]={"server_dump":False,"xlib_full_map":False,"xlib_selected":False};row["status"]="CONTROL"
 except Exception as e:row["error"]=f"{type(e).__name__}:{e}"
 finally:
  if xv.poll() is None:xv.terminate()
  try:rc=xv.wait(timeout=4)
  except subprocess.TimeoutExpired:xv.kill();rc=xv.wait(timeout=4)
  log.flush();log.close();row["xvfb_process"]={"pid":xv.pid,"returncode":rc,"reaped":xv.poll() is not None};row["xvfb_log_sha256"]=sha((root/"xvfb.log").read_bytes())
 return row
def main():
 if any(OUT.iterdir()):raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for case,layout,n in (("german","de",171),("us-control","us",172)):
  row=one(case,layout,n);rows.append(row)
  if row["status"].startswith("STOP_") or row["status"]=="STOP_SETUP":break
 artifacts={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name!="raw.json"}
 raw={"allocation":ALLOCATION,"base_commit":BASE,"image":IMAGE,"platform":"linux/arm64","network":"none","xlib_version":str(getattr(Xlib,"__version__","unknown")),"rows":rows,"artifact_sha256":artifacts,"disposition":"OBSERVED_PENDING_AUDIT" if len(rows)==2 and [r["status"] for r in rows]==["OBSERVED","CONTROL"] else "STOP"}
 (OUT/"raw.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n");print(json.dumps({"allocation":ALLOCATION,"disposition":raw["disposition"],"rows":[{"case":r["case"],"status":r["status"]} for r in rows]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
