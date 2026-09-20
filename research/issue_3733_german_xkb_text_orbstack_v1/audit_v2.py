from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-02"
FORMULA = "=B2*A2"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
HARNESS = Path("/harness")
FORMAL = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def events(text: str) -> list[dict]:
    found = []
    for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
        first = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not first:
            continue
        km = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        sm = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lm = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        raw = bytes.fromhex(lm.group(1)) if lm and lm.group(1).strip() else b""
        found.append({"type":first.group(1),"keycode":int(km.group(1)) if km else None,"keysym":km.group(2).strip() if km else None,"state":int(sm.group(1),16) if sm else None,"lookup_ascii":raw.decode("ascii","replace")})
    return found


def check() -> dict:
    raw_path = FORMAL / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    findings=[]; errors=[]
    manifest=json.loads((HARNESS/"source_manifest_v2.json").read_text())
    if raw.get("allocation")!=ALLOCATION: errors.append("allocation")
    if raw.get("source_base")!=manifest["base_commit"] or raw.get("candidate_blob")!=manifest["candidate_blob"]: errors.append("source_identity")
    if raw.get("source_manifest_sha256")!=sha((HARNESS/"source_manifest_v2.json").read_bytes()): errors.append("manifest_hash")
    if raw.get("runner_sha256")!=sha((HARNESS/"run_v2.py").read_bytes()): errors.append("runner_hash")
    if raw.get("image_ref")!=IMAGE or raw.get("platform")!="linux/arm64" or raw.get("container_network")!="none": errors.append("environment")
    for p,h in manifest["files"].items():
        if sha((Path("/src")/p).read_bytes())!=h: errors.append("source:"+p)
    artifacts={}
    for p in sorted(FORMAL.rglob("*")):
        if p.is_symlink(): errors.append("symlink:"+str(p.relative_to(FORMAL)))
        elif p.is_file() and p.name!="raw.json":
            rel=p.relative_to(FORMAL).as_posix()
            if PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts: errors.append("unsafe_path")
            artifacts[rel]=sha(p.read_bytes())
    if artifacts!=raw.get("artifact_sha256"): errors.append("artifact_inventory")
    if raw.get("formal01_disposition")!="STOP" or len(raw.get("formal01_raw_sha256",""))!=64: errors.append("predecessor_link")
    rows=raw.get("rows",[]); expected=[("de-00","de"),("de-01","de"),("de-02","de"),("us-control","us")]
    if [r.get("case_id") for r in rows]!=[x[0] for x in expected[:len(rows)]]: findings.append("row_order")
    for i,row in enumerate(rows):
        case,layout=expected[i]
        if row.get("requested_layout")!=layout: findings.append(f"row_{i}_layout")
        if not row.get("xvfb_process",{}).get("reaped"): findings.append(f"row_{i}_xvfb_cleanup")
        if row.get("status")!="EXECUTED":
            if i!=len(rows)-1: findings.append("rows_after_nonexecuted")
            continue
        if not row.get("xev_process",{}).get("reaped"): findings.append(f"row_{i}_xev_cleanup")
        if layout=="de":
            a=row.get("after",{})
            if not (a.get("layout")=="de" and a.get("fresh_client") and a.get("server_changed") and a.get("core_map_changed")): findings.append(f"row_{i}_german_gate")
            if row.get("apply",{}).get("argv")!=["setxkbmap","-layout","de"] or row.get("apply",{}).get("returncode")!=0: findings.append(f"row_{i}_apply")
        plan=row.get("candidate_plan_keycodes",[]); expected_trace=[]
        for chord in plan:
            expected_trace.extend(("KeyPress",k) for k in chord)
            expected_trace.extend(("KeyRelease",k) for k in reversed(chord))
        log=(FORMAL/"cases"/case/"xev.log").read_text(errors="replace")
        ev=events(log); trace=[(e["type"],e["keycode"]) for e in ev]
        text="".join(e["lookup_ascii"] for e in ev if e["type"]=="KeyPress")
        if trace!=expected_trace or text!=FORMULA or row.get("receiver_text")!=text: findings.append(f"row_{i}_observed_trace")
        if row.get("emissions_after_text")!=len(expected_trace) or len(ev)!=len(expected_trace): findings.append(f"row_{i}_event_count")
        uc=row.get("unsupported_control",{})
        pre=events((FORMAL/"cases"/case/"unsupported.preflight.xev.txt").read_text(errors="replace"))
        if not uc.get("refused") or "U+20AC" not in str(uc.get("error")) or uc.get("emissions_after")!=0 or any(e["type"]=="KeyPress" for e in pre): findings.append(f"row_{i}_unsupported_preflight")
    stop=bool(rows and rows[-1].get("status","").startswith("STOP_"))
    fail=any(r.get("status","").startswith("FAIL_") for r in rows)
    if stop and raw.get("disposition")!="STOP": findings.append("stop_disposition")
    if fail and raw.get("disposition")!="FAIL": findings.append("fail_disposition")
    if len(rows)<4 and not(stop or fail): findings.append("incomplete")
    if len(rows)==4 and raw.get("disposition")!="EXECUTED_PENDING_INDEPENDENT_AUDIT" and not fail: findings.append("complete_disposition")
    disposition="FAIL_AUDIT_INTEGRITY" if errors else "STOP_ENVIRONMENT_OR_SETUP" if stop and not findings else "FAIL_GERMAN_XKB_TEXT_DELIVERY" if fail or findings else "PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED" if len(rows)==4 else "HOLD_INCOMPLETE"
    return {"allocation":ALLOCATION,"disposition":disposition,"formal_raw_sha256":sha(raw_bytes),"source_manifest_sha256":sha((HARNESS/"source_manifest_v2.json").read_bytes()),"runner_sha256":sha((HARNESS/"run_v2.py").read_bytes()),"auditor_sha256":sha(Path(__file__).read_bytes()),"integrity_errors":errors,"candidate_findings":findings,"source_files_checked":len(manifest["files"]),"artifact_files_checked":len(artifacts),"rows":[{"case_id":r.get("case_id"),"status":r.get("status")} for r in rows],"predecessor_formal01_raw_sha256":raw.get("formal01_raw_sha256")}


def main() -> int:
    result=check()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"independent.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return 1 if result["disposition"]=="FAIL_AUDIT_INTEGRITY" else 0


if __name__=="__main__": raise SystemExit(main())
