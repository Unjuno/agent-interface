"""Independent raw-only reconstruction; imports no candidate code."""
import argparse
import copy
import json
from pathlib import Path

POLICIES = ["identity_epoch_gate", "identity_only_gate", "kinematic_only", "no_continuation"]
CASE_IDS = ["same_identity_control", "visible_identity_switch", "epoch_only_switch",
            "unknown_epoch_switch", "silent_identity_switch"]
OBS_KEYS = {"tick", "observed_identity", "observed_epoch", "focus_valid", "lease_valid",
            "prediction_error", "predicted_direction"}


def input_errors(data):
    errors = []
    if set(data) != {"schema", "cases"} or data.get("schema") != "agent-interface.intermit6061.identity-switch.input.v1":
        errors.append("visible_schema")
    cases = data.get("cases", [])
    if [c.get("case_id") for c in cases] != CASE_IDS:
        errors.append("case_inventory")
    for c in cases:
        if set(c) != {"case_id", "intended_identity", "intended_epoch", "observations"}:
            errors.append("case_fields")
        if len(c.get("observations", [])) != 12:
            errors.append("horizon")
        for o in c.get("observations", []):
            if set(o) != OBS_KEYS:
                errors.append("observation_fields_or_oracle_leak")
    return errors


def reconstruct(case, policy):
    trace, origin, captures, halted = [], 0, 0, False
    for obs in case["observations"]:
        tick = obs["tick"]
        why = "already_released" if halted else None
        if not halted:
            if obs["focus_valid"] is not True:
                why = "focus_invalid"
            elif obs["lease_valid"] is not True:
                why = "lease_invalid"
            elif policy == "no_continuation" and tick > 0:
                why = "baseline_release"
            elif policy in ("identity_epoch_gate", "identity_only_gate"):
                if obs["observed_identity"] is None:
                    why = "identity_unknown"
                elif obs["observed_identity"] != case["intended_identity"]:
                    why = "identity_changed"
                elif policy == "identity_epoch_gate":
                    if obs["observed_epoch"] is None:
                        why = "epoch_unknown"
                    elif obs["observed_epoch"] != case["intended_epoch"]:
                        why = "epoch_changed"
            if why is None and policy != "no_continuation":
                if obs["prediction_error"] is None:
                    why = "prediction_unknown"
                elif obs["prediction_error"] > 2.0:
                    why = "prediction_error"
        if why not in (None, "already_released"):
            halted = True
        renew = not halted and (captures == 0 or tick - origin >= 8)
        if renew:
            captures += 1
            origin = tick
        trace.append({
            "tick": tick, "command": obs["predicted_direction"] if not halted else 0,
            "capture": renew, "gate_reason": why,
            "observed_identity": obs["observed_identity"], "observed_epoch": obs["observed_epoch"],
            "prediction_error": obs["prediction_error"], "focus_valid": obs["focus_valid"],
            "lease_valid": obs["lease_valid"], "released": halted,
        })
    release = next((r["tick"] for r in trace if r["released"] and r["gate_reason"] != "already_released"), None)
    return trace, captures, release


def audit_data(visible, truth, raw):
    errors = input_errors(visible)
    if truth.get("schema") != "agent-interface.intermit6061.identity-switch.truth.v1":
        errors.append("truth_schema")
    cases = {c["case_id"]: c for c in visible.get("cases", [])}
    oracle = {c["case_id"]: c for c in truth.get("cases", [])}
    order = [(c["case_id"], p) for c in visible.get("cases", []) for p in POLICIES]
    keys = [(r.get("case_id"), r.get("policy")) for r in raw]
    if keys != order:
        errors.append("row_order_inventory")
    found, details = {}, []
    for row in raw:
        key = (row.get("case_id"), row.get("policy"))
        if key in found or key[0] not in cases or key[1] not in POLICIES:
            errors.append("duplicate_or_unknown_row")
            continue
        found[key] = row
        trace, captures, release = reconstruct(cases[key[0]], key[1])
        occupancy = sum(x["command"] != 0 for x in trace)
        if row.get("trace") != trace:
            errors.append("trace_mismatch:" + ":".join(key))
        if (row.get("capture_count"), row.get("commanded_occupancy_ticks"), row.get("release_tick")) != (captures, occupancy, release):
            errors.append("summary_mismatch:" + ":".join(key))
        switch = oracle.get(key[0], {}).get("switch_tick")
        post = sum(x["command"] != 0 for x in trace if switch is not None and x["tick"] >= switch)
        details.append({"case_id": key[0], "policy": key[1], "captures": captures,
                        "commanded_occupancy_ticks": occupancy, "release_tick": release,
                        "post_switch_command_ticks": post})
    if set(found) != set(order):
        errors.append("missing_row")
    release_ticks = {}
    for cid in ("visible_identity_switch", "epoch_only_switch", "unknown_epoch_switch"):
        row, switch = found.get((cid, "identity_epoch_gate"), {}), oracle.get(cid, {}).get("switch_tick")
        release_ticks[cid] = row.get("release_tick")
        if row.get("release_tick") != switch:
            errors.append("gate_boundary:" + cid)
        if any(x.get("command") for x in row.get("trace", []) if switch is not None and x.get("tick", -1) >= switch):
            errors.append("post_switch_command:" + cid)
    identity_only = found.get(("epoch_only_switch", "identity_only_gate"), {})
    identity_misses = identity_only.get("release_tick") is None and identity_only.get("commanded_occupancy_ticks", 0) > 5
    if not identity_misses:
        errors.append("identity_only_control")
    kinematic = {}
    for cid in ("visible_identity_switch", "epoch_only_switch", "unknown_epoch_switch"):
        row = found.get((cid, "kinematic_only"), {})
        kinematic[cid] = row.get("release_tick") is None and row.get("commanded_occupancy_ticks", 0) > 5
    if not all(kinematic.values()):
        errors.append("kinematic_negative_control")
    equivalent = all(found.get(("same_identity_control", p), {}).get("trace") ==
                     found.get(("silent_identity_switch", p), {}).get("trace") for p in POLICIES)
    silent_release = found.get(("silent_identity_switch", "identity_epoch_gate"), {}).get("release_tick")
    unidentifiable = equivalent and silent_release is None
    if not unidentifiable:
        errors.append("silent_switch_not_quarantined")
    return {
        "status": "PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_HOLD" if not errors else "FAIL_AUDIT",
        "decision": "HOLD_SILENT_IDENTITY_SWITCH_UNOBSERVABLE" if not errors and unidentifiable else "FAIL_GATE_OR_AUDIT",
        "rows": len(raw), "errors": errors, "observable_gate_release_ticks": release_ticks,
        "identity_only_misses_epoch_only_switch": identity_misses,
        "kinematic_only_misses_observable_switches": kinematic,
        "silent_switch_observationally_equivalent_to_control": equivalent,
        "silent_switch_disposition": "UNKNOWN_NOT_CREDITED" if unidentifiable else "ERROR",
        "details": details,
    }


def mutations(visible, truth, raw):
    checks = []
    x = copy.deepcopy(raw); x.pop(); checks.append(("drop_row", visible, x))
    x = copy.deepcopy(raw); x.append(copy.deepcopy(x[0])); checks.append(("duplicate_row", visible, x))
    x = copy.deepcopy(raw)
    next(r for r in x if r["case_id"] == "epoch_only_switch" and r["policy"] == "identity_epoch_gate")["trace"][5]["command"] = 1
    checks.append(("continue_after_epoch_change", visible, x))
    x = copy.deepcopy(raw)
    next(r for r in x if r["case_id"] == "visible_identity_switch" and r["policy"] == "identity_epoch_gate")["release_tick"] = 6
    checks.append(("shift_release_tick", visible, x))
    v = copy.deepcopy(visible); v["cases"][0]["observations"][0]["target_identity"] = "target-A"
    checks.append(("oracle_leak_into_input", v, raw))
    result = []
    for name, v, rows in checks:
        errors = audit_data(v, truth, rows)["errors"]
        result.append({"case": name, "rejected": bool(errors), "errors": errors})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("input", "truth", "raw", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    visible = json.loads(Path(args.input).read_text(encoding="utf-8"))
    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    raw = [json.loads(x) for x in Path(args.raw).read_text(encoding="utf-8").splitlines() if x]
    result = audit_data(visible, truth, raw)
    result["mutations"] = mutations(visible, truth, raw)
    if not all(x["rejected"] for x in result["mutations"]):
        result["errors"].append("mutation_control_accepted")
        result["status"], result["decision"] = "FAIL_AUDIT", "FAIL_GATE_OR_AUDIT"
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "decision", "rows", "errors")}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_HOLD" else 1)
