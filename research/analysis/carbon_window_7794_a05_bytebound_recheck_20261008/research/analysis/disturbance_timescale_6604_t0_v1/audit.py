"""Independent raw-only replay auditor for Issue #6604 T0."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _clip(value: int, low: int, high: int) -> int:
    return min(high, max(low, value))


def _rebuild(case: dict, route: str, horizon: int, cap: int, limits: list[int]) -> dict:
    x = 0
    pending = 0
    rebuilt = []
    for t in range(horizon):
        current_target = case["targets"][t]
        if route == "direct":
            sample_t = 3 * (t // 3)
            observed = case["targets"][sample_t]
            age = t - sample_t
            output = _clip(observed - x, -cap, cap)
            applied = output
        else:
            observed = current_target
            age = 0
            output = _clip(observed - x, -cap, cap)
            applied = pending
            pending = output
        prior = x
        x = _clip(x + applied, limits[0], limits[1])
        rebuilt.append({
            "tick": t,
            "observation_age": age,
            "observed_target": observed,
            "position_before": prior,
            "command": output,
            "applied": applied,
            "position_after": x,
            "tracking_error": abs(current_target - x),
        })
    release_lag = 0 if route == "direct" else 1
    residual = 0 if route == "direct" else pending
    released_x = _clip(x + residual, limits[0], limits[1])
    release_error = abs(case["targets"][-1] - released_x)
    return {
        "case_id": case["id"],
        "route": route,
        "rows": rebuilt,
        "tracking_error_sum": sum(row["tracking_error"] for row in rebuilt) + release_error,
        "action_count": len(rebuilt),
        "release_lag_ticks": release_lag,
        "release": {
            "requested_at_tick": horizon,
            "neutral_at_tick": horizon + release_lag,
            "residual_command_applied": residual,
            "position_after_release": released_x,
            "terminal_neutral": True,
        },
        "terminal_neutral": True,
    }


def audit(raw: dict, inputs: dict, oracle: dict) -> dict:
    errors: list[str] = []
    if raw.get("schema") != "issue6604-t0-candidate-v1":
        errors.append("candidate_schema_mismatch")
    horizon = inputs["horizon"]
    cap = inputs["action_limit"]
    limits = inputs["position_limits"]
    cases = inputs["cases"]
    expected_keys = [(case["id"], route) for case in cases for route in ("direct", "local_periodic")]
    actual = [(r.get("case_id"), r.get("route")) for r in raw.get("records", [])]
    if actual != expected_keys:
        errors.append("missing_extra_duplicate_or_reordered_rows")
    by_key = {(r.get("case_id"), r.get("route")): r for r in raw.get("records", [])}
    for case in cases:
        for route in ("direct", "local_periodic"):
            key = (case["id"], route)
            expected = _rebuild(case, route, horizon, cap, limits)
            if by_key.get(key) != expected:
                errors.append(f"raw_replay_mismatch:{case['id']}:{route}")
            record = by_key.get(key, {})
            if record.get("action_count") != horizon or record.get("terminal_neutral") is not True:
                errors.append(f"budget_or_release_gate:{case['id']}:{route}")
            if any(abs(row.get("applied", cap + 1)) > cap for row in record.get("rows", [])):
                errors.append(f"unsafe_action:{case['id']}:{route}")
    matrices = oracle["matrices"]
    totals = {
        key: {
            route: sum(by_key[(case_id, route)]["tracking_error_sum"] for case_id in case_ids)
            for route in ("direct", "local_periodic")
        }
        for key, case_ids in matrices.items()
    }
    planted = totals["planted_crossover"]
    crossover = planted["direct"] < planted["local_periodic"]
    slow = by_key[("C01", "local_periodic")]["tracking_error_sum"] < by_key[("C01", "direct")]["tracking_error_sum"]
    fast = by_key[("C02", "direct")]["tracking_error_sum"] < by_key[("C02", "local_periodic")]["tracking_error_sum"]
    null_directions = [
        by_key[(case_id, "direct")]["tracking_error_sum"] < by_key[(case_id, "local_periodic")]["tracking_error_sum"]
        for case_id in matrices["no_crossover"]
    ]
    null_same = len(set(null_directions)) == 1
    if not (slow and fast):
        errors.append("planted_stratum_ordering_not_recovered")
    if not null_same:
        errors.append("no_crossover_control_reversed")
    if not crossover:
        errors.append("pooled_direction_unexpected")
    # No semantic-effect field is admitted in candidate raw. The scorer-only
    # aliasing oracle therefore cannot be mistaken for a visible cue.
    swap_records = [by_key.get(("C07", route), {}) for route in ("direct", "local_periodic")]
    swap_input = next((case for case in cases if case["id"] == "C07"), {})
    slow_input = next((case for case in cases if case["id"] == "C01"), {})
    if swap_input.get("targets") != slow_input.get("targets"):
        errors.append("semantic_swap_stream_not_aliased")
    if any("semantic_claim" in record for record in swap_records) or oracle["semantic_swap_unobservable"]["visible_cue"] is not False:
        errors.append("unobservable_semantic_swap_claimed")
    return {
        "schema": "issue6604-t0-independent-audit-v1",
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_INTEGRITY",
        "rows": len(actual),
        "errors": errors,
        "matrix_error_totals": totals,
        "planted_crossover_detected": crossover,
        "slow_local_better": slow,
        "fast_direct_better": fast,
        "no_crossover_control_consistent": null_same,
        "semantic_swap_claim_absent": all("semantic_claim" not in record for record in swap_records),
    }


def main() -> int:
    raw_path, inputs_path, oracle_path, out_path = map(Path, sys.argv[1:5])
    result = audit(json.loads(raw_path.read_text()), json.loads(inputs_path.read_text()), json.loads(oracle_path.read_text()))
    out_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"status={result['status']} rows={result['rows']} errors={len(result['errors'])}")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
