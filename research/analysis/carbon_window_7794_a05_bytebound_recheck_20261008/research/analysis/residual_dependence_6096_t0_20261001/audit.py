"""Independent finite reconstruction for the frozen Issue #6096 candidate."""
import argparse
import json
from pathlib import Path


def oracle_training_cutoff(spec):
    largest = 0
    width = spec["dependence_window_pairs"]
    for training_case in spec["training"]:
        values = training_case["residual_num"]
        for right in range(width, len(values)):
            total = 0
            for k in range(right - width, right):
                total += values[k] * values[k + 1]
            if total > largest:
                largest = total
    return largest + 1


def oracle_decision(spec, case, policy, threshold):
    if policy == "always_yield":
        return 0, "YIELD_ALWAYS"
    series = []
    origin = case["identity"][0]
    for position in range(len(case["residual_num"])):
        t = position + 1
        sample = case["residual_num"][position]
        if not case["present"][position] or sample is None:
            return t, "YIELD_MISSING"
        if case["identity"][position] != origin:
            return t, "YIELD_IDENTITY_CHANGE"
        series.append(sample)
        if policy == "fixed_short_hold" and t >= spec["fixed_short_hold_samples"]:
            return t, "OBSERVE_FIXED_SHORT"
        if policy == "pointwise" and max(sample, -sample) > spec["pointwise_threshold_num"]:
            return t, "YIELD_POINTWISE"
        if policy == "running_mean" and abs(sum(series)) > t:
            return t, "YIELD_RUNNING_MEAN"
        if policy == "calibrated_dependence" and len(series) >= spec["dependence_window_pairs"] + 1:
            start = len(series) - spec["dependence_window_pairs"] - 1
            lag_score = sum(series[k] * series[k + 1] for k in range(start, len(series) - 1))
            if max(0, lag_score) >= threshold:
                return t, "YIELD_DEPENDENCE"
    return len(series), "CONTINUE_TO_HORIZON"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec = json.loads(Path(args.public).read_text(encoding="utf-8"))
    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    raw_lines = Path(args.raw).read_text(encoding="utf-8").splitlines()
    found = json.loads(raw_lines[0]) if len(raw_lines) == 1 else None
    expected_threshold = oracle_training_cutoff(spec)
    errors = []
    expected_rows = []
    for case in spec["cases"]:
        for policy in spec["policies"]:
            t, reason = oracle_decision(spec, case, policy, expected_threshold)
            expected_rows.append({"case_id": case["id"], "policy": policy, "seen_samples": t, "stop_reason": reason})
    if found is None:
        errors.append({"error": "raw must contain exactly one JSON object line"})
    else:
        if found.get("calibrated_dependence_threshold") != expected_threshold:
            errors.append({"error": "training calibration threshold mismatch"})
        if found.get("rows") != expected_rows:
            errors.append({"error": "decision-row reconstruction mismatch"})

    by_key = {(r["case_id"], r["policy"]): r for r in (found or {}).get("rows", [])}
    danger_id = "heldout-phase-lag-danger"
    dangerous_stop = by_key.get((danger_id, "calibrated_dependence"), {}).get("seen_samples")
    wrong_after = truth["danger_wrong_continuation_after_sample"][danger_id]
    safe_ids = truth["false_yield_zero_limit_cases"]
    false_yields = [cid for cid in safe_ids if by_key.get((cid, "calibrated_dependence"), {}).get("stop_reason") == "YIELD_DEPENDENCE"]
    pointwise_reason = by_key.get((danger_id, "pointwise"), {}).get("stop_reason")
    mean_reason = by_key.get((danger_id, "running_mean"), {}).get("stop_reason")
    mean_control = by_key.get((truth["mean_shift_positive_control"], "running_mean"), {})
    source_case = "target-identity-swap"
    missing_case = "missing-observation"
    source_fail_closed = all(by_key.get((source_case, p), {}).get("stop_reason") == "YIELD_IDENTITY_CHANGE" and by_key.get((source_case, p), {}).get("seen_samples") == truth["expected_source_invalidation_sample"][source_case] for p in spec["policies"] if p != "always_yield")
    missing_fail_closed = all(by_key.get((missing_case, p), {}).get("stop_reason") == "YIELD_MISSING" and by_key.get((missing_case, p), {}).get("seen_samples") == truth["expected_missing_invalidation_sample"][missing_case] for p in spec["policies"] if p != "always_yield")

    # Enumerate integer thresholds to expose the finite false-YIELD/detection frontier.
    frontier = []
    window = spec["dependence_window_pairs"]
    for threshold in range(1, expected_threshold + 2):
        detected = []
        false = []
        for case in spec["cases"]:
            row = oracle_decision(spec, case, "calibrated_dependence", threshold)
            if row[1] == "YIELD_DEPENDENCE":
                if case["id"] == danger_id:
                    detected.append(case["id"])
                elif case["id"] in safe_ids:
                    false.append(case["id"])
        frontier.append({"threshold": threshold, "danger_detected": bool(detected), "false_yield_cases": false})
    danger_prefix = next(c for c in spec["cases"] if c["id"] == danger_id)["residual_num"][:truth["critical_observability_witness"]["identical_residual_prefix_samples"]]
    matched_safe = [next(c for c in spec["cases"] if c["id"] == cid)["residual_num"][:len(danger_prefix)] for cid in safe_ids if cid in ("heldout-valid-periodic", "heldout-camera-jitter")]
    indistinguishable = all(seq == danger_prefix for seq in matched_safe)
    criteria = {
        "audit_reconstruction_pass": not errors,
        "baseline_pointwise_misses_danger": pointwise_reason == "CONTINUE_TO_HORIZON",
        "baseline_running_mean_misses_danger": mean_reason == "CONTINUE_TO_HORIZON",
        "calibrated_dependence_stops_before_wrong_continuation": isinstance(dangerous_stop, int) and dangerous_stop <= wrong_after,
        "false_yield_zero_limit_pass": len(false_yields) == 0,
        "mean_shift_positive_control_detected": mean_control.get("stop_reason") == "YIELD_RUNNING_MEAN",
        "source_invalidation_fail_closed": source_fail_closed,
        "missing_evidence_fail_closed": missing_fail_closed,
        "matched_harmless_prefix_indistinguishable": indistinguishable,
    }
    method_pass = criteria["baseline_pointwise_misses_danger"] and criteria["baseline_running_mean_misses_danger"] and criteria["calibrated_dependence_stops_before_wrong_continuation"] and criteria["false_yield_zero_limit_pass"] and criteria["mean_shift_positive_control_detected"] and criteria["source_invalidation_fail_closed"] and criteria["missing_evidence_fail_closed"]
    result = {
        "schema": "agent-interface.residual-dependence-6096.audit.v1",
        "raw_line_count": len(raw_lines),
        "expected_rows": len(expected_rows),
        "observed_rows": len((found or {}).get("rows", [])),
        "calibrated_threshold_expected": expected_threshold,
        "calibrated_danger_stop_sample": dangerous_stop,
        "wrong_continuation_after_sample": wrong_after,
        "calibrated_false_yield_cases": false_yields,
        "criteria": criteria,
        "threshold_frontier": frontier,
        "errors": errors,
        "disposition": "PASS_METHOD_SCOPED" if method_pass and not errors else ("STOP_AUDIT_MISMATCH" if errors else "FAIL_METHOD_NO_ZERO_FALSE_YIELD_DETECTION_FRONTIER"),
        "scope": "finite synthetic residual sequences only; no calibrated serial-correlation p-value, GUI, actuator, or safety claim"
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"auditor rows={result['observed_rows']} errors={len(errors)} disposition={result['disposition']}")


if __name__ == "__main__":
    main()
