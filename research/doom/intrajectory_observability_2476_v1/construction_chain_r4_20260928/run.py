import argparse
import hashlib
import json
from pathlib import Path


LOCAL_RADIUS = 8
GLOBAL_CAP = 12
MAX_AGE_NS = 250_000_000
MAX_GAP = 2
MIN_SCORE = 0.80
MIN_MARGIN = 0.08
GEOMETRY = (640, 480)
POLICIES = ("PER_HOP_ONLY", "PER_HOP_PLUS_GLOBAL_12PX")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def candidates(data):
    result = []
    origin = data["initial"]
    template = data["steps_template"]
    for case_index, spec in enumerate(data["cases"]):
        prev_seq, prev_time = origin["frame_seq"], origin["captured_ns"]
        prev_x, prev_y = origin["center_x_px"], origin["center_y_px"]
        steps = []
        for number, residual in enumerate(spec["residuals_px"], start=1):
            override = spec.get("step_overrides", {}).get(str(number), {})
            seq_delta = override.get("frame_seq_delta", template["frame_seq_delta"])
            age = override.get("age_ns", template["age_ns"])
            step = {
                "frame_seq": prev_seq + seq_delta,
                "captured_ns": prev_time + age,
                "frame_sha256": "%064x" % (number + case_index * 4 + 1),
                "width": override.get("width", template["width"]),
                "height": override.get("height", template["height"]),
                "status": override.get("status", template["status"]),
                "score": override.get("score", template["score"]),
                "margin": override.get("margin", template["margin"]),
                "command_dx_px": 8,
                "command_dy_px": 0,
                "center_x_px": override.get("center_x_px", prev_x + 8 + residual),
                "center_y_px": override.get("center_y_px", prev_y),
                "fallback": override.get("fallback", template["fallback"]),
            }
            steps.append(step)
            prev_seq, prev_time = step["frame_seq"], step["captured_ns"]
            if isinstance(step["center_x_px"], int):
                prev_x = step["center_x_px"]
            if isinstance(step["center_y_px"], int):
                prev_y = step["center_y_px"]
        result.append({"id": spec["id"], "initial": dict(origin), "steps": steps})
    return result


def execute(case, policy):
    origin = case["initial"]
    previous = dict(origin)
    cumulative_x = cumulative_y = 0
    stopped = False
    rows = []
    for index, step in enumerate(case["steps"], start=1):
        if stopped:
            rows.append({"step": index, "state": "NOT_REACHED_AFTER_STOP",
                         "reason": "PRIOR_STOP", "physical_input_emitted": False})
            continue
        reason = "TRACKED"
        age = step["captured_ns"] - previous["captured_ns"]
        gap = step["frame_seq"] - previous["frame_seq"]
        predicted = [previous["center_x_px"] + step["command_dx_px"],
                     previous["center_y_px"] + step["command_dy_px"]]
        observed = [step["center_x_px"], step["center_y_px"]]
        local = [observed[0] - predicted[0] if isinstance(observed[0], int) else None,
                 observed[1] - predicted[1] if isinstance(observed[1], int) else None]
        next_x = cumulative_x + step["command_dx_px"]
        next_y = cumulative_y + step["command_dy_px"]
        global_predicted = [origin["center_x_px"] + next_x,
                            origin["center_y_px"] + next_y]
        drift = [observed[0] - global_predicted[0] if isinstance(observed[0], int) else None,
                 observed[1] - global_predicted[1] if isinstance(observed[1], int) else None]

        if step["status"] != "FOUND":
            reason = "OBSERVATION_NOT_FOUND"
        elif (not isinstance(step["score"], (int, float)) or step["score"] < MIN_SCORE
              or not isinstance(step["margin"], (int, float)) or step["margin"] < MIN_MARGIN):
            reason = "CURRENT_MATCH_GATE"
        elif (step["width"], step["height"]) != GEOMETRY:
            reason = "CURRENT_GEOMETRY"
        elif not 1 <= gap <= MAX_GAP:
            reason = "FRAME_SEQUENCE"
        elif not 0 <= age <= MAX_AGE_NS:
            reason = "OBSERVATION_AGE"
        elif any(not isinstance(v, int) for v in local) or any(abs(v) > LOCAL_RADIUS for v in local):
            reason = "LOCAL_CORRIDOR_MISS"
        elif (policy == "PER_HOP_PLUS_GLOBAL_12PX"
              and any(v is None or abs(v) > GLOBAL_CAP for v in drift)):
            reason = "GLOBAL_DRIFT_BOUND"

        valid = reason == "TRACKED"
        rows.append({
            "step": index,
            "state": "TRACKED" if valid else "ABSTAIN",
            "reason": reason,
            "frame_seq": step["frame_seq"],
            "frame_sha256": step["frame_sha256"],
            "captured_ns": step["captured_ns"],
            "local_predicted_center_px": predicted,
            "observed_center_px": observed,
            "local_residual_px": local,
            "global_predicted_center_px": global_predicted,
            "global_drift_px": drift,
            "score": step["score"],
            "margin": step["margin"],
            "physical_input_emitted": False,
        })
        if valid:
            previous = step
            cumulative_x, cumulative_y = next_x, next_y
        else:
            stopped = True
    stop_steps = [r["step"] for r in rows if r["state"] == "ABSTAIN"]
    return {"case_id": case["id"], "policy": policy, "rows": rows,
            "stopped_at_step": stop_steps[0] if stop_steps else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    freeze = json.loads((source / "FREEZE.json").read_text())
    for name, expected in freeze["source_sha256"].items():
        if sha((source / name).read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + name)
    case_bytes = (source / "cases.json").read_bytes()
    case_data = json.loads(case_bytes)
    rows = []
    for case in candidates(case_data):
        for policy in POLICIES:
            rows.append(execute(case, policy))
    raw = {
        "allocation": freeze["allocation"],
        "cases_sha256": sha(case_bytes),
        "source_sha256": freeze["source_sha256"],
        "case_count": len(case_data["cases"]),
        "policy_count": len(POLICIES),
        "scheduled_hops_per_policy": 3,
        "physical_input_emissions": 0,
        "runs": rows,
    }
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (out / "raw.json").write_bytes(raw_bytes)
    print(json.dumps({"allocation": freeze["allocation"], "runs": len(rows),
                      "scheduled_rows": sum(len(r["rows"]) for r in rows),
                      "raw_sha256": sha(raw_bytes), "physical_input_emissions": 0}, sort_keys=True))


if __name__ == "__main__":
    main()

