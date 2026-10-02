"""Finite candidate: bounded motor continuation with independently checked identity/epoch gates."""
import argparse
import json
from pathlib import Path


POLICIES = ("identity_epoch_gate", "identity_only_gate", "kinematic_only", "no_continuation")
MAX_CHUNK = 8
ERROR_LIMIT = 2.0


def stop_reason(obs, case, policy, tick):
    if not obs["focus_valid"]:
        return "focus_invalid"
    if not obs["lease_valid"]:
        return "lease_invalid"
    if policy == "no_continuation" and tick > 0:
        return "baseline_release"
    if policy in ("identity_epoch_gate", "identity_only_gate"):
        if obs["observed_identity"] is None:
            return "identity_unknown"
        if obs["observed_identity"] != case["intended_identity"]:
            return "identity_changed"
    if policy == "identity_epoch_gate":
        if obs["observed_epoch"] is None:
            return "epoch_unknown"
        if obs["observed_epoch"] != case["intended_epoch"]:
            return "epoch_changed"
    if policy != "no_continuation" and obs["prediction_error"] is None:
        return "prediction_unknown"
    if policy != "no_continuation" and obs["prediction_error"] > ERROR_LIMIT:
        return "prediction_error"
    return None


def run_case(case, policy):
    stopped = False
    chunk_start = 0
    captures = 0
    trace = []
    for obs in case["observations"]:
        tick = obs["tick"]
        reason = stop_reason(obs, case, policy, tick) if not stopped else "already_released"
        capture = False
        command = 0
        if not stopped and reason is None:
            if captures == 0 or tick - chunk_start >= MAX_CHUNK or obs["prediction_error"] > ERROR_LIMIT:
                capture = True
                captures += 1
                chunk_start = tick
            command = obs["predicted_direction"]
        elif not stopped:
            stopped = True
        trace.append({
            "tick": tick,
            "command": command,
            "capture": capture,
            "gate_reason": reason,
            "observed_identity": obs["observed_identity"],
            "observed_epoch": obs["observed_epoch"],
            "prediction_error": obs["prediction_error"],
            "focus_valid": obs["focus_valid"],
            "lease_valid": obs["lease_valid"],
            "released": stopped,
        })
    return {"case_id": case["case_id"], "policy": policy,
            "capture_count": captures,
            "commanded_occupancy_ticks": sum(r["command"] != 0 for r in trace),
            "release_tick": next((r["tick"] for r in trace if r["released"] and r["gate_reason"] != "already_released"), None),
            "trace": trace}


def run(input_path):
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = [run_case(case, policy) for case in data["cases"] for policy in POLICIES]
    return {"schema": "agent-interface.intermit6061.identity-switch.raw.v1", "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.input)
    Path(args.output).write_text("\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in result["rows"]) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result["rows"]), "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()
