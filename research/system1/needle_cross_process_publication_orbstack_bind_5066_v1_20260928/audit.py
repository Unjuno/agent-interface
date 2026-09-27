"""Independent raw/receipt auditor; imports neither runner nor protocol."""
from __future__ import annotations

import copy
import base64
import hashlib
import json
import os
from pathlib import Path
import sys

OUT = Path("/out")
OLD_SHA = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
OLD, NEW, READERS, PHASES = 3788, 3789, 4, 7


def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def blob_id(data: bytes) -> str: return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def reconstructed(row: object):
    if not isinstance(row,dict): return None
    try: data=base64.b64decode(row["raw_b64"],validate=True)
    except Exception: return None
    if len(data)!=row.get("bytes") or digest(data)!=row.get("raw_sha256"): return None
    try: obj=json.loads(data)
    except Exception: return {"raw":data,"object":None,"valid":False}
    body={k:v for k,v in obj.items() if k!="payload_sha256"} if isinstance(obj,dict) else None
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode() if body is not None else b""
    correct=isinstance(obj,dict) and obj.get("payload_sha256")==digest(canonical) and isinstance(obj.get("generation"),int)
    if row.get("parse_ok") is not True or row.get("generation")!=obj.get("generation") or row.get("embedded_digest")!=obj.get("payload_sha256") or row.get("valid") is not correct:
        return None
    return {"raw":data,"object":obj,"valid":correct}


def audit(raw: object, receipt: object) -> list[str]:
    e = []
    if not isinstance(raw, dict) or not isinstance(receipt, dict): return ["input_not_object"]
    top = {"allocation":"needle-publication-orbstack-bind-5066-20260928-01","issue":5073,
           "formal_invocations":1,"image_id":IMAGE,"input_sha256":OLD_SHA,"input_bytes":15279,
           "input_git_blob":"45b80150dac503f4eb6f3cb5d82f9afa2c587107","platform_prefix":"linux/arm64",
           "dispatch_count":0,"authority_granted":False}
    for k,v in top.items():
        actual = str(raw.get("platform","")).startswith(v) if k == "platform_prefix" else raw.get(k)
        if actual != v: e.append("raw_"+k)
    for k in ("source_commit","source_tree_sha","freeze_sha256","source_sha256","source_blob_sha256","image_id","mounts","docker_argv"):
        if raw.get(k) != receipt.get(k): e.append("receipt_binding_"+k)
    if receipt.get("construction") != "0" or raw.get("construction") != "0": e.append("construction_flag")
    if receipt.get("environment") != {"OBSTAC_SOURCE_COMMIT":raw.get("source_commit"),"OBSTAC_IMAGE_ID":IMAGE,
                                         "OBSTAC_FREEZE_SHA256":raw.get("freeze_sha256"),"OBSTAC_CONSTRUCTION":"0"}:
        e.append("receipt_environment")
    for key, env_name in (("source_commit","OBSTAC_SOURCE_COMMIT"),("image_id","OBSTAC_IMAGE_ID"),
                          ("freeze_sha256","OBSTAC_FREEZE_SHA256"),("construction","OBSTAC_CONSTRUCTION")):
        if os.environ.get(env_name)!=receipt.get(key): e.append("process_environment_"+key)
    if receipt.get("image_platform")!="linux/arm64" or receipt.get("docker_context")!="orbstack":
        e.append("platform_or_context")
    if receipt.get("resource_limits")!={"cpus":"0.25","memory":"512m","pids":32,"network":"none",
          "root_read_only":True,"source_read_only":True,"cap_drop":"ALL","no_new_privileges":True}:
        e.append("resource_limits")
    for rel, expected in receipt.get("source_sha256",{}).items():
        path=Path("/src")/rel
        try: source_bytes=path.read_bytes()
        except OSError: e.append("source_missing_"+rel); continue
        if digest(source_bytes)!=expected: e.append("source_sha256_"+rel)
        if blob_id(source_bytes)!=receipt.get("source_blob_sha256",{}).get(rel): e.append("source_blob_"+rel)
    seed_path=Path("/src/research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json")
    try: seed_raw=seed_path.read_bytes()
    except OSError: seed_raw=b""
    if digest(seed_raw)!=OLD_SHA or blob_id(seed_raw)!="45b80150dac503f4eb6f3cb5d82f9afa2c587107": e.append("seed_raw_bytes")
    mounts = receipt.get("mounts")
    if not isinstance(mounts,list): e.append("mount_inventory")
    else:
        by_target={m.get("Destination"):m for m in mounts if isinstance(m,dict)}
        if set(by_target) != {"/src","/out"}: e.append("mount_targets")
        else:
            if by_target["/src"].get("RW") is not False or by_target["/src"].get("Source") != receipt.get("source_mount"):
                e.append("source_mount_identity")
            if by_target["/out"].get("RW") is not True or by_target["/out"].get("Source") != receipt.get("output_mount"):
                e.append("output_mount_identity")
    finfo=receipt.get("formal_container_inspect",{})
    if finfo.get("ConfigImage")!=IMAGE or finfo.get("Image")!=IMAGE or finfo.get("State",{}).get("ExitCode")!=0 or finfo.get("State",{}).get("Status")!="exited":
        e.append("formal_container_state_or_image")
    if finfo.get("Id") is None or finfo.get("Image") is None: e.append("formal_container_identity")
    try:
        freeze_bytes=Path("/src/research/system1/needle_cross_process_publication_orbstack_bind_5066_v1_20260928/FREEZE.json").read_bytes()
        if digest(freeze_bytes)!=receipt.get("freeze_sha256"): e.append("freeze_file_hash")
    except OSError:
        e.append("freeze_file_missing")
    actual_mounts=finfo.get("Mounts",[])
    if not isinstance(actual_mounts,list): e.append("formal_actual_mounts")
    else:
        actual={m.get("Destination"):m for m in actual_mounts if isinstance(m,dict)}
        if set(actual)!={"/src","/out"}: e.append("formal_actual_mount_targets")
        else:
            for target in ("/src","/out"):
                wanted=next((m for m in receipt.get("mounts",[]) if m.get("Destination")==target),{})
                if actual[target].get("Source")!=wanted.get("Source") or bool(actual[target].get("RW"))!=wanted.get("RW"):
                    e.append("formal_actual_mount_"+target)
    for name, arm, prefix in (("atomic",raw.get("atomic",{}),"phase_"),("unsafe",raw.get("unsafe",{}),"phase_")):
        roster=arm.get("reader_pids")
        if not isinstance(roster,list) or len(roster)!=READERS or len(set(roster))!=READERS:
            e.append(name+"_pid_roster"); continue
        if arm.get("publisher_pid") in roster: e.append(name+"_publisher_collision")
        if arm.get("exit_codes") != [0]*READERS: e.append(name+"_reader_exits")
        rows=arm.get("rows")
        if not isinstance(rows,list) or len(rows)!=PHASES*READERS:
            e.append(name+"_row_count"); continue
        seen=set()
        for row in rows:
            if not isinstance(row,dict): e.append(name+"_row_type"); continue
            phase, reader=row.get("phase"),row.get("reader")
            if not isinstance(phase,str) or not phase.startswith(prefix) or reader not in range(READERS):
                e.append(name+"_phase_reader"); continue
            key=(phase,reader)
            if key in seen: e.append(name+"_duplicate")
            seen.add(key)
            if row.get("pid")!=roster[reader]: e.append(name+"_pid_binding")
            if name=="atomic":
                expected_held_sha=raw.get("old_raw_sha256") if phase=="phase_1" else raw.get("candidate_raw_sha256")
                expected_held_gen=OLD if phase=="phase_1" else NEW
                if not (row.get("fd_open_ns",0)<row.get("replace_start_ns",0)<row.get("replace_return_ns",0)<row.get("fd_read_end_ns",0)):
                    e.append("fd_partial_order_"+phase)
                held=row.get("held",{})
                held_rebuilt=reconstructed(held)
                if held_rebuilt is None: e.append("atomic_raw_reconstruction_"+phase)
                if held.get("raw_sha256")!=expected_held_sha or held.get("generation")!=expected_held_gen or held.get("valid") is not True:
                    e.append("held_descriptor_bytes_"+phase)
            else:
                partial=row.get("partial",{}); complete=row.get("complete",{})
                partial_rebuilt=reconstructed(partial); complete_rebuilt=reconstructed(complete)
                if partial_rebuilt is None or complete_rebuilt is None: e.append("unsafe_raw_reconstruction_"+phase)
                if not (row.get("write_start_ns",0)<=row.get("partial_start_ns",0)<=row.get("partial_end_ns",0)<=row.get("write_end_ns",0)):
                    e.append("partial_window_order_"+phase)
                if partial.get("valid") is not False or not (0<partial.get("bytes",0)<raw.get("candidate_bytes",0)):
                    e.append("partial_bytes_"+phase)
                if complete.get("raw_sha256")!=raw.get("candidate_raw_sha256") or complete.get("valid") is not True or complete.get("generation")!=NEW:
                    e.append("completed_bytes_"+phase)
        if seen!={(f"phase_{n}",i) for n in range(1,PHASES+1) for i in range(READERS)}: e.append(name+"_schedule")
    atomic=raw.get("atomic",{}); post=atomic.get("post_rows")
    if not isinstance(post,list) or len(post)!=PHASES*READERS:
        e.append("post_read_denominator")
    else:
        post_seen=set()
        for row in post:
            if not isinstance(row,dict): e.append("post_row_type");continue
            key=(row.get("phase"),row.get("reader"))
            if key in post_seen:e.append("post_duplicate")
            post_seen.add(key)
            if row.get("reader") not in range(READERS) or row.get("pid")!=atomic.get("reader_pids",[])[row.get("reader",-1)]:
                e.append("post_pid_binding")
            rebuilt=reconstructed(row.get("path",{})); path=row.get("path",{})
            if rebuilt is None or path.get("raw_sha256")!=raw.get("candidate_raw_sha256") or path.get("generation")!=NEW or path.get("valid") is not True:
                e.append("post_path_bytes")
            if not (row.get("replace_return_ns",0)<=row.get("path_read_start_ns",0)<=row.get("path_read_end_ns",0)):
                e.append("fresh_path_order")
        if post_seen!={(f"phase_{n}",i) for n in range(1,PHASES+1) for i in range(READERS)}:
            e.append("post_schedule")
        phases={r.get("phase"):r.get("replace_return_ns") for r in atomic.get("rows",[]) if isinstance(r,dict)}
        for row in post:
            if phases.get(row.get("phase"))!=row.get("replace_return_ns"):e.append("post_phase_binding")
    replacements=atomic.get("replacement_intervals")
    if not isinstance(replacements,list) or len(replacements)!=PHASES: e.append("replacement_count")
    else:
        by_phase={x.get("phase"):x for x in replacements if isinstance(x,dict)}
        for row in atomic.get("rows",[]):
            interval=by_phase.get(row.get("phase"),{})
            if row.get("replace_start_ns")!=interval.get("replace_start_ns") or row.get("replace_return_ns")!=interval.get("replace_return_ns"):
                e.append("replacement_receipt_binding")
    reject=raw.get("rejection_gate",{})
    if reject.get("before_sha256")!=reject.get("after_sha256") or reject.get("before_sha256")!=raw.get("candidate_raw_sha256") or reject.get("invalid_accepted") is not False or reject.get("stale_disposition")!="YIELD_STALE_GENERATION":
        e.append("invalid_stale_preservation")
    invalid=reconstructed(reject.get("invalid_proposal",{}))
    if invalid is None or invalid["valid"] is not False or invalid["object"].get("generation")!=NEW:
        e.append("invalid_candidate_raw")
    if reject.get("stale_proposal_generation")!=OLD or reject.get("active_generation")!=NEW or reject.get("stale_disposition")!=("YIELD_STALE_GENERATION" if reject.get("stale_proposal_generation")!=reject.get("active_generation") else "ELIGIBLE_PROPOSAL_ONLY"):
        e.append("stale_candidate_recomputed")
    return e


def mutations(raw,receipt):
    tests={}
    x=copy.deepcopy(raw); x["dispatch_count"]=1; tests["dispatch"]= (x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["rows"].pop(); tests["missing_row"]=(x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["rows"][0]["replace_return_ns"]=0; tests["fd_order"]=(x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["post_rows"][0]["path"]["raw_sha256"]="0"*64; tests["wrong_path_bytes"]=(x,receipt)
    x=copy.deepcopy(raw); x["unsafe"]["rows"][0]["partial"]["valid"]=True; tests["partial_claimed_valid"]=(x,receipt)
    x=copy.deepcopy(receipt); x["mounts"][0]["RW"]=True; tests["writable_source"]=(raw,x)
    return {n:bool(audit(r,c)) for n,(r,c) in tests.items()}


def main():
    raw_path=OUT/"raw.json"; receipt_path=OUT/"invocation_receipt.json"
    raw=json.loads(raw_path.read_text()); receipt=json.loads(receipt_path.read_text())
    errors=audit(raw,receipt); controls=mutations(raw,receipt)
    report={"status":"PASS_ORBSTACK_CROSS_PROCESS_PUBLICATION_SCOPED" if not errors and all(controls.values()) else "STOP_PROVENANCE_ENVIRONMENT_OR_AUDIT",
            "errors":errors,"corruption_controls":controls,"raw_sha256":digest(raw_path.read_bytes()),
            "receipt_sha256":digest(receipt_path.read_bytes()),"atomic_rows":28,"unsafe_rows":28,"post_rows":28}
    (OUT/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__=="__main__": raise SystemExit(main())
