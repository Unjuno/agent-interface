from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
import Xlib
from Xlib import display
OUT=Path(sys.argv[1]);ALLOC="issue3733-german-xkb-xkbcomp-apply-formal-01";IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
def sha(b):return hashlib.sha256(b).hexdigest()
def cmd(a,e,stdin=None):
 p=subprocess.run(a,env=e,input=stdin,capture_output=True,text=True,timeout=15);return {"argv":a,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
def xlib(n):
 d=display.Display(n);i=d.display.info;m=[list(x) for x in d.get_keyboard_mapping(i.min_keycode,i.max_keycode-i.min_keycode+1)];d.close();return {"map":m,"sha256":sha(json.dumps(m,separators=(",",":")).encode())}
def row(case,layout,num):
 root=OUT/case;root.mkdir(parents=True,exist_ok=False);dn=f":{num}";e=os.environ.copy();e["DISPLAY"]=dn;l=(root/"xvfb.log").open("wb");x=subprocess.Popen(["/usr/bin/Xvfb",dn,"-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST"],env=e,stdin=subprocess.DEVNULL,stdout=l,stderr=subprocess.STDOUT);r={"case":case,"display":dn,"layout":layout,"status":"STOP_SETUP"}
 try:
  end=time.monotonic()+8
  while time.monotonic()<end:
   if x.poll() is not None:raise RuntimeError("XVFB_EXIT")
   try:d=display.Display(dn);break
   except Exception:time.sleep(.05)
  else:raise RuntimeError("XVFB_CONNECT_TIMEOUT")
  r["extensions"]={"XKEYBOARD":bool(d.query_extension("XKEYBOARD").present),"XTEST":bool(d.has_extension("XTEST"))};d.close()
  bq=cmd(["setxkbmap","-display",dn,"-query"],e);bd=cmd(["xkbcomp","-xkb",dn,"-"],e);bm=xlib(dn)
  r["before"]={"query":bq,"xkbcomp":bd,"xlib":bm}
  (root/"before.query.txt").write_text(bq["stdout"]);(root/"before.xkbcomp.txt").write_text(bd["stdout"]);(root/"before.xlib.json").write_text(json.dumps(bm,sort_keys=True)+"\n")
  if layout=="de":
   gen=cmd(["setxkbmap","-display",dn,"-print","-layout","de"],e);r["generate"]={"argv":gen["argv"],"returncode":gen["returncode"],"stderr":gen["stderr"],"stdout_sha256":sha(gen["stdout"].encode())};(root/"generated-de.xkb").write_text(gen["stdout"])
   app=cmd(["xkbcomp","-w","0","-",dn],e,gen["stdout"]);r["direct_apply"]=app;(root/"direct-apply.json").write_text(json.dumps(app,indent=2,sort_keys=True)+"\n")
   aq=cmd(["setxkbmap","-display",dn,"-query"],e);ad=cmd(["xkbcomp","-xkb",dn,"-"],e);am=xlib(dn);r["after"]={"query":aq,"xkbcomp":ad,"xlib":am}
   (root/"after.query.txt").write_text(aq["stdout"]);(root/"after.xkbcomp.txt").write_text(ad["stdout"]);(root/"after.xlib.json").write_text(json.dumps(am,sort_keys=True)+"\n")
   m=re.search(r"(?m)^layout:\s*(\S+)",aq["stdout"]);r["query_layout"]=m.group(1) if m else None;r["changed"]={"xkbcomp":bd["stdout"]!=ad["stdout"],"xlib":bm["map"]!=am["map"]};r["status"]="OBSERVED" if gen["returncode"]==0 and app["returncode"]==0 and r["query_layout"]=="de" else "STOP_DIRECT_APPLY"
  else:r["query_layout"]="us";r["status"]="CONTROL"
 except Exception as ex:r["error"]=f"{type(ex).__name__}:{ex}"
 finally:
  if x.poll() is None:x.terminate()
  try:rc=x.wait(timeout=4)
  except subprocess.TimeoutExpired:x.kill();rc=x.wait(timeout=4)
  l.flush();l.close();r["xvfb_process"]={"pid":x.pid,"returncode":rc,"reaped":x.poll() is not None};r["xvfb_log_sha256"]=sha((root/"xvfb.log").read_bytes())
 return r
def main():
 if any(OUT.iterdir()):raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for c,l,n in (("german","de",191),("us-control","us",192)):
  a=row(c,l,n);rows.append(a)
  if a["status"].startswith("STOP_") or a["status"]=="STOP_SETUP":break
 files={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name!="raw.json"}
 raw={"allocation":ALLOC,"image":IMAGE,"platform":"linux/arm64","network":"none","rows":rows,"artifact_sha256":files,"disposition":"OBSERVED_PENDING_AUDIT" if len(rows)==2 and [z["status"] for z in rows]==["OBSERVED","CONTROL"] else "STOP"}
 (OUT/"raw.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n");print(json.dumps({"allocation":ALLOC,"disposition":raw["disposition"],"rows":[{"case":z["case"],"status":z["status"]} for z in rows]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
