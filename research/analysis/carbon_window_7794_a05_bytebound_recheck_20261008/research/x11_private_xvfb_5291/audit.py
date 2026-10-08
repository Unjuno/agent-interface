#!/usr/bin/env python3
"""Independent strict audit for issue #5291."""
import argparse, hashlib, json, re, sys
from pathlib import Path

BASE="1d5b5f2a7b8d7ac6a467a1aaabdfc30c851f7f72"

def audit(path):
    reasons=[]
    try: d=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e: return {"decision":"STOP","reasons":[f"unreadable raw JSON: {e}"]}
    if d.get("schema")!="x11-private-xvfb-5291-v1": reasons.append("schema mismatch")
    if d.get("base_main_sha")!=BASE: reasons.append("base SHA mismatch")
    if d.get("decision")!="PASS": reasons.append("runner decision not PASS")
    valid=lambda n: bool(re.fullmatch(r"mnt:\[[0-9]+\]", str(n)))
    if not valid(d.get("child_mount_ns")) or d.get("child_mount_ns")!=d.get("xvfb_proc_mount_ns") or d.get("child_mount_ns")==d.get("wrapper_mount_ns"): reasons.append("namespace cross-binding failed")
    mi=d.get("mountinfo_line", "").split(" - ")
    if len(mi)!=2 or mi[1].split()[:1]!=["tmpfs"] or mi[0].split()[4:5]!=["/tmp/.X11-unix"]: reasons.append("private tmpfs target/type mismatch")
    if d.get("readiness")!={"width":640,"height":480,"display":":97"}: reasons.append("readiness mismatch")
    if d.get("sigterm_sent") is not True or d.get("xvfb_exit_code")!=0 or d.get("wrapper_exit_code")!=0 or d.get("forced_kill") is not False: reasons.append("clean explicit SIGTERM not independently proven")
    if d.get("host_socket_before")!=d.get("host_socket_after"): reasons.append("host socket changed")
    if not d.get("checks") or not all(d["checks"].values()): reasons.append("checks missing or failed")
    raw=Path(path); log=raw.with_name("runner.log")
    if not raw.is_file() or raw.stat().st_size==0: reasons.append("raw result absent")
    if not log.is_file() or hashlib.sha256(log.read_bytes()).hexdigest()!=d.get("log_sha256"): reasons.append("runner log absent or hash mismatch")
    return {"decision":"PASS" if not reasons else "STOP","reasons":reasons}

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("raw_json",type=Path); r=audit(ap.parse_args().raw_json)
    print(json.dumps(r,indent=2)); sys.exit(0 if r["decision"]=="PASS" else 1)
