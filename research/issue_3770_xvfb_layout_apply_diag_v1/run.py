from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
import Xlib
from Xlib import display
OUT=Path(sys.argv[1]);ALLOC="issue3733-german-xkb-apply-diagnostic-formal-01";IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
def sha(b):return hashlib.sha256(b).hexdigest()
def cmd(argv,env):
 try:
  p=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=12);return {"argv":argv,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
 except Exception as e:return {"argv":argv,"exception":f"{type(e).__name__}:{e}"}
def xlib(name):
 d=display.Display(name);i=d.display.info;m=[list(x) for x in d.get_keyboard_mapping(i.min_keycode,i.max_keycode-i.min_keycode+1)];d.close();return {"map":m,"sha256":sha(json.dumps(m,separators=(",",":")).encode())}
def row(case,layout,n):
 root=OUT/case;root.mkdir(parents=True,exist_ok=False);dn=f":{n}";env=os.environ.copy();env["DISPLAY"]=dn;log=(root/"xvfb.log").open("wb")
 xv=subprocess.Popen(["/usr/bin/Xvfb",dn,"-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST"],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);r={"case":case,"layout":layout,"display":dn,"status":"STOP_SETUP"}
 try:
  end=time.monotonic()+8
  while time.monotonic()<end:
   if xv.poll() is not None:raise RuntimeError("XVFB_EXIT")
   try:d=display.Display(dn);break
   except Exception:time.sleep(.05)
  else:raise RuntimeError("XVFB_CONNECT_TIMEOUT")
  r["extensions"]={"XKEYBOARD":bool(d.query_extension("XKEYBOARD").present),"XTEST":bool(d.has_extension("XTEST"))};d.close()
  r["before"]={"query":cmd(["setxkbmap","-display",dn,"-query"],env),"rules":cmd(["setxkbmap","-display",dn,"-print","-verbose","10"],env),"xkbcomp":cmd(["xkbcomp","-xkb",dn,"-"],env),"xlib":xlib(dn)}
  for k in ("query","rules","xkbcomp"): (root/f"before.{k}.txt").write_text(r["before"][k].get("stdout",""))
  (root/"before.xlib.json").write_text(json.dumps(r["before"]["xlib"],sort_keys=True)+"\n")
  if "layout:     us" not in r["before"]["query"].get("stdout","") and "layout: us" not in r["before"]["query"].get("stdout",""):raise RuntimeError("BASELINE_NOT_US")
  if layout=="de":
   r["apply"]=cmd(["setxkbmap","-display",dn,"-verbose","10","-layout","de"],env);(root/"apply.json").write_text(json.dumps(r["apply"],indent=2,sort_keys=True)+"\n")
   r["print_after"]=cmd(["setxkbmap","-display",dn,"-print","-verbose","10","-layout","de"],env);(root/"print-after.json").write_text(json.dumps(r["print_after"],indent=2,sort_keys=True)+"\n")
   time.sleep(.25)
   r["after"]={"query":cmd(["setxkbmap","-display",dn,"-query"],env),"xkbcomp":cmd(["xkbcomp","-xkb",dn,"-"],env),"xlib":xlib(dn)}
   for k in ("query","xkbcomp"): (root/f"after.{k}.txt").write_text(r["after"][k].get("stdout",""))
   (root/"after.xlib.json").write_text(json.dumps(r["after"]["xlib"],sort_keys=True)+"\n")
   m=re.search(r"(?m)^layout:\s*(\S+)",r["after"]["query"].get("stdout",""));r["query_layout"]=m.group(1) if m else None
   r["changed"]={"xkbcomp":r["before"]["xkbcomp"].get("stdout")!=r["after"]["xkbcomp"].get("stdout"),"xlib":r["before"]["xlib"]["map"]!=r["after"]["xlib"]["map"]}
   r["status"]="OBSERVED" if r["query_layout"]=="de" else "STOP_LAYOUT_NOT_APPLIED"
  else:r["query_layout"]="us";r["status"]="CONTROL"
 except Exception as e:r["error"]=f"{type(e).__name__}:{e}"
 finally:
  if xv.poll() is None:xv.terminate()
  try:rc=xv.wait(timeout=4)
  except subprocess.TimeoutExpired:xv.kill();rc=xv.wait(timeout=4)
  log.flush();log.close();r["xvfb_process"]={"pid":xv.pid,"returncode":rc,"reaped":xv.poll() is not None};r["xvfb_log_sha256"]=sha((root/"xvfb.log").read_bytes())
 return r
def main():
 if any(OUT.iterdir()):raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for c,l,n in (("german","de",181),("us-control","us",182)):
  r=row(c,l,n);rows.append(r)
  if r["status"].startswith("STOP_") or r["status"]=="STOP_SETUP":break
 inventory={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name!="raw.json"}
 out={"allocation":ALLOC,"image":IMAGE,"platform":"linux/arm64","network":"none","rows":rows,"artifact_sha256":inventory,"disposition":"OBSERVED_PENDING_AUDIT" if len(rows)==2 and [r["status"] for r in rows]==["OBSERVED","CONTROL"] else "STOP"}
 (OUT/"raw.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"allocation":ALLOC,"disposition":out["disposition"],"rows":[{"case":r["case"],"status":r["status"]} for r in rows]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
