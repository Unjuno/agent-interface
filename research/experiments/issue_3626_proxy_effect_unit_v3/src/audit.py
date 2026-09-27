"""Independent raw auditor; no imports from the experiment runner or proxy."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path("/input")
OUT = Path("/evidence")
ARMS = {"ordinary_screenshot", "proxy_image", "structured_proxy", "hybrid"}
CASES = {"positive", "no_effect", "stale_version", "target_replaced", "unavailable", "ambiguous", "macro_failure"}
NEGATIVE_DECISIONS = {
    "stale_version": "REFUSE_STALE_BINDING",
    "target_replaced": "REFUSE_STALE_BINDING",
    "unavailable": "YIELD_TARGET_UNAVAILABLE",
    "ambiguous": "YIELD_TARGET_AMBIGUOUS",
    "macro_failure": "YIELD_MACRO_FAILURE",
    "no_effect": "YIELD_NO_APPLICATION_EFFECT",
}


def digest(data): return hashlib.sha256(data).hexdigest()


def validate(raw, check_files=True):
    errors=[]
    rows=raw.get("rows")
    if not isinstance(rows,list) or len(rows)!=28: return ["expected exactly 28 rows"]
    expected={(a,c) for a in ARMS for c in CASES}
    observed={(r.get("arm"),r.get("case")) for r in rows}
    if observed!=expected or len(observed)!=len(rows): errors.append("row identity/denominator mismatch")
    if raw.get("formal_invocations")!=1 or raw.get("retries")!=0: errors.append("formal invocation count mismatch")
    for r in rows:
        label=f"{r.get('arm')}/{r.get('case')}"
        case=r.get("case")
        if r.get("error") is not None: errors.append(f"{label}: runner error"); continue
        if r.get("decision") != ("COMPLETED" if case=="positive" else NEGATIVE_DECISIONS[case]): errors.append(f"{label}: decision mismatch")
        request=r.get("request",{})
        if request.get("operation")!="increment" or request.get("representation_arm")!=r.get("arm"): errors.append(f"{label}: request/arm mismatch")
        if request.get("source_token")!= {k:r.get("initial_state",{}).get(k) for k in ("xid","pid","start_ticks","counter","version","title")}: errors.append(f"{label}: source token mismatch")
        if request.get("source_frame_sha256")!=r.get("initial_state",{}).get("frame_sha256"): errors.append(f"{label}: source image binding mismatch")
        if r.get("reply",{}).get("decision")!=r.get("decision"): errors.append(f"{label}: request/reply decision mismatch")
        if not r.get("release_verified") or not r.get("socket_disappeared"): errors.append(f"{label}: release/socket cleanup missing")
        if not r.get("processes") or any(not p.get("pid") or not p.get("start_ticks") for p in r["processes"]): errors.append(f"{label}: process incarnation missing")
        if not r.get("process_exit_codes") or any(v not in (0,-15,-9) for v in r["process_exit_codes"].values()): errors.append(f"{label}: process exit/reap missing")
        ev=r.get("fixture_events",[])
        evpath=ROOT/"rows"/r.get("row_id","")/"fixture-events.jsonl"
        if check_files:
            if not evpath.is_file(): errors.append(f"{label}: fixture event log missing")
            elif digest(evpath.read_bytes())!=r.get("fixture_events_sha256"): errors.append(f"{label}: fixture event log hash mismatch")
        fixture_pids=sorted(p.get("pid") for p in r.get("processes",[]) if p.get("role") in {"fixture","fixture_replacement","duplicate_fixture"})
        ready_pids=sorted(e.get("pid") for e in ev if e.get("kind")=="ready")
        if fixture_pids!=ready_pids: errors.append(f"{label}: fixture PID/start evidence does not match app event owners")
        if len(r.get("process_exit_codes",{}))!=len(r.get("processes",[])): errors.append(f"{label}: not every child has an exit/reap record")
        ack=sum(x.get("kind")=="click_ack" for x in ev)
        effects=sum(x.get("kind")=="effect" for x in ev)
        if bool(ack)!=bool(r.get("input_ack")): errors.append(f"{label}: click acknowledgement mismatch")
        if ack != r.get("emissions"): errors.append(f"{label}: emission/ack mismatch")
        if effects != (1 if case=="positive" else 0): errors.append(f"{label}: independent effect event count mismatch")
        if case=="positive":
            before,after=r.get("initial_state",{}),r.get("after_state",{})
            if before.get("counter")!=0 or after.get("counter")!=1 or after.get("version")!=before.get("version",0)+1: errors.append(f"{label}: expected exact 0-to-1 visible effect")
            if after.get("frame_sha256")==before.get("frame_sha256"): errors.append(f"{label}: visible frame unchanged")
        elif case=="no_effect":
            if ack!=1 or r.get("emissions")!=1 or r.get("after_state",{}).get("counter")!=0: errors.append(f"{label}: no-effect acknowledgement control invalid")
        else:
            if ack or r.get("emissions") or r.get("after_state",{}).get("counter") not in (0,None): errors.append(f"{label}: negative control emitted or caused effect")
        if case=="stale_version" and r.get("current_state",{}).get("version")==r.get("initial_state",{}).get("version"): errors.append(f"{label}: stale version was not changed")
        if case=="target_replaced" and r.get("current_state",{}).get("pid")==r.get("initial_state",{}).get("pid"): errors.append(f"{label}: process incarnation did not change")
        if case=="unavailable" and r.get("current_state",{}).get("status")!="unavailable": errors.append(f"{label}: unavailable target not established")
        if case=="ambiguous":
            setup=r.get("ambiguous_setup",{})
            if r.get("current_state",{}).get("status")!="ambiguous": errors.append(f"{label}: ambiguity not established")
            if setup.get("status")!="ambiguous" or setup.get("count")!=2: errors.append(f"{label}: two-target setup not established")
            if len(set(setup.get("ready_pids",[])))!=2 or len(set(t.get("xid") for t in setup.get("targets",[])))!=2:
                errors.append(f"{label}: ready process/window identities not distinct")
            if r.get("emissions") or r.get("after_state",{}).get("status")!="ambiguous":
                errors.append(f"{label}: action/effect occurred during established ambiguity")
        if r.get("arm") in {"proxy_image","hybrid"}:
            p=r.get("presentation",{}).get("proxy_image")
            if not p: errors.append(f"{label}: proxy image missing")
            elif check_files:
                path=ROOT/p
                if not path.is_file() or digest(path.read_bytes())!=r["presentation"].get("proxy_sha256"): errors.append(f"{label}: proxy image hash mismatch")
        for state_key in ("initial_state","current_state","after_state"):
            s=r.get(state_key,{})
            if s.get("status")=="ok" and check_files:
                if s.get("width",0)<=0 or s.get("height",0)<=0 or s.get("frame_bytes",0)<=0: errors.append(f"{label}: invalid frame dimensions {state_key}")
                path=ROOT/s.get("frame_path","")
                if not path.is_file(): errors.append(f"{label}: missing frame {state_key}")
                else:
                    data=path.read_bytes()
                    if len(data)!=s.get("frame_bytes") or digest(data)!=s.get("frame_sha256"): errors.append(f"{label}: frame hash/length mismatch {state_key}")
    return errors


def challenge(raw):
    results=[]
    mutators=(
        ("row-removed",lambda x:x["rows"].pop()),
        ("effect-forged",lambda x:x["rows"][0]["fixture_events"].append({"kind":"effect"})),
        ("stale-admitted",lambda x: next(r for r in x["rows"] if r["case"]=="stale_version").update(emissions=1)),
        ("ack-as-success",lambda x: next(r for r in x["rows"] if r["case"]=="no_effect").update(decision="COMPLETED")),
    )
    for name,mutate in mutators:
        copyraw=copy.deepcopy(raw); mutate(copyraw); results.append({"name":name,"detected":bool(validate(copyraw,False))})
    return results


def main():
    raw_bytes=(ROOT/"raw.json").read_bytes(); raw=json.loads(raw_bytes)
    errors=validate(raw)
    if raw.get("allocation_id")!="issue3626-proxy-effect-unit-formal-03" or raw.get("issue")!=3626: errors.append("allocation identity mismatch")
    payload=dict(raw); claimed=payload.pop("result_sha256",None)
    if digest(json.dumps(payload,sort_keys=True,separators=(",",":")).encode())!=claimed: errors.append("raw result self-hash mismatch")
    freeze_bytes=Path("/freeze.json").read_bytes()
    manifest_bytes=Path("/source_manifest.json").read_bytes()
    prereg_bytes=Path("/preregistration.md").read_bytes()
    freeze=json.loads(freeze_bytes); manifest=json.loads(manifest_bytes)
    if digest(freeze_bytes)!=raw.get("freeze_sha256"): errors.append("freeze hash binding mismatch")
    if digest(manifest_bytes)!=raw.get("source_manifest_sha256"): errors.append("source manifest hash binding mismatch")
    if digest(prereg_bytes)!=raw.get("preregistration_sha256"): errors.append("preregistration hash binding mismatch")
    if freeze.get("source_commit")!=raw.get("source_commit"): errors.append("source commit mismatch")
    if freeze.get("preregistration_sha256")!=digest(prereg_bytes): errors.append("freeze/preregistration binding mismatch")
    if freeze.get("image_id")!=raw.get("image_id"): errors.append("image identity mismatch")
    for rel, expected in manifest.get("files",{}).items():
        path=Path("/src")/rel
        if not path.is_file() or digest(path.read_bytes())!=expected: errors.append(f"source hash mismatch: {rel}")
    challenges=challenge(raw)
    if not all(x["detected"] for x in challenges): errors.append("corruption challenge escaped")
    result={"decision":"PASS_PROXY_BINDING_EFFECT_UNIT" if not errors else "HOLD_OR_FAIL_PROXY_BINDING_EFFECT_UNIT",
            "row_count":len(raw.get("rows",[])),"raw_sha256":digest(raw_bytes),"errors":errors,"corruption_controls":challenges}
    (OUT/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
    if errors: raise SystemExit(1)


if __name__=="__main__":main()
