#!/usr/bin/env python3
"""Raw-only stdlib auditor for the bounded #4935 mode comparison."""
import json
import math
import statistics
import sys
from pathlib import Path


def audit(raw, freeze=None, freeze_sha256=None):
    errors = []
    if raw.get("schema") != "mitra-inference-mode-diagnostic-4935-v1" or raw.get("issue") != 4935:
        errors.append("SCHEMA_OR_ISSUE")
    if freeze is not None:
        if raw.get("allocation") != freeze.get("allocation") or raw.get("main_intake_sha") != freeze.get("main_intake_sha"):
            errors.append("FREEZE_IDENTITY")
        if raw.get("image_id") != freeze.get("execution", {}).get("image_id"):
            errors.append("IMAGE_IDENTITY")
        if raw.get("expected_input_sha256") != {k: freeze.get("inputs", {}).get(k, {}).get("sha256") for k in ("support", "queries")}:
            errors.append("INPUT_IDENTITY")
        if raw.get("source_sha256") != freeze.get("source_sha256"):
            errors.append("SOURCE_IDENTITY")
        if freeze_sha256 is not None and raw.get("freeze_sha256") != freeze_sha256:
            errors.append("FREEZE_HASH")
        expected_model = freeze.get("model", {}).get("sha256")
        expected_support = freeze.get("inputs", {}).get("support", {}).get("sha256")
        expected_queries = freeze.get("inputs", {}).get("queries", {}).get("sha256")
        if raw.get("runtime", {}).get("model_sha256") != expected_model:
            errors.append("MODEL_IDENTITY")
        if raw.get("runtime", {}).get("support_sha256") != expected_support or raw.get("runtime", {}).get("queries_sha256") != expected_queries:
            errors.append("RUNTIME_INPUT_HASHES")
    runtime = raw.get("runtime", {})
    if runtime.get("optimizer_step_calls") != 0:
        errors.append("OPTIMIZER_STEPS")
    if len(runtime.get("model_load_seconds", [])) != 1:
        errors.append("MODEL_LOAD_COUNT")
    rows = raw.get("predictions", [])
    expected = {(i, j, arm) for i in range(16) for j in range(4) for arm in ("A", "B")}
    observed = [(x.get("row_index"), x.get("repeat_index"), x.get("arm")) for x in rows]
    if len(rows) != 128 or len(set(observed)) != 128 or set(observed) != expected:
        errors.append("POPULATION_OR_DUPLICATES")
    natural = {x.get("name"): bool(x.get("training")) for x in raw.get("natural_module_state", [])}
    orders = {}
    for r in rows:
        p = r.get("probabilities", [])
        if len(p) != 6 or not all(isinstance(v, (float, int)) and math.isfinite(v) and v >= 0 for v in p):
            errors.append("PROBABILITY_VECTOR")
            break
        if abs(sum(p) - 1.0) > 1e-4:
            errors.append("PROBABILITY_SUM")
            break
        bef = r.get("modules_before", [])
        aft = r.get("modules_after", [])
        if not bef or not aft or [x.get("name") for x in bef] != [x.get("name") for x in aft]:
            errors.append("MODULE_STATE_EVIDENCE")
            break
        active = [x for x in bef + aft if x.get("training") and "dropout" in str(x.get("type", "")).lower()]
        if r.get("arm") == "B" and active:
            errors.append("EVAL_ARM_ACTIVE_DROPOUT")
            break
        if r.get("arm") == "B" and (any(x.get("training") for x in bef) or any(x.get("training") for x in aft)):
            errors.append("EVAL_ARM_MODULE_TRAINING")
            break
        if r.get("arm") == "A" and {x.get("name"): bool(x.get("training")) for x in bef} != natural:
            errors.append("NATURAL_MODE_NOT_RESTORED")
            break
        orders[r.get("row_index")] = r.get("order")
    if len(orders) != 16 or sum(orders.get(i) == ["A", "B"] for i in range(16)) != 8 or sum(orders.get(i) == ["B", "A"] for i in range(16)) != 8:
        errors.append("ORDER_NOT_COUNTERBALANCED")
    ranges = {}
    for arm in ("A", "B"):
        per_row = []
        for i in range(16):
            vecs = [x["probabilities"] for x in rows if x.get("row_index") == i and x.get("arm") == arm]
            if len(vecs) != 4:
                continue
            per_row.append(max(max(abs(a[k] - b[k]) for k in range(6)) for a in vecs for b in vecs))
        ranges[arm] = per_row
    med_a = statistics.median(ranges.get("A", [0]))
    med_b = statistics.median(ranges.get("B", [0]))
    result = {"schema": "mitra-inference-mode-audit-4935-v1", "errors": errors,
        "row_count": len(rows), "per_row_max_range": ranges,
        "median_range_A": med_a, "median_range_B": med_b,
        "natural_active_dropout_modules": raw.get("natural_active_dropout_modules", []),
        "scientific_disposition": None}
    if not errors:
        count_a = sum(x > 1e-6 for x in ranges["A"])
        count_b = sum(x <= 1e-6 for x in ranges["B"])
        pass_gate = bool(result["natural_active_dropout_modules"]) and count_a >= 8 and count_b == 16 and med_b * 10 <= med_a
        result["scientific_disposition"] = "PASS_EVAL_MODE_EXPLAINS_REPEAT_DRIFT_SCOPED" if pass_gate else "REJECT_EVAL_MODE_CAUSE_SCOPED"
    return result


def main():
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    raw = json.loads(source.read_text(encoding="utf-8"))
    freeze_path = Path("/src/FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    import hashlib
    freeze_sha = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    result = audit(raw, freeze, freeze_sha)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
