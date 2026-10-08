"""Independent raw-only oracle for Issue #6523 synthetic T0."""
import copy
import json
import sys
from pathlib import Path


def oracle(case, route):
    target = case["target_generation"]
    phase = "UNKNOWN" if any(x["type"] == "COMPOSITION_UNKNOWN" for x in case["events"]) else "IDLE"
    committed = None
    submits = 0
    effect = None
    for x in case["events"]:
        kind = x["type"]
        valid = x.get("generation") == target
        if route == "RAW_ENTER":
            if kind in ("VALUE_CHANGE", "NATIVE_FILL") and valid:
                committed = x["value"]
            if kind in ("ENTER", "SUBMIT_INTENT") and valid:
                submits += 1
            if kind == "APP_EFFECT" and valid:
                effect = x["value"]
        elif route == "SYMBOLIC_ONLY":
            if kind in ("VALUE_CHANGE", "NATIVE_FILL") and valid:
                committed = x["value"]
            if kind == "ENTER" and valid:
                phase = "COMMITTED_ASSUMED"
            elif kind == "SUBMIT_INTENT" and valid:
                submits += 1
            elif kind == "APP_EFFECT" and valid:
                effect = x["value"]
        elif route == "NATIVE_FILL":
            if kind in ("NATIVE_FILL", "VALUE_CHANGE") and valid:
                committed = x["value"]
            elif kind == "SUBMIT_INTENT" and valid:
                submits += 1
            elif kind == "APP_EFFECT" and valid:
                effect = x["value"]
        elif route == "PHASE_AWARE":
            if kind == "COMPOSITION_UNKNOWN":
                phase = "UNKNOWN"
            elif not valid:
                continue
            elif kind == "COMPOSITION_START":
                phase = "PREEDIT_ACTIVE"
            elif kind == "PREEDIT_UPDATE":
                if phase != "PREEDIT_ACTIVE":
                    continue
            elif kind == "COMPOSITION_CANCEL":
                phase = "CANCELLED"
            elif kind == "COMPOSITION_END":
                if phase != "UNKNOWN":
                    phase = "COMMIT_PENDING"
            elif kind in ("VALUE_CHANGE", "NATIVE_FILL"):
                committed = x["value"]
                phase = "COMMITTED_VALUE_OBSERVED"
            elif kind == "SUBMIT_INTENT":
                if phase == "COMMITTED_VALUE_OBSERVED" and committed is not None:
                    submits += 1
            elif kind == "APP_EFFECT":
                effect = x["value"]
    intended = committed == case["expected"]
    completion = submits > 0 and intended and effect == case["expected"]
    return {"case_id": case["id"], "route": route, "phase": phase,
            "committed_value": committed, "submit_count": submits,
            "effect_value": effect, "intended_value_match": intended,
            "completion_claim": completion, "consumer_authority": False,
            "consumer_side_effects": 0}


def reconstruct(spec):
    return [oracle(case, route) for case in spec["cases"] for route in spec["routes"]]


def audit_object(spec, raw):
    errors = []
    if raw.get("schema") != "ime-commit-effect-raw-v1":
        errors.append("schema")
    if raw.get("case_count") != len(spec["cases"]):
        errors.append("case_count")
    if raw.get("routes") != spec["routes"]:
        errors.append("route_set")
    want = reconstruct(spec)
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(want) or raw.get("row_count") != len(want):
        errors.append("row_coverage")
        rows = rows if isinstance(rows, list) else []
    if rows != want:
        errors.append("independent_reconstruction")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row_{i}_shape")
            continue
        if row.get("consumer_authority") is not False or row.get("consumer_side_effects") != 0:
            errors.append(f"row_{i}_authority")
        if row.get("completion_claim") and not (
            row.get("submit_count", 0) > 0
            and row.get("intended_value_match") is True
            and row.get("effect_value") is not None
        ):
            errors.append(f"row_{i}_false_completion")
    return errors


def corruption_controls(spec, raw):
    controls = {}
    mutations = {
        "preedit_as_committed": lambda r: r.update(committed_value="PREEDIT_FORGED",
                                                    intended_value_match=False,
                                                    completion_claim=False),
        "enter_counts_as_submit": lambda r: r.update(submit_count=999),
        "wrong_intended_value": lambda r: r.update(intended_value_match=not r.get("intended_value_match")),
        "effect_without_receipt": lambda r: r.update(effect_value="FORGED_EFFECT"),
        "false_completion": lambda r: r.update(completion_claim=not r.get("completion_claim")),
        "authority_expansion": lambda r: r.update(consumer_authority=True),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed["rows"][0])
        controls[name] = bool(audit_object(spec, changed))
    return controls


def audit(spec_path, raw_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    errors = audit_object(spec, raw)
    controls = corruption_controls(spec, raw)
    if not all(controls.values()):
        errors.append("mutation_control_missed")
    rows = raw.get("rows", [])
    oracle_rows = reconstruct(spec)
    expected_by_key = {(r["case_id"], r["route"]): r for r in oracle_rows}
    case_by_id = {case["id"]: case for case in spec["cases"]}
    premature = {}
    premature_cases = {}
    false_completion = {}
    for route in spec["routes"]:
        selected = [r for r in rows if isinstance(r, dict) and r.get("route") == route]
        premature[route] = sum(max(0, r.get("submit_count", 0) -
                                    case_by_id[r["case_id"]]["oracle"]["submit_count"])
                               for r in selected if (r.get("case_id"), route) in expected_by_key)
        premature_cases[route] = sorted(
            r["case_id"] for r in selected
            if (r.get("case_id"), route) in expected_by_key and
            r.get("submit_count", 0) > case_by_id[r["case_id"]]["oracle"]["submit_count"])
        false_completion[route] = sum(
            bool(r.get("completion_claim")) and not (
                case_by_id.get(r.get("case_id"), {}).get("oracle", {}).get("committed") ==
                case_by_id.get(r.get("case_id"), {}).get("expected") and
                case_by_id.get(r.get("case_id"), {}).get("oracle", {}).get("submit_count", 0) > 0 and
                case_by_id.get(r.get("case_id"), {}).get("oracle", {}).get("effect") ==
                case_by_id.get(r.get("case_id"), {}).get("expected"))
            for r in selected)
    result = {"schema": "ime-commit-effect-audit-v1",
              "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
              "errors": errors, "rows": len(rows), "case_count": len(spec["cases"]),
              "mutation_controls": controls,
              "route_premature_submit_excess": premature,
              "route_premature_submit_cases": premature_cases,
              "route_false_completion_claims": false_completion,
              "scope": "synthetic authored finite event traces only; no real IME/GUI/application result"}
    return result


if __name__ == "__main__":
    result = audit(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 2)
