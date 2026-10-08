#!/usr/bin/env python3
"""Independent strict audit for a #5286 runner result."""
import argparse
import json
from pathlib import Path
import re
import sys

BASE = "c45e1947e498dce08abfb27e459e610054a0602e"


def audit(path: Path):
    reasons = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"decision": "STOP", "reasons": [f"unreadable JSON: {e}"]}
    if d.get("schema") != "x11-private-xvfb-5286-v1": reasons.append("schema mismatch")
    if d.get("base_main_sha") != BASE: reasons.append("base main SHA mismatch")
    if d.get("decision") != "PASS": reasons.append("runner decision is not PASS")
    valid_ns = lambda x: bool(re.fullmatch(r"mnt:\[[0-9]+\]", str(x)))
    if not valid_ns(d.get("wrapper_mount_ns")) or not valid_ns(d.get("child_mount_ns")) or d.get("child_mount_ns") == d.get("wrapper_mount_ns") or d.get("xvfb_proc_mount_ns") != d.get("child_mount_ns") or not isinstance(d.get("xvfb_pid"), int): reasons.append("child mount namespace is not bound to host /proc PID record")
    mi = d.get("mountinfo_line", "")
    fields = mi.split(" - ")
    if len(fields) != 2 or fields[1].split()[0:1] != ["tmpfs"] or len(fields[0].split()) < 5 or fields[0].split()[4] != "/tmp/.X11-unix": reasons.append("private mount target/filesystem mismatch")
    if d.get("readiness", {}).get("width") != 640 or d.get("readiness", {}).get("height") != 480: reasons.append("readiness dimensions mismatch")
    if d.get("sigterm_sent") is not True or d.get("xvfb_exit_code") != 0 or d.get("forced_kill") is not False: reasons.append("explicit clean SIGTERM not proven")
    if d.get("host_socket_before") != d.get("host_socket_after"): reasons.append("host WSLg socket changed")
    if not all(d.get("checks", {}).values()) or not d.get("checks"): reasons.append("runner checks absent or failed")
    if not path.is_file() or path.stat().st_size == 0: reasons.append("raw record is not durable")
    log_path = path.with_name("runner.log")
    if not log_path.is_file(): reasons.append("runner log missing")
    else:
        import hashlib
        if hashlib.sha256(log_path.read_bytes()).hexdigest() != d.get("log_sha256"): reasons.append("runner log hash mismatch")
    return {"decision": "PASS" if not reasons else "STOP", "reasons": reasons}


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("raw_json", type=Path)
    result = audit(p.parse_args().raw_json)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["decision"] == "PASS" else 1)
