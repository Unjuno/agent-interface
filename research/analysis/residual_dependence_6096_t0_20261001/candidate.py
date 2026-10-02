"""One-shot finite candidate for Issue #6096 residual-dependence sentinel."""
import argparse
import json
from pathlib import Path


def lag_sum(values, width):
    tail = values[-(width + 1):]
    return sum(a * b for a, b in zip(tail, tail[1:]))


def calibrate_threshold(public):
    scores = []
    for case in public["training"]:
        seq = case["residual_num"]
        for end in range(1, len(seq) + 1):
            if end >= public["dependence_window_pairs"] + 1:
                scores.append(max(0, lag_sum(seq[:end], public["dependence_window_pairs"])))
    return max(scores, default=0) + 1


def decide(public, case, policy, dep_threshold):
    if policy == "always_yield":
        return {"case_id": case["id"], "policy": policy, "seen_samples": 0, "stop_reason": "YIELD_ALWAYS"}
    expected_identity = case["identity"][0]
    observed = []
    for idx, (present, identity, value) in enumerate(zip(case["present"], case["identity"], case["residual_num"]), start=1):
        if not present or value is None:
            return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "YIELD_MISSING"}
        if identity != expected_identity:
            return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "YIELD_IDENTITY_CHANGE"}
        observed.append(value)
        if policy == "fixed_short_hold" and idx >= public["fixed_short_hold_samples"]:
            return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "OBSERVE_FIXED_SHORT"}
        if policy == "pointwise" and abs(value) > public["pointwise_threshold_num"]:
            return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "YIELD_POINTWISE"}
        if policy == "running_mean":
            # Residual is residual_num / residual_scale. Threshold is 1/4.
            if abs(sum(observed)) > idx:
                return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "YIELD_RUNNING_MEAN"}
        if policy == "calibrated_dependence" and idx >= public["dependence_window_pairs"] + 1:
            if max(0, lag_sum(observed, public["dependence_window_pairs"])) >= dep_threshold:
                return {"case_id": case["id"], "policy": policy, "seen_samples": idx, "stop_reason": "YIELD_DEPENDENCE"}
    return {"case_id": case["id"], "policy": policy, "seen_samples": len(observed), "stop_reason": "CONTINUE_TO_HORIZON"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = json.loads(Path(args.public).read_text(encoding="utf-8"))
    threshold = calibrate_threshold(public)
    rows = [decide(public, case, policy, threshold) for case in public["cases"] for policy in public["policies"]]
    result = {"schema": "agent-interface.residual-dependence-6096.raw.v1", "calibrated_dependence_threshold": threshold, "training_case_count": len(public["training"]), "rows": rows}
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"candidate cases={len(public['cases'])} policies={len(public['policies'])} rows={len(rows)} dependence_threshold={threshold}")


if __name__ == "__main__":
    main()
