import hashlib
import json
import math
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("RESEARCH_REPO_ROOT", HERE.parents[2]))
OUT = Path(os.environ.get("RESEARCH_OUTPUT_DIR", HERE / "formal-output"))
FROZEN = HERE / "FROZEN_IMAGE.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def softmax(logits):
    top = max(logits)
    exps = [math.exp(x - top) for x in logits]
    return [x / sum(exps) for x in exps]


def audit():
    prereg = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    errors = []
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    if result.get("status") == "STOP_BEFORE_FIRST_OPTIMIZER_STEP":
        checks = {
            "runtime_matches_freeze": result.get("runtime") == frozen.get("runtime"),
            "zero_steps": result.get("optimizer_steps_completed") == 0,
            "no_retry": result.get("retry") is False and frozen.get("allocation", {}).get("retry") is False,
            "no_model_rows": result.get("arms") == {} and result.get("evaluation_rows") == 0,
        }
        for rel, expected in frozen.get("source_sha256", {}).items():
            checks["frozen_source:" + rel] = sha256((HERE / rel).resolve()) == expected
        checks["manifest"] = sha256(ROOT / prereg["manifest"]["path"]) == prereg["manifest"]["sha256"]
        checks["validator"] = sha256(ROOT / "research/live_control/compiled_form_grounding_v1.py") == frozen["source_sha256"]["../../../research/live_control/compiled_form_grounding_v1.py"]
        verdict = "STOP_INFRASTRUCTURE_NO_RETRY" if all(checks.values()) else "STOP_EVIDENCE_INTEGRITY_FAILURE"
        audit = {"schema": "gpu-photometric-grounding-audit-v1", "verdict": verdict,
                 "checks": checks, "errors": [k for k, v in checks.items() if not v],
                 "model_comparison_performed": False}
        (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not all(checks.values()):
            raise SystemExit(2)
        return
    if result.get("runtime") != frozen.get("runtime"):
        errors.append("runtime_freeze_mismatch")
    for rel, expected in frozen.get("source_sha256", {}).items():
        if sha256((HERE / rel).resolve()) != expected:
            errors.append("frozen_source_sha256_mismatch:" + rel)
    manifest_path = ROOT / prereg["manifest"]["path"]
    if sha256(manifest_path) != prereg["manifest"]["sha256"]:
        errors.append("manifest_sha256_mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_id = {r["task_id"]: r for r in manifest["records"]}
    for item in prereg["source_images"]:
        if sha256(ROOT / item["path"]) != item["sha256"]:
            errors.append("source_image_sha256_mismatch:" + item["task_id"])
    sys.path.insert(0, str(ROOT / "research" / "live_control"))
    from compiled_form_grounding_v1 import validate
    audit_rows = {}
    for arm, rows in result.get("arms", {}).items():
        if len(rows) != 6:
            errors.append("row_count:" + arm)
        seen = set()
        for row in rows:
            key = (row.get("task_id"), row.get("factor"))
            if key in seen:
                errors.append("duplicate_row:" + arm + ":" + str(key))
            seen.add(key)
            source = by_id.get(row.get("task_id"))
            if source is None or source["layout"] != row.get("layout_gold"):
                errors.append("gold_mismatch:" + arm + ":" + str(key))
                continue
            probs = softmax(row["raw_logits"])
            if any(abs(a - b) > 1e-12 for a, b in zip(probs, row["probabilities_recomputed"])):
                errors.append("probability_mismatch:" + arm + ":" + str(key))
            confidence = max(probs)
            expected_decision = "accept" if confidence >= .75 else "yield" if confidence >= .25 else "reject"
            predicted = "A" if probs.index(max(probs)) == 0 else "B"
            if row["decision"] != expected_decision or row["predicted_layout"] != predicted:
                errors.append("route_mismatch:" + arm + ":" + str(key))
            try:
                validated = validate(row["candidate"])
                if validated != row["validator_output"]:
                    errors.append("validator_output_mismatch:" + arm + ":" + str(key))
            except Exception:
                errors.append("validator_rejected:" + arm + ":" + str(key))
                continue
            exact = (predicted == source["layout"] and
                     validated["field_point"] == source["field_point"] and
                     validated["submit_point"] == source["submit_point"])
            accepted = expected_decision == "accept"
            if row["accepted_exact"] != (accepted and exact):
                errors.append("exact_label_mismatch:" + arm + ":" + str(key))
            if row["accepted_wrong"] != (accepted and not exact):
                errors.append("wrong_label_mismatch:" + arm + ":" + str(key))
            audit_rows.setdefault(arm, []).append({"task_id": key[0], "factor": key[1],
                                                   "decision": expected_decision,
                                                   "predicted_layout": predicted,
                                                   "exact": exact, "accepted": accepted})
    required_arms = {"no_augmentation", "brightness_augmentation"}
    if set(result.get("arms", {})) != required_arms:
        errors.append("arm_set_mismatch")
    false_accepts = any(r.get("accepted_wrong") for rows in result.get("arms", {}).values() for r in rows)
    counts = {}
    for arm, rows in result.get("arms", {}).items():
        counts[arm] = sum(r["accepted_exact"] for r in rows if r["factor"] != 1.0)
    if errors:
        verdict = "STOP_AUDIT_INTEGRITY_FAILURE"
    elif false_accepts:
        verdict = "FAIL_ACCEPTED_FALSE_GROUNDING"
    elif counts.get("brightness_augmentation", 0) >= counts.get("no_augmentation", 0) and counts.get("brightness_augmentation", 0) > counts.get("no_augmentation", 0):
        verdict = "PASS_PHOTOMETRIC_AUGMENTATION_SCOPED"
    else:
        verdict = "HOLD_NO_SAFE_BENEFIT"
    audit = {"schema": "gpu-photometric-grounding-audit-v1", "verdict": verdict,
             "errors": errors, "accepted_exact_perturbed": counts,
             "rows_independently_recomputed": audit_rows}
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    audit()
