"""Independent raw/receipt auditor; imports neither runner nor protocol."""
from __future__ import annotations

import copy
import base64
import hashlib
import json
import os
from pathlib import Path
import sys

INPUT = Path("/in")
OUT = Path("/out")
EXP = Path(__file__).resolve().parent
EXP_REL = "research/system1/needle_cross_process_publication_orbstack_bind_5066_v3_20260928"
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
    except Exception:
        if row.get("parse_ok") is not False or row.get("generation") is not None or row.get("valid") is not False:return None
        return {"raw":data,"object":None,"valid":False}
    if not isinstance(obj,dict):return None
    body={k:v for k,v in obj.items() if k!="payload_sha256"}
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    correct=obj.get("payload_sha256")==digest(canonical) and isinstance(obj.get("generation"),int)
    if row.get("parse_ok") is not True or row.get("generation")!=obj.get("generation") or row.get("embedded_digest")!=obj.get("payload_sha256") or row.get("valid") is not correct:
        return None
    return {"raw":data,"object":obj,"valid":correct}


def expected_candidate(seed:dict,generation:int)->bytes:
    obj=copy.deepcopy(seed);obj["generation"]=generation
    if not isinstance(obj.get("provenance"),dict):return b""
    obj["provenance"]=dict(obj["provenance"])
    obj["provenance"]["allocation"]="needle-publication-orbstack-bind-5066-20260928-03"
    obj["provenance"]["predecessor_issue"]=3890
    body={k:v for k,v in obj.items() if k!="payload_sha256"}
    obj["payload_sha256"]=digest(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def exact_raw_matches(row:object,expected:bytes)->bool:
    rebuilt=reconstructed(row)
    return rebuilt is not None and rebuilt["raw"]==expected


def unsafe_completion_errors(row:dict,interval:dict)->list[str]:
    errors=[]
    if row.get("phase")!=interval.get("phase"):
        errors.append("phase")
    if row.get("write_start_ns")!=interval.get("start_ns") or row.get("write_end_ns")!=interval.get("end_ns"):
        errors.append("interval_binding")
    times=[row.get(k) for k in ("write_start_ns","partial_start_ns","partial_end_ns","write_end_ns","complete_start_ns","complete_end_ns")]
    if any(not isinstance(value,int) or isinstance(value,bool) for value in times) or times!=sorted(times):
        errors.append("completion_order")
    return errors


def fd_read_order_errors(row:dict,phase:str)->list[str]:
    fields=("fd_open_ns","replace_start_ns","replace_return_ns","fd_read_start_ns","fd_read_end_ns")
    values=[row.get(key) for key in fields]
    if any(not isinstance(value,int) or isinstance(value,bool) for value in values):
        return ["fd_timestamps_missing_"+phase]
    if values!=sorted(values) or len(set(values))!=len(values):
        return ["fd_partial_order_"+phase]
    return []


def expected_docker_argv(receipt:dict,entrypoint:str)->list[str]:
    """Reconstruct the exact formal/audit command from the host receipt fields."""
    name_key="formal_container_name" if entrypoint=="runner" else "auditor_container_name"
    env=receipt.get("environment",{})
    common=["--pull=never","--platform","linux/arm64","--network","none","--read-only","--cpus","0.25",
            "--memory","512m","--pids-limit","32","--shm-size","32m","--cap-drop","ALL",
            "--security-opt","no-new-privileges","--mount",
            f"type=bind,source={receipt.get('source_mount')},target=/src,readonly"]
    if entrypoint=="runner":
        common += ["--mount",f"type=bind,source={receipt.get('output_mount')},target=/out"]
    else:
        common += ["--mount",f"type=bind,source={receipt.get('audit_input_mount')},target=/in,readonly",
                   "--mount",f"type=bind,source={receipt.get('audit_output_mount')},target=/out"]
    envargs=[v for k in ("OBSTAC_SOURCE_COMMIT","OBSTAC_IMAGE_ID","OBSTAC_FREEZE_SHA256","OBSTAC_CONSTRUCTION")
             for v in ("-e",f"{k}={env.get(k)}")]
    return ["docker","--context","orbstack","run","--name",receipt.get(name_key),*common,*envargs,
            IMAGE,"python","-B",f"/src/{EXP_REL}/{entrypoint}.py"]


def provenance_errors(raw:object,receipt:object,experiment_root:Path|None=None,input_root:Path|None=None)->list[str]:
    """Check the raw/receipt/source contract without importing the candidate runner."""
    if not isinstance(raw,dict) or not isinstance(receipt,dict):return ["input_not_object"]
    root=Path(experiment_root) if experiment_root is not None else EXP
    errors=[]
    expected={"allocation":"needle-publication-orbstack-bind-5066-20260928-03","issue":5134,
              "formal_invocations":1,"image_id":IMAGE,"input_sha256":OLD_SHA,"input_bytes":15279,
              "input_git_blob":"45b80150dac503f4eb6f3cb5d82f9afa2c587107",
              "dispatch_count":0,"authority_granted":False}
    for key,value in expected.items():
        if raw.get(key)!=value:errors.append("raw_"+key)
    if not str(raw.get("platform","" )).startswith("linux/arm64"):
        errors.append("raw_platform_prefix")
    for key in ("source_commit","live_main_sha","source_tree_sha","freeze_sha256","source_sha256",
                "source_blob_sha256","image_id","mounts"):
        if raw.get(key)!=receipt.get(key):errors.append("receipt_binding_"+key)
    try:freeze=json.loads((root/"FREEZE.json").read_bytes())
    except (OSError,ValueError):freeze={}
    frozen_sources=freeze.get("source_sha256",{}) if isinstance(freeze,dict) else {}
    if not isinstance(frozen_sources,dict) or not frozen_sources:
        errors.append("freeze_source_inventory")
    else:
        if experiment_root is None and receipt.get("source_sha256")!=frozen_sources:errors.append("receipt_source_inventory")
        for rel,digest_expected in frozen_sources.items():
            if experiment_root is not None:
                try: digest_expected=digest((root/rel).read_bytes())
                except OSError: errors.append("source_missing_"+rel);continue
            try:source_bytes=(root/rel).read_bytes()
            except OSError:errors.append("source_missing_"+rel);continue
            if digest(source_bytes)!=digest_expected:errors.append("source_sha256_"+rel)
            if blob_id(source_bytes)!=receipt.get("source_blob_sha256",{}).get(rel):errors.append("source_blob_"+rel)
    try:seed_raw=(root.parents[2]/"research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json").read_bytes()
    except OSError:seed_raw=b""
    if digest(seed_raw)!=OLD_SHA or blob_id(seed_raw)!="45b80150dac503f4eb6f3cb5d82f9afa2c587107":
        errors.append("seed_raw_bytes")
    for field,entrypoint in (("docker_argv","runner"),("auditor_docker_argv","audit")):
        if field in receipt and receipt.get(field)!=expected_docker_argv(receipt,entrypoint):errors.append("receipt_"+field)
    if input_root is not None:
        input_root=Path(input_root)
        try: manifest=json.loads((input_root/"input_manifest.json").read_bytes())
        except (OSError,ValueError): manifest={}
        expected_files={}
        for name,value in (("raw.json",raw),("invocation_receipt.json",receipt)):
            path=input_root/name
            try: contents=path.read_bytes()
            except OSError: errors.append("audit_input_missing_"+name); continue
            if contents!=json.dumps(value,sort_keys=True,indent=2).encode()+b"\n":
                errors.append("audit_input_content_"+name)
            expected_files[name]=digest(contents)
        if not isinstance(manifest,dict) or manifest.get("files")!=expected_files:
            errors.append("audit_input_manifest")
        auditor_mounts=receipt.get("auditor_mounts")
        if not isinstance(auditor_mounts,list): errors.append("auditor_mount_inventory")
        else:
            by_target={m.get("Destination"):m for m in auditor_mounts if isinstance(m,dict)}
            if set(by_target)!={"/src","/in","/out"}: errors.append("auditor_mount_targets")
            else:
                for target,source,rw in (("/src",receipt.get("source_mount"),False),
                                         ("/in",receipt.get("audit_input_mount"),False),
                                         ("/out",receipt.get("audit_output_mount"),True)):
                    if by_target[target].get("Source")!=source or by_target[target].get("RW") is not rw:
                        errors.append("auditor_mount_"+target)
    if receipt.get("image_platform")!="linux/arm64" or receipt.get("docker_context")!="orbstack":
        errors.append("platform_or_context")
    if receipt.get("construction")!="0" or raw.get("construction")!="0":errors.append("construction_flag")
    expected_env={"OBSTAC_SOURCE_COMMIT":raw.get("source_commit"),"OBSTAC_IMAGE_ID":IMAGE,
                  "OBSTAC_FREEZE_SHA256":raw.get("freeze_sha256"),"OBSTAC_CONSTRUCTION":"0"}
    if receipt.get("environment")!=expected_env:errors.append("receipt_environment")
    for key,env_name in (("source_commit","OBSTAC_SOURCE_COMMIT"),("image_id","OBSTAC_IMAGE_ID"),
                         ("freeze_sha256","OBSTAC_FREEZE_SHA256"),("construction","OBSTAC_CONSTRUCTION")):
        if os.environ.get(env_name)!=receipt.get(key):errors.append("process_environment_"+key)
    return errors


def audit(raw: object, receipt: object, input_root:Path|None=None) -> list[str]:
    e = []
    if not isinstance(raw, dict) or not isinstance(receipt, dict): return ["input_not_object"]
    e.extend(provenance_errors(raw,receipt,input_root=input_root))
    if receipt.get("resource_limits")!={"cpus":"0.25","memory":"512m","pids":32,"network":"none",
          "root_read_only":True,"source_read_only":True,"cap_drop":"ALL","no_new_privileges":True}:
        e.append("resource_limits")
    for rel, expected in receipt.get("source_sha256",{}).items():
        path=EXP/rel
        try: source_bytes=path.read_bytes()
        except OSError: e.append("source_missing_"+rel); continue
        if digest(source_bytes)!=expected: e.append("source_sha256_"+rel)
        if blob_id(source_bytes)!=receipt.get("source_blob_sha256",{}).get(rel): e.append("source_blob_"+rel)
    seed_path=EXP.parents[2]/"research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
    try: seed_raw=seed_path.read_bytes()
    except OSError: seed_raw=b""
    if digest(seed_raw)!=OLD_SHA or blob_id(seed_raw)!="45b80150dac503f4eb6f3cb5d82f9afa2c587107": e.append("seed_raw_bytes")
    try: seed=json.loads(seed_raw)
    except Exception: seed={}
    expected={g:expected_candidate(seed,g) for g in range(NEW,NEW+PHASES)} if isinstance(seed,dict) else {}
    final_expected=expected.get(NEW+PHASES-1,b"")
    if raw.get("old_digest")!=(seed.get("payload_sha256") if isinstance(seed,dict) else None):e.append("old_payload_digest")
    if raw.get("candidate_raw_sha256")!=digest(final_expected) or raw.get("candidate_bytes")!=len(final_expected):e.append("final_candidate_identity")
    try: final_digest=json.loads(final_expected).get("payload_sha256")
    except Exception: final_digest=None
    if raw.get("candidate_digest")!=final_digest:e.append("final_candidate_digest")
    registry=raw.get("candidate_registry")
    if not isinstance(registry,list) or len(registry)!=PHASES:e.append("candidate_registry_count")
    else:
        for i,entry in enumerate(registry):
            if not isinstance(entry,dict):e.append("candidate_registry_entry_type");continue
            gen=NEW+i; candidate=expected.get(gen,b"")
            if entry.get("generation")!=gen or entry.get("raw_sha256")!=digest(candidate) or entry.get("bytes")!=len(candidate):
                e.append("candidate_registry_"+str(gen))
            try: obj=json.loads(candidate)
            except Exception: obj={}
            if entry.get("payload_sha256")!=obj.get("payload_sha256"):e.append("candidate_digest_"+str(gen))
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
        freeze_bytes=(EXP/"FREEZE.json").read_bytes()
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
        unsafe_intervals={}
        if name=="unsafe":
            intervals=arm.get("write_intervals")
            if not isinstance(intervals,list) or len(intervals)!=PHASES:
                e.append("unsafe_write_interval_count")
            else:
                for interval in intervals:
                    if not isinstance(interval,dict) or interval.get("phase") in unsafe_intervals:
                        e.append("unsafe_write_interval_identity");continue
                    unsafe_intervals[interval.get("phase")]=interval
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
                phase_number=int(phase.split("_")[-1]) if phase.startswith("phase_") else 0
                expected_held=seed_raw if phase_number==1 else expected.get(NEW+phase_number-2,b"")
                expected_target=expected.get(NEW+phase_number-1,b"")
                expected_held_sha=digest(expected_held);expected_held_gen=OLD+phase_number-1
                e.extend(fd_read_order_errors(row,phase))
                held=row.get("held",{})
                held_rebuilt=reconstructed(held)
                if held_rebuilt is None: e.append("atomic_raw_reconstruction_"+phase)
                if held.get("raw_sha256")!=expected_held_sha or held.get("generation")!=expected_held_gen or held.get("valid") is not True or held.get("raw_b64")!=base64.b64encode(expected_held).decode():
                    e.append("held_descriptor_bytes_"+phase)
                if row.get("previous_generation")!=expected_held_gen or row.get("target_generation")!=expected_held_gen+1:
                    e.append("atomic_generation_transition_"+phase)
                pub=row.get("publication",{})
                if pub.get("disposition")!="PUBLISHED" or pub.get("active_before_generation")!=expected_held_gen or pub.get("active_after_generation")!=expected_held_gen+1 or pub.get("before_sha256")!=expected_held_sha or pub.get("after_sha256")!=digest(expected_target) or pub.get("candidate_sha256")!=digest(expected_target) or pub.get("replace_start_ns")!=row.get("replace_start_ns") or pub.get("replace_return_ns")!=row.get("replace_return_ns"):
                    e.append("publication_effect_"+phase)
            else:
                partial=row.get("partial",{}); complete=row.get("complete",{})
                partial_rebuilt=reconstructed(partial); complete_rebuilt=reconstructed(complete)
                if partial_rebuilt is None or complete_rebuilt is None: e.append("unsafe_raw_reconstruction_"+phase)
                if not (row.get("write_start_ns",0)<=row.get("partial_start_ns",0)<=row.get("partial_end_ns",0)<=row.get("write_end_ns",0)):
                    e.append("partial_window_order_"+phase)
                completion_errors=unsafe_completion_errors(row,unsafe_intervals.get(phase,{}))
                for error in completion_errors:e.append("unsafe_completion_"+error+"_"+phase)
                if partial.get("valid") is not False or not (0<partial.get("bytes",0)<raw.get("candidate_bytes",0)):
                    e.append("partial_bytes_"+phase)
                phase_number=int(phase.split("_")[-1]) if phase.startswith("phase_") else 0
                target=expected.get(NEW+phase_number-1,b"")
                if partial_rebuilt is not None and partial_rebuilt.get("raw")!=target[:len(target)//2]:
                    e.append("partial_not_exact_prefix_"+phase)
                if complete.get("raw_sha256")!=digest(target) or complete.get("valid") is not True or complete.get("generation")!=NEW+phase_number-1 or complete.get("raw_b64")!=base64.b64encode(target).decode():
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
            phase_number=int(str(row.get("phase","")).split("_")[-1]) if str(row.get("phase","")).startswith("phase_") else 0
            expected_path=expected.get(NEW+phase_number-1,b"")
            rebuilt=reconstructed(row.get("path",{})); path=row.get("path",{})
            if rebuilt is None or path.get("raw_sha256")!=digest(expected_path) or path.get("generation")!=NEW+phase_number-1 or path.get("valid") is not True or path.get("raw_b64")!=base64.b64encode(expected_path).decode():
                e.append("post_path_bytes")
            if row.get("target_generation")!=NEW+phase_number-1 or row.get("target_raw_sha256")!=digest(expected_path):
                e.append("post_target_identity")
            if not (row.get("replace_return_ns",0)<=row.get("path_read_start_ns",0)<=row.get("path_read_end_ns",0)):
                e.append("fresh_path_order")
            atomic_row=next((x for x in atomic.get("rows",[]) if isinstance(x,dict) and (x.get("phase"),x.get("reader"))==key),{})
            if atomic_row and not (atomic_row.get("fd_read_end_ns",0)<=row.get("path_read_start_ns",0)):
                e.append("descriptor_then_path_order")
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
    invalid_result=reject.get("invalid_result",{});stale_result=reject.get("stale_result",{})
    invalid_bytes=reconstructed(reject.get("invalid_proposal",{}))
    if invalid_result.get("disposition")!="YIELD_INVALID_CANDIDATE" or invalid_result.get("active_before_generation")!=NEW+PHASES-1 or invalid_result.get("active_after_generation")!=NEW+PHASES-1 or invalid_result.get("before_sha256")!=invalid_result.get("after_sha256") or invalid_result.get("before_sha256")!=raw.get("candidate_raw_sha256") or invalid_bytes is None or invalid_result.get("candidate_sha256")!=digest(invalid_bytes["raw"]):
        e.append("invalid_candidate_effect")
    if stale_result.get("disposition")!="YIELD_STALE_GENERATION" or stale_result.get("active_before_generation")!=NEW+PHASES-1 or stale_result.get("active_after_generation")!=NEW+PHASES-1 or stale_result.get("before_sha256")!=stale_result.get("after_sha256") or stale_result.get("before_sha256")!=raw.get("candidate_raw_sha256") or stale_result.get("candidate_sha256")!=digest(expected.get(NEW,b"")):
        e.append("stale_candidate_effect")
    invalid=reconstructed(reject.get("invalid_proposal",{}))
    if invalid is None or invalid["valid"] is not False or invalid["object"].get("generation")!=NEW+PHASES-1:
        e.append("invalid_candidate_raw")
    stale_package=reconstructed(reject.get("stale_proposal",{}).get("package",{}))
    if stale_package is None or stale_package.get("raw")!=expected.get(NEW,b"") or reject.get("stale_proposal",{}).get("base_generation")!=OLD:
        e.append("stale_candidate_recomputed")
    return e


def mutations(raw,receipt):
    tests={}
    x=copy.deepcopy(raw); x["dispatch_count"]=1; tests["dispatch"]= (x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["rows"].pop(); tests["missing_row"]=(x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["rows"][0]["replace_return_ns"]=0; tests["fd_order"]=(x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["rows"][0]["fd_read_start_ns"]=x["atomic"]["rows"][0]["replace_return_ns"]-1; tests["fd_read_start_before_replace_return"]=(x,receipt)
    x=copy.deepcopy(raw); x["atomic"]["post_rows"][0]["path"]["raw_sha256"]="0"*64; tests["wrong_path_bytes"]=(x,receipt)
    x=copy.deepcopy(raw); x["unsafe"]["rows"][0]["partial"]["valid"]=True; tests["partial_claimed_valid"]=(x,receipt)
    x=copy.deepcopy(raw); x["unsafe"]["rows"][0]["complete_start_ns"]=x["unsafe"]["rows"][0]["write_end_ns"]-1; tests["completion_before_writer_end"]=(x,receipt)
    x=copy.deepcopy(raw); x["unsafe"]["rows"][0]["complete_end_ns"]=x["unsafe"]["rows"][0]["complete_start_ns"]-1; tests["completion_timestamp_reversed"]=(x,receipt)
    x=copy.deepcopy(raw); x["unsafe"]["write_intervals"][0]["end_ns"]+=1; tests["wrong_write_interval_binding"]=(x,receipt)
    x=copy.deepcopy(receipt); x["mounts"][0]["RW"]=True; tests["writable_source"]=(raw,x)
    x=copy.deepcopy(raw); item=x["atomic"]["post_rows"][0]["path"]
    package=json.loads(base64.b64decode(item["raw_b64"]));package["provenance"]["allocation"]="unregistered-allocation"
    body={k:v for k,v in package.items() if k!="payload_sha256"}
    package["payload_sha256"]=digest(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
    changed=json.dumps(package,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    item.update({"raw_b64":base64.b64encode(changed).decode(),"bytes":len(changed),"raw_sha256":digest(changed),
                 "parse_ok":True,"valid":True,"generation":package["generation"],"embedded_digest":package["payload_sha256"]})
    tests["wrong_lineage_rehashed"]=(x,receipt)
    return {n:bool(audit(r,c)) for n,(r,c) in tests.items()}


def main():
    raw_path=INPUT/"raw.json"; receipt_path=INPUT/"invocation_receipt.json"
    raw=json.loads(raw_path.read_text()); receipt=json.loads(receipt_path.read_text())
    errors=audit(raw,receipt,INPUT); controls=mutations(raw,receipt)
    report={"status":"PASS_ORBSTACK_CROSS_PROCESS_PUBLICATION_SCOPED" if not errors and all(controls.values()) else "STOP_PROVENANCE_ENVIRONMENT_OR_AUDIT",
            "errors":errors,"corruption_controls":controls,"raw_sha256":digest(raw_path.read_bytes()),
            "receipt_sha256":digest(receipt_path.read_bytes()),"atomic_rows":28,"unsafe_rows":28,"post_rows":28}
    (OUT/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__=="__main__": raise SystemExit(main())
