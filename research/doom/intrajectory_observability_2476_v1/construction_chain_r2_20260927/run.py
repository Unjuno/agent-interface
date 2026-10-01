from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path


LOCAL_RADIUS_PX = 8
GLOBAL_DRIFT_CAP_PX = 12
MAX_AGE_NS = 250_000_000
MAX_FRAME_GAP = 2
MIN_SCORE = 0.80
MIN_MARGIN = 0.08
GEOMETRY = (640, 480)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_cases(data: dict) -> list[dict]:
    all_cases = []
    start = data["initial"]
    template = data["steps_template"]
    for spec in data["cases"]:
        prev_seq = start["frame_seq"]
        prev_time = start["captured_ns"]
        prev_x, prev_y = start["center_x_px"], start["center_y_px"]
        steps = []
        for n, residual in enumerate(spec["residuals_px"], start=1):
            patch = spec.get("step_overrides", {}).get(str(n), {})
            seq_delta = patch.get("frame_seq_delta", template["frame_seq_delta"])
            age = patch.get("age_ns", template["age_ns"])
            step = {
                "frame_seq": prev_seq + seq_delta,
                "captured_ns": prev_time + age,
                "frame_sha256": ("%064x" % (n + len(all_cases) * 4 + 1))[-64:],
                "width": patch.get("width", template["width"]),
                "height": patch.get("height", template["height"]),
                "status": patch.get("status", template["status"]),
                "score": patch.get("score", template["score"]),
                "margin": patch.get("margin", template["margin"]),
                "command_dx_px": 8,
                "command_dy_px": 0,
                "center_x_px": patch.get("center_x_px", prev_x + 8 + residual),
                "center_y_px": patch.get("center_y_px", prev_y),
                "fallback": patch.get("fallback", template["fallback"]),
            }
            steps.append(step)
            prev_seq, prev_time = step["frame_seq"], step["captured_ns"]
            if isinstance(step["center_x_px"], int):
                prev_x = step["center_x_px"]
            if isinstance(step["center_y_px"], int):
                prev_y = step["center_y_px"]
        all_cases.append({"id": spec["id"], "initial": dict(start), "steps": steps})
    return all_cases


def run_policy(case: dict, global_cap: bool) -> dict:
    origin = case["initial"]
    previous = dict(origin)
    cumulative_dx = cumulative_dy = 0
    stopped = False
    rows = []
    for index, step in enumerate(case["steps"], start=1):
        if stopped:
            rows.append({"step": index, "state": "NOT_REACHED_AFTER_STOP", "reason": "PRIOR_STOP"})
            continue
        reason = "TRACKED"
        age = step["captured_ns"] - previous["captured_ns"]
        gap = step["frame_seq"] - previous["frame_seq"]
        predicted_x = previous["center_x_px"] + step["command_dx_px"]
        predicted_y = previous["center_y_px"] + step["command_dy_px"]
        local_dx = step["center_x_px"] - predicted_x if isinstance(step["center_x_px"], int) else None
        local_dy = step["center_y_px"] - predicted_y if isinstance(step["center_y_px"], int) else None
        next_dx = cumulative_dx + step["command_dx_px"]
        next_dy = cumulative_dy + step["command_dy_px"]
        global_x = origin["center_x_px"] + next_dx
        global_y = origin["center_y_px"] + next_dy
        drift_x = step["center_x_px"] - global_x if isinstance(step["center_x_px"], int) else None
        drift_y = step["center_y_px"] - global_y if isinstance(step["center_y_px"], int) else None
        if step["status"] != "FOUND":
            reason = "OBSERVATION_NOT_FOUND"
        elif not isinstance(step["score"], (int, float)) or step["score"] < MIN_SCORE or not isinstance(step["margin"], (int, float)) or step["margin"] < MIN_MARGIN:
            reason = "CURRENT_MATCH_GATE"
        elif (step["width"], step["height"]) != GEOMETRY:
            reason = "CURRENT_GEOMETRY"
        elif not 1 <= gap <= MAX_FRAME_GAP:
            reason = "FRAME_SEQUENCE"
        elif not 0 <= age <= MAX_AGE_NS:
            reason = "OBSERVATION_AGE"
        elif not isinstance(local_dx, int) or not isinstance(local_dy, int) or abs(local_dx) > LOCAL_RADIUS_PX or abs(local_dy) > LOCAL_RADIUS_PX:
            reason = "LOCAL_CORRIDOR_MISS"
        elif global_cap and (abs(drift_x) > GLOBAL_DRIFT_CAP_PX or abs(drift_y) > GLOBAL_DRIFT_CAP_PX):
            reason = "GLOBAL_DRIFT_BOUND"
        valid = reason == "TRACKED"
        rows.append({
            "step": index,
            "state": "TRACKED" if valid else "ABSTAIN",
            "reason": reason,
            "frame_seq": step["frame_seq"],
            "frame_sha256": step["frame_sha256"],
            "captured_ns": step["captured_ns"],
            "local_predicted_center_px": [predicted_x, predicted_y],
            "observed_center_px": [step["center_x_px"], step["center_y_px"]],
            "local_residual_px": [local_dx, local_dy],
            "global_predicted_center_px": [global_x, global_y],
            "global_drift_px": [drift_x, drift_y],
            "score": step["score"],
            "margin": step["margin"],
            "fallback": step["fallback"],
            "physical_input_emitted": False,
        })
        if valid:
            previous = step
            cumulative_dx, cumulative_dy = next_dx, next_dy
        else:
            stopped = True
    reached = sum(row["state"] == "TRACKED" for row in rows)
    stop = next((row for row in rows if row["state"] == "ABSTAIN"), None)
    return {"policy": "PER_HOP_PLUS_GLOBAL_12PX" if global_cap else "PER_HOP_ONLY", "steps": rows, "hops_tracked": reached, "stop_step": stop["step"] if stop else None, "stop_reason": stop["reason"] if stop else None, "physical_input_emissions": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    src, out = args.source.resolve(), args.out.resolve()
    freeze = json.loads((src / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if digest(src / name) != expected:
            raise SystemExit("FREEZE_MISMATCH:" + name)
    inputs = json.loads((src / "cases.json").read_text())
    cases = make_cases(inputs)
    started = time.monotonic_ns()
    rows = []
    for case in cases:
        rows.append({"case_id": case["id"], "raw_case": case, "per_hop_only": run_policy(case, False), "global_drift_cap": run_policy(case, True)})
    result = {"schema": "track-chain-construction-trace-v1", "allocation": freeze["allocation"], "source_sha256": freeze["sha256"], "input_sha256": digest(src / "cases.json"), "python": sys.version, "platform": platform.platform(), "started_monotonic_ns": started, "finished_monotonic_ns": time.monotonic_ns(), "cases": rows, "physical_input_emissions": 0}
    out.mkdir(parents=True, exist_ok=True)
    with (out / "trace.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"allocation": freeze["allocation"], "cases": len(rows), "trace_sha256": digest(out / "trace.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

