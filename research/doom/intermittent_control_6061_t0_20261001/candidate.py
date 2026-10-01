"""Candidate controller simulation. It reads only the planner-visible fixture."""
import argparse
import json
from pathlib import Path


POLICIES = ("fixed_period", "prediction_triggered", "bounded_hold", "no_continuation")
MAX_CHUNK = 8
FIXED_PERIOD = 4
ERROR_THRESHOLD = 2.0
MAX_OCCUPANCY = 40


def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def invalid(obs, intended):
    return (obs["identity"] != intended or not obs["focus_valid"]
            or not obs["lease_valid"] or obs["capture_x"] is None)


def run_case(case, policy):
    agent = float(case["initial_agent_x"])
    intended = case["intended_identity"]
    observations = case["observations"]
    last_capture = None
    previous_capture = None
    last_capture_tick = None
    chunk_start = 0
    command = 0
    stopped = False
    capture_count = 0
    occupancy = 0
    trace = []

    for tick, obs in enumerate(observations):
        reason = None
        if invalid(obs, intended):
            command = 0
            stopped = True
            reason = "invalidation_release"
        elif not stopped:
            if capture_count == 0:
                reason = "initial"
            elif policy == "fixed_period" and tick % FIXED_PERIOD == 0:
                reason = "fixed_period"
            elif policy in ("bounded_hold", "prediction_triggered") and tick - chunk_start >= MAX_CHUNK:
                reason = "max_chunk"
            elif policy == "prediction_triggered" and last_capture is not None:
                if previous_capture is None:
                    predicted = last_capture
                else:
                    dt = last_capture_tick - previous_capture[0]
                    velocity = ((last_capture - previous_capture[1]) / dt) if dt else 0.0
                    predicted = last_capture + velocity * (tick - last_capture_tick)
                probe = obs["probe_x"]
                if probe is None or abs(probe - predicted) > ERROR_THRESHOLD:
                    reason = "prediction_error"
            elif policy == "no_continuation" and tick > 0:
                command = 0
                stopped = True
                reason = "bounded_baseline_release"

            if reason and reason not in ("invalidation_release", "bounded_baseline_release"):
                previous_capture = ((last_capture_tick, last_capture)
                                    if last_capture is not None else None)
                last_capture = obs["capture_x"]
                last_capture_tick = tick
                command = sign(last_capture - agent)
                chunk_start = tick
                capture_count += 1

        before = agent
        if command:
            occupancy += 1
            agent += command
        trace.append({"tick": tick, "capture": bool(reason and reason not in
                       ("invalidation_release", "bounded_baseline_release")),
                      "trigger": reason, "command": command,
                      "agent_before": round(before, 4), "agent_after": round(agent, 4),
                      "identity": obs["identity"], "focus_valid": obs["focus_valid"],
                      "lease_valid": obs["lease_valid"]})

    return {"case_id": case["case_id"], "policy": policy, "capture_count": capture_count,
            "probe_count": len(observations), "occupancy_ticks": occupancy,
            "cpu_proxy": capture_count * 10 + len(observations), "trace": trace}


def run(input_path):
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = [run_case(case, policy) for case in data["cases"] for policy in POLICIES]
    return {"schema": "agent-interface.intermit6061.raw.v1", "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.input)
    Path(args.output).write_text("\n".join(json.dumps(row, sort_keys=True, separators=(",", ":"))
                                                    for row in result["rows"]) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result["rows"]), "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()
