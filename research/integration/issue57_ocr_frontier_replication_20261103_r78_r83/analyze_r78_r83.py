#!/usr/bin/env python3
"""Audit r78-r83 raw results without excluding a failed gate."""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def arm(name, condition):
    root = ROOT / name
    result = read(root / "result.json")
    compiled = read(root / "compiled-result.json")
    close = read(root / "close.json")
    verified = read(root / "verify-task.json")
    artifact = read(root / "artifact-read-before-close.json")
    ocr = [read(p) for p in sorted((root / "server-output").rglob("calc-ocr/*.json"))]
    deps = [read(p) for p in sorted((root / "server-output").rglob("*-input_dependency.json"))]
    by_key = defaultdict(list)
    for row in ocr:
        by_key[(row.get("sequence"), row.get("artifact_sha256"))].append(row)
    joined=[]
    for dep in deps:
        key=(dep.get("observation_sequence"),dep.get("evidence_digest"))
        rows=by_key.get(key,[])
        if len(rows)!=1:
            joined.append({"key":list(key),"match_count":len(rows),"valid":False})
            continue
        row=rows[0]
        joined.append({"action":dep.get("action"),"sequence":key[0],
            "ocr_invoked":row.get("ocr_invoked"),"ocr_status":row.get("ocr_status"),
            "valid":dep.get("eligible") is True and
                ((condition=="always" and row.get("ocr_invoked") is True) or
                 (condition=="skip" and
                  ((dep.get("action")=="enter" and row.get("ocr_invoked") is False) or
                   (dep.get("action")=="save" and row.get("ocr_invoked") is True))))})
    transitions=compiled.get("method_receipt",{}).get("transitions",[])
    lifecycle=close.get("calc_target_lifecycle",[])
    target_exit=lifecycle[0].get("target_process_exit_receipt",{}) if lifecycle else {}
    cleanup=lifecycle[0].get("process_group_cleanup",{}) if lifecycle else {}
    counts=Counter(row.get("ocr_invoked") for row in ocr)
    ocr_ms=sum((r["ended_ns"]-r["started_ns"])/1e6 for r in ocr
        if r.get("ocr_invoked") is True and type(r.get("ended_ns")) is int
        and type(r.get("started_ns")) is int)
    task_values=artifact.get("cells",{})
    return {"arm":name,"condition":condition,
        "docker_exit_code":read(root/"docker-exit-code.json")["exit_code"],
        "preclose_artifact_status":artifact.get("status"),
        "preclose_cells":task_values,
        "preclose_task_success":artifact.get("task_success"),
        "graph_outcome":compiled.get("method_receipt",{}).get("outcome"),
        "graph_reason":compiled.get("method_receipt",{}).get("reason"),
        "graph_completed_transitions":len(transitions),
        "transition_releases":[t.get("release_verified") for t in transitions],
        "close_release_confirmed":close.get("release_confirmed"),
        "close_keys_down":close.get("release",{}).get("keys_down"),
        "close_buttons_down":close.get("release",{}).get("buttons_down"),
        "owner_exit_code":close.get("owner_process_exitcode"),
        "parent_verify_status":verified.get("status"),
        "parent_verify_reason":verified.get("task_effect",{}).get("reason"),
        "target_exit_status":target_exit.get("status"),
        "target_exit_reason":target_exit.get("reason"),
        "cleanup_status":cleanup.get("status"),
        "cleanup_verified_empty":cleanup.get("verified_empty"),
        "clean_exit_verified":cleanup.get("clean_exit_verified"),
        "guard_dependencies":len(deps),"ocr_record_count":len(ocr),
        "ocr_invoked_count":counts[True],"ocr_skipped_count":counts[False],
        "ocr_elapsed_ms":round(ocr_ms,3),
        "profile_elapsed_ms":round(compiled.get("method_receipt",{}).get("elapsed_ns",0)/1e6,3),
        "guard_join_valid":len(joined)==len(deps) and all(r["valid"] for r in joined),
        "guard_join":joined,
        "arm_gate_pass":(read(root/"docker-exit-code.json")["exit_code"]==0 and
            verified.get("status")=="verified" and verified.get("task_success") is True and
            task_values=={"A1":"731","A2":"864"} and
            all(t.get("release_verified") is True for t in transitions) and
            close.get("release_confirmed") is True and
            close.get("release",{}).get("keys_down")==[] and
            close.get("release",{}).get("buttons_down")==[] and
            target_exit.get("verified") is True and target_exit.get("exit_code")==0 and
            cleanup.get("clean_exit_verified") is True and
            len(joined)==14 and all(r["valid"] for r in joined))}

summary={"schema":"agent-interface/postclose-ocr-replication-audit-v1",
 "arms":[arm("r78-b5","always"),arm("r79-a5","skip"),arm("r80-a6","skip"),arm("r81-b6","always"),arm("r82-b7","always"),arm("r83-a7","skip")],
 "interpretation":"Both arm gates are evaluated as frozen; no failed task/exit is excluded.",
 "block_gate_pass":False}
summary["block_gate_pass"]=all(a["arm_gate_pass"] for a in summary["arms"])
pairs=[("block1","r78-b5","r79-a5"),("block2","r80-a6","r81-b6"),("block3","r82-b7","r83-a7")]
by_name={a["arm"]:a for a in summary["arms"]}
summary["pairs"]=[]
for label,full,skip in pairs:
 f,s=by_name[full],by_name[skip]
 summary["pairs"].append({"pair":label,"full_arm":full,"skip_arm":skip,
   "both_functional_gates_pass":f["arm_gate_pass"] and s["arm_gate_pass"],
   "full_ocr_calls":f["ocr_invoked_count"],"skip_ocr_calls":s["ocr_invoked_count"],
   "full_ocr_elapsed_ms":f["ocr_elapsed_ms"],"skip_ocr_elapsed_ms":s["ocr_elapsed_ms"],
   "full_profile_elapsed_ms":f["profile_elapsed_ms"],"skip_profile_elapsed_ms":s["profile_elapsed_ms"]})
(ROOT/"analysis.json").write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
print(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False))
