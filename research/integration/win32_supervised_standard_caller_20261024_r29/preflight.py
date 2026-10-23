"""R29 input-free source, predecessor, and registry preflight."""
from __future__ import annotations
import datetime as dt, hashlib, json, platform, subprocess, sys, winreg
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]; C=json.loads((P/"conditions.json").read_text(encoding="utf-8")); out={"schema":"win32-supervised-standard-caller-r29-preflight-v1","utc":dt.datetime.now(dt.timezone.utc).isoformat(),"native_input_sent":False,"checks":{}}
try:
 commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(); out["source_commit"]=commit; out["checks"]["frozen_commit"]=commit==C["source_commit"]
 out["checks"]["tracked_tree_clean"]=subprocess.run(["git","diff","--quiet","HEAD","--"],cwd=ROOT).returncode==0 and subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT).returncode==0
 src={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in C["source_sha256"] if k not in ("probe.py","audit.py")}; src["probe.py"]=hashlib.sha256((P/"probe.py").read_bytes()).hexdigest(); src["audit.py"]=hashlib.sha256((P/"audit.py").read_bytes()).hexdigest(); out["source_sha256"]=src; out["checks"]["source_hashes_match"]=src==C["source_sha256"]
 pkt={k:hashlib.sha256((P/k).read_bytes()).hexdigest() for k in C["frozen_files"]}; out["frozen_packet_hashes"]=pkt; out["checks"]["frozen_packet_hashes_match"]=pkt==C["frozen_files"]
 pred=C["predecessor"]; ph={"raw":hashlib.sha256((ROOT/pred["raw_path"]).read_bytes()).hexdigest(),"audit":hashlib.sha256((ROOT/pred["audit_path"]).read_bytes()).hexdigest()}; out["predecessor_hashes"]=ph; r=json.loads((ROOT/pred["raw_path"]).read_text(encoding="utf-8")); a=json.loads((ROOT/pred["audit_path"]).read_text(encoding="utf-8")); checks={"hashes_match":ph=={"raw":pred["raw_sha256"],"audit":pred["audit_sha256"]},"R14_audit_19_of_20_fail_unknown":a.get("status")=="FAIL_OR_UNKNOWN" and a.get("passed")==19 and a.get("total")==20,"callback_still_blocked_after_hold":r.get("post_cancel_io_hold",{}).get("hook_trace_before_release",{}).get("callback_return_ns") is None,"release_not_confirmed_during_block":not any(x.get("cancellation_release_confirmed") is True for x in r.get("post_cancel_io_hold",{}).get("status_polls",[])),"R14_fixture_and_foreground_cleanup":r.get("fixture",{}).get("exit_code")==0 and r.get("foreground_restore",{}).get("restored") is True}; out["R14_predecessor_semantics"]=checks; out["checks"]["R14_predecessor_verified"]=all(checks.values())
 prev=C["previous_prelaunch_stop"]; launch=json.loads((ROOT/prev["launch_failure_path"]).read_text(encoding="utf-8")); prevhash=hashlib.sha256((ROOT/prev["launch_failure_path"]).read_bytes()).hexdigest(); out["R15_prelaunch"]=launch; out["checks"]["R15_no_input_prelaunch_failure_preserved"]=prevhash==prev["launch_failure_sha256"] and launch.get("caller_dispatches")==0 and launch.get("fixture_created") is False and launch.get("native_input_sent") is False
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Control Panel\Desktop") as key:
  try: value,typ=winreg.QueryValueEx(key,"LowLevelHooksTimeout"); observed={"present":True,"value":value,"type":typ}
  except FileNotFoundError: observed={"present":False,"value":None,"type":None}
 out["low_level_hooks_timeout_registry"]=observed; out["checks"]["registry_matches_frozen_read_only_observation"]=(observed["present"] is False and C["environment"]["low_level_hooks_timeout_registry"].endswith("absent at R29 preflight; read only"))
 out["checks"]["native_windows"]=sys.platform=="win32"; out["platform"]=platform.platform(); out["python"]=sys.version
 for name in ("probe.py","audit.py"): compile((P/name).read_text(encoding="utf-8"),name,"exec")
 out["checks"]["python_sources_compile"]=True; out["status"]="PASS" if all(out["checks"].values()) else "FAIL_OR_UNKNOWN"
except BaseException as e: out["status"]="FAIL_OR_UNKNOWN"; out["error"]={"type":type(e).__name__,"detail":str(e)}
(P/"preflight.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps({"status":out["status"],"checks":out["checks"],"native_input_sent":False},sort_keys=True)); raise SystemExit(0 if out["status"]=="PASS" else 1)
