"""Post-commit audit of frozen V39 source identity and retained raw output."""
import hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def run_git(args):
    return subprocess.run(["git",*args],cwd=ROOT,capture_output=True)

def validate(raw):
    freeze=json.loads((HERE/"FREEZE.json").read_text(encoding="utf-8"))
    inp=json.loads((HERE/"input.json").read_text(encoding="utf-8"))
    src=ROOT/freeze["source_path"]
    frozen=run_git(["show",f"{freeze['source_commit']}:{freeze['source_path']}"])
    frozen_blob=run_git(["rev-parse",f"{freeze['source_commit']}:{freeze['source_path']}"])
    current_blob=run_git(["hash-object",str(src)])
    current_head=run_git(["rev-parse","HEAD"]).stdout.decode().strip()
    ancestor=run_git(["merge-base","--is-ancestor",freeze["source_commit"],"HEAD"])
    checks={
      "frozen_commit_available":frozen.returncode==0 and frozen_blob.returncode==0,
      "frozen_source_hash":frozen.returncode==0 and hashlib.sha256(frozen.stdout).hexdigest()==freeze["source_sha256"],
      "frozen_source_blob":frozen_blob.returncode==0 and frozen_blob.stdout.decode().strip()==freeze["source_git_blob"],
      "current_source_matches_freeze":hashlib.sha256(src.read_bytes()).hexdigest()==freeze["source_sha256"] and current_blob.stdout.decode().strip()==freeze["source_git_blob"],
      "frozen_commit_in_current_history":ancestor.returncode==0,
      "raw_source_identity":raw.get("source_commit")==freeze["source_commit"] and raw.get("source_sha256")==freeze["source_sha256"] and raw.get("source_git_blob")==freeze["source_git_blob"],
      "input_hash":raw.get("input_sha256")==freeze["input_sha256"]==hashlib.sha256((HERE/"input.json").read_bytes()).hexdigest(),
      "advancing_epoch":raw.get("source_observation",{}).get("sequence")==inp["source_sequence"] and raw.get("next_observation",{}).get("sequence")==inp["next_sequence"] and raw.get("next_observation",{}).get("capture_ns")==inp["next_capture_ns"],
      "frame_changed":raw.get("source_observation",{}).get("frame_rgb_sha256")!=raw.get("next_observation",{}).get("frame_rgb_sha256"),
      "typed_values_unchanged":all(raw.get("next_observation",{}).get("signals",{}).get(k,{}).get("value")==inp[k] for k in ("health","ammo")),
      "same_binding":raw.get("source_observation",{}).get("pointer_binding")==raw.get("next_observation",{}).get("pointer_binding")==inp["binding"],
      "no_invalidation":raw.get("monitor_result") is None,
      "no_soft_event":raw.get("post_state",{}).get("soft_event_count")==0 and raw.get("post_state",{}).get("latest_soft_event") is None,
      "monitor_advanced":raw.get("post_state",{}).get("last_sequence")==inp["next_sequence"] and raw.get("post_state",{}).get("last_frame_rgb_sha256")==raw.get("next_observation",{}).get("frame_rgb_sha256"),
      "no_authority":raw.get("admission_receipt",{}).get("grants_input_authority") is False,
    }
    return {"schema":"v39-frame-only-threat-boundary-audit-v2","disposition":"CONFIRMED_BOUNDARY" if all(checks.values()) else "REJECTED","audit_head":current_head,"checks":checks}

if __name__=="__main__":
    out=HERE/"results"/"a01"/"candidate.json"
    audit_path=HERE/"results"/"a01"/"audit-v2.json"
    if audit_path.exists(): raise SystemExit("audit-v2 output already exists; preserve first outcome")
    result=validate(json.loads(out.read_text(encoding="utf-8")))
    audit_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    if result["disposition"]!="CONFIRMED_BOUNDARY": raise SystemExit(1)
