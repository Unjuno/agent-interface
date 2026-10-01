from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HOP = 8
GLOBAL = 12
AGE = 250_000_000
GAP = 2
SCORE = 0.80
MARGIN = 0.08
SIZE = (640, 480)
EXPECTED = {
    "exact_three_hops": {"PER_HOP_ONLY": (3, None, None), "PER_HOP_PLUS_GLOBAL_12PX": (3, None, None)},
    "cumulative_drift_exactly_12": {"PER_HOP_ONLY": (3, None, None), "PER_HOP_PLUS_GLOBAL_12PX": (3, None, None)},
    "repeated_8px_hop_residual_crosses_global_at_hop2": {"PER_HOP_ONLY": (3, None, None), "PER_HOP_PLUS_GLOBAL_12PX": (1, 2, "GLOBAL_DRIFT_BOUND")},
    "cumulative_drift_crosses_at_13px_hop3": {"PER_HOP_ONLY": (3, None, None), "PER_HOP_PLUS_GLOBAL_12PX": (2, 3, "GLOBAL_DRIFT_BOUND")},
    "abrupt_translation_at_hop2": {"PER_HOP_ONLY": (1, 2, "LOCAL_CORRIDOR_MISS"), "PER_HOP_PLUS_GLOBAL_12PX": (1, 2, "LOCAL_CORRIDOR_MISS")},
    "true_target_disappearance_at_hop2": {"PER_HOP_ONLY": (1, 2, "OBSERVATION_NOT_FOUND"), "PER_HOP_PLUS_GLOBAL_12PX": (1, 2, "OBSERVATION_NOT_FOUND")},
    "score_below_gate_at_hop3": {"PER_HOP_ONLY": (2, 3, "CURRENT_MATCH_GATE"), "PER_HOP_PLUS_GLOBAL_12PX": (2, 3, "CURRENT_MATCH_GATE")},
    "stale_hop_age_at_hop2": {"PER_HOP_ONLY": (1, 2, "OBSERVATION_AGE"), "PER_HOP_PLUS_GLOBAL_12PX": (1, 2, "OBSERVATION_AGE")},
    "geometry_change_at_hop3": {"PER_HOP_ONLY": (2, 3, "CURRENT_GEOMETRY"), "PER_HOP_PLUS_GLOBAL_12PX": (2, 3, "CURRENT_GEOMETRY")},
    "frame_sequence_gap_at_hop2": {"PER_HOP_ONLY": (1, 2, "FRAME_SEQUENCE"), "PER_HOP_PLUS_GLOBAL_12PX": (1, 2, "FRAME_SEQUENCE")},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge(a: dict, b: dict | None) -> dict:
    output = dict(a)
    if b:
        output.update(b)
    return output


def generate(data: dict) -> list[dict]:
    cases = []
    for spec in data["cases"]:
        initial = dict(data["initial"])
        prior_seq, prior_time = initial["frame_seq"], initial["captured_ns"]
        prior_x, prior_y = initial["center_x_px"], initial["center_y_px"]
        chain = []
        for index, residual in enumerate(spec["residuals_px"], 1):
            override = spec.get("step_overrides", {}).get(str(index), {})
            dd = override.get("frame_seq_delta", data["steps_template"]["frame_seq_delta"])
            dt = override.get("age_ns", data["steps_template"]["age_ns"])
            chain.append({
                "frame_seq": prior_seq + dd,
                "captured_ns": prior_time + dt,
                "frame_sha256": ("%064x" % (index + len(cases) * 4 + 1))[-64:],
                "width": override.get("width", data["steps_template"]["width"]),
                "height": override.get("height", data["steps_template"]["height"]),
                "status": override.get("status", data["steps_template"]["status"]),
                "score": override.get("score", data["steps_template"]["score"]),
                "margin": override.get("margin", data["steps_template"]["margin"]),
                "command_dx_px": 8,
                "command_dy_px": 0,
                "center_x_px": override.get("center_x_px", prior_x + 8 + residual),
                "center_y_px": override.get("center_y_px", prior_y),
                "fallback": override.get("fallback", data["steps_template"]["fallback"]),
            })
            prior_seq, prior_time = chain[-1]["frame_seq"], chain[-1]["captured_ns"]
            if isinstance(chain[-1]["center_x_px"], int):
                prior_x = chain[-1]["center_x_px"]
            if isinstance(chain[-1]["center_y_px"], int):
                prior_y = chain[-1]["center_y_px"]
        cases.append({"id": spec["id"], "initial": initial, "steps": chain})
    return cases


def independently_run(case: dict, bounded: bool) -> dict:
    origin = case["initial"]
    current = dict(origin)
    total_x = total_y = 0
    records = []
    stopped = False
    for position, obs in enumerate(case["steps"], 1):
        if stopped:
            records.append({"step": position, "state": "NOT_REACHED_AFTER_STOP", "reason": "PRIOR_STOP"})
            continue
        code = "TRACKED"
        dt = obs["captured_ns"] - current["captured_ns"]
        ds = obs["frame_seq"] - current["frame_seq"]
        next_x, next_y = total_x + obs["command_dx_px"], total_y + obs["command_dy_px"]
        local_x = current["center_x_px"] + obs["command_dx_px"]
        local_y = current["center_y_px"] + obs["command_dy_px"]
        global_x = origin["center_x_px"] + next_x
        global_y = origin["center_y_px"] + next_y
        if obs["status"] != "FOUND":
            code = "OBSERVATION_NOT_FOUND"
        elif not isinstance(obs["score"], (int, float)) or obs["score"] < SCORE or not isinstance(obs["margin"], (int, float)) or obs["margin"] < MARGIN:
            code = "CURRENT_MATCH_GATE"
        elif (obs["width"], obs["height"]) != SIZE:
            code = "CURRENT_GEOMETRY"
        elif ds not in (1, 2):
            code = "FRAME_SEQUENCE"
        elif dt < 0 or dt > AGE:
            code = "OBSERVATION_AGE"
        elif not isinstance(obs["center_x_px"], int) or not isinstance(obs["center_y_px"], int) or abs(obs["center_x_px"] - local_x) > HOP or abs(obs["center_y_px"] - local_y) > HOP:
            code = "LOCAL_CORRIDOR_MISS"
        elif bounded and (abs(obs["center_x_px"] - global_x) > GLOBAL or abs(obs["center_y_px"] - global_y) > GLOBAL):
            code = "GLOBAL_DRIFT_BOUND"
        ok = code == "TRACKED"
        records.append({
            "step": position,
            "state": "TRACKED" if ok else "ABSTAIN",
            "reason": code,
            "frame_seq": obs["frame_seq"],
            "frame_sha256": obs["frame_sha256"],
            "captured_ns": obs["captured_ns"],
            "local_predicted_center_px": [local_x, local_y],
            "observed_center_px": [obs["center_x_px"], obs["center_y_px"]],
            "local_residual_px": [obs["center_x_px"] - local_x if isinstance(obs["center_x_px"], int) else None, obs["center_y_px"] - local_y if isinstance(obs["center_y_px"], int) else None],
            "global_predicted_center_px": [global_x, global_y],
            "global_drift_px": [obs["center_x_px"] - global_x if isinstance(obs["center_x_px"], int) else None, obs["center_y_px"] - global_y if isinstance(obs["center_y_px"], int) else None],
            "score": obs["score"], "margin": obs["margin"], "fallback": obs["fallback"],
            "physical_input_emitted": False,
        })
        if ok:
            current = obs
            total_x, total_y = next_x, next_y
        else:
            stopped = True
    completed = sum(1 for entry in records if entry["state"] == "TRACKED")
    first_stop = next((entry for entry in records if entry["state"] == "ABSTAIN"), None)
    return {"policy": "PER_HOP_PLUS_GLOBAL_12PX" if bounded else "PER_HOP_ONLY", "steps": records, "hops_tracked": completed, "stop_step": first_stop["step"] if first_stop else None, "stop_reason": first_stop["reason"] if first_stop else None, "physical_input_emissions": 0}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    source, out = a.source.resolve(), a.out.resolve()
    freeze = json.loads((source / "FREEZE.json").read_text())
    errors = []
    for name, expected in freeze["sha256"].items():
        if sha(source / name) != expected:
            errors.append("SOURCE_HASH:" + name)
    inputs = json.loads((source / "cases.json").read_text())
    trace = json.loads((out / "trace.json").read_text())
    expected_cases = generate(inputs)
    if trace.get("schema") != "track-chain-construction-trace-v1":
        errors.append("TRACE_SCHEMA")
    if trace.get("allocation") != freeze.get("allocation"):
        errors.append("ALLOCATION_BINDING")
    if trace.get("source_sha256") != freeze.get("sha256"):
        errors.append("SOURCE_BINDING")
    if trace.get("input_sha256") != sha(source / "cases.json"):
        errors.append("INPUT_BINDING")
    rows = trace.get("cases", [])
    if len(rows) != len(expected_cases):
        errors.append("CASE_COUNT")
    by_id = {row.get("case_id"): row for row in rows}
    if len(by_id) != len(rows):
        errors.append("DUPLICATE_CASE")
    for case in expected_cases:
        cid = case["id"]
        row = by_id.get(cid)
        if row is None:
            errors.append("MISSING_CASE:" + cid)
            continue
        if row.get("raw_case") != case:
            errors.append("RAW_CASE_MISMATCH:" + cid)
        for key, bounded in (("per_hop_only", False), ("global_drift_cap", True)):
            recomputed = independently_run(case, bounded)
            if row.get(key) != recomputed:
                errors.append("POLICY_RECOMPUTE:" + cid + ":" + key)
        declared = EXPECTED.get(cid)
        for key in ("per_hop_only", "global_drift_cap"):
            decision = row.get(key, {})
            observed = (decision.get("hops_tracked"), decision.get("stop_step"), decision.get("stop_reason"))
            if declared is None or observed != declared.get(decision.get("policy")):
                errors.append("FROZEN_EXPECTATION:" + cid + ":" + key)
            if decision.get("physical_input_emissions") != 0:
                errors.append("INPUT_EMISSION_COUNT:" + cid + ":" + key)
            for step in decision.get("steps", []):
                if step.get("physical_input_emitted") is not False:
                    errors.append("INPUT_EMITTED:" + cid + ":" + key)
    if trace.get("physical_input_emissions") != 0:
        errors.append("TRACE_INPUT_EMISSIONS")
    drift_case = by_id.get("repeated_8px_hop_residual_crosses_global_at_hop2", {})
    if drift_case:
        candidate = drift_case.get("per_hop_only", {}).get("steps", [])
        if not all(s.get("state") == "TRACKED" and abs(s.get("global_drift_px", [999])[0]) <= 24 for s in candidate):
            errors.append("PER_HOP_DRIFT_COUNTEREXAMPLE")
        bounded = drift_case.get("global_drift_cap", {}).get("steps", [])
        if len(bounded) < 2 or bounded[1].get("reason") != "GLOBAL_DRIFT_BOUND" or bounded[1].get("global_drift_px") != [16, 0]:
            errors.append("GLOBAL_CAP_DID_NOT_STOP_FIRST_CROSSING")
    result = {
        "schema": "track-chain-construction-audit-v1",
        "allocation": freeze["allocation"],
        "case_count": len(rows),
        "policy_rows_audited": 2 * len(rows),
        "decision": "PASS_CUMULATIVE_TRACK_DRIFT_BOUNDARY_CONSTRUCTION_ONLY" if not errors else "FAIL_CUMULATIVE_DRIFT_GATE",
        "physical_input_emissions": trace.get("physical_input_emissions"),
        "errors": errors,
    }
    with (out / "audit.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

