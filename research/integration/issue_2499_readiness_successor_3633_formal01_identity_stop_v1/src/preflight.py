"""Readiness construction gate; does not run formal transitions or input."""
import json, os, subprocess, tempfile, time
from pathlib import Path

root=Path(tempfile.mkdtemp(prefix="readiness-preflight-"))
env=os.environ.copy(); env.update(DISPLAY=":158",HOME=str(root),XAUTHORITY=str(root/"Xauthority"))
xvfb=subprocess.Popen(["Xvfb",":158","-screen","0","1600x1000x24"],env=env,
                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
try:
    time.sleep(.5)
    timeout=60
    run=subprocess.run(["/usr/bin/python3","-B","/src/identity_reference.py"],env=env,
                       text=True,capture_output=True,timeout=timeout,check=False)
finally:
    xvfb.terminate()
    xvfb.wait(timeout=5)
if run.returncode!=0:
    raise SystemExit(f"STOP_IDENTITY_PREFLIGHT:{run.returncode}:{run.stderr[-1200:]}")
result=json.loads(run.stdout)
if result.get("decision")!="PASS_XAUTH_COOKIE_IDENTITY_FILTERED":
    raise SystemExit("STOP_IDENTITY_PREFLIGHT:"+str(result.get("decision")))
selected={name:data.get("selected",[]) for name,data in result.get("apps",{}).items()}
if set(selected)!={"inkscape","calc","chromium"} or any(len(rows)!=1 for rows in selected.values()):
    raise SystemExit("STOP_IDENTITY_PREFLIGHT:required role cardinality")
windows=[rows[0].get("window") for rows in selected.values()]
if len(set(windows))!=3:
    raise SystemExit("STOP_IDENTITY_PREFLIGHT:window identity collision")
if any(result.get(key)!=0 for key in ("input_operations","model_calls","network_calls")):
    raise SystemExit("STOP_IDENTITY_PREFLIGHT:unexpected authority activity")
receipt={"decision":"PASS_READINESS_CONSTRUCTION","display":result.get("display"),
         "window_ids":{name:rows[0].get("window") for name,rows in selected.items()},
         "candidate_counts":{name:len(data.get("all_candidates",[])) for name,data in result["apps"].items()},
         "input_operations":0,"model_calls":0,"network_calls":0,
         "source_gate_decision":result["decision"]}
Path(os.environ["PREFLIGHT_OUTPUT"]).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print(json.dumps(receipt,sort_keys=True))
