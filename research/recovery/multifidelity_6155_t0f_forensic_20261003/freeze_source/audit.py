#!/usr/bin/env python3
"""Independent raw-only replay for #6155 T0f; does not import candidate.py."""
import json
import math
import random
import sys
from pathlib import Path


def expected_record(fixture, case, case_index, stream_id):
    delta = fixture["deltas"][case]
    rng = random.Random(fixture["seed"] + case_index * 1_000_003 + stream_id)
    looks = set(fixture["looks"])
    total_z = 0.0
    total_z2 = 0.0
    total_leak = 0.0
    naive_time = None
    cs_time = None
    n = 0
    for t in range(1, fixture["max_time"] + 1):
        x = fixture["x_magnitude"] * (1 if rng.getrandbits(1) else -1)
        noise = fixture["epsilon_magnitude"] * (1 if rng.getrandbits(1) else -1)
        high = delta + x + noise
        corrected = high - fixture["fixed_beta"] * x
        row_beta = high / x
        row_corrected = high - row_beta * x
        n += 1
        total_z += corrected
        total_z2 += corrected * corrected
        total_leak += row_corrected
        if t in looks:
            average = total_z / n
            s2 = max(0.0, (total_z2 - total_z * total_z / n) / (n - 1))
            se = math.sqrt(s2 / n)
            naive_lower = average - fixture["naive_two_sided_z"] * se
            per_time_alpha = fixture["family_alpha"] / (t * (t + 1))
            b_lo, b_hi = fixture["corrected_bound"]
            cs_halfwidth = math.sqrt((b_hi - b_lo) ** 2 * math.log(2 / per_time_alpha) / (2 * n))
            if naive_time is None and naive_lower > 0:
                naive_time = t
            if cs_time is None and average - cs_halfwidth > 0:
                cs_time = t
    return {
        "case": case,
        "stream": stream_id,
        "delta": delta,
        "naive_stop_time": naive_time,
        "cs_stop_time": cs_time,
        "fixed_beta_final_mean": total_z / n,
        "leaky_final_mean": total_leak / n,
        "leaky_stop_time": None
    }


def same_row(actual, expected):
    return actual == expected


def main(fixture_path: str, raw_path: str, audit_path: str) -> int:
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw_lines = Path(raw_path).read_text(encoding="utf-8").splitlines()
    expected_count = fixture["streams_per_case"] * len(fixture["deltas"])
    errors = []
    expected_rows = []
    for case_index, case in enumerate(fixture["deltas"]):
        for stream_id in range(fixture["streams_per_case"]):
            expected_rows.append(expected_record(fixture, case, case_index, stream_id))
    if len(raw_lines) != expected_count:
        errors.append(f"row_count:{len(raw_lines)}!={expected_count}")
    actual_rows = []
    for index, line in enumerate(raw_lines):
        try:
            actual_rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f"json:{index}:{type(exc).__name__}")
            actual_rows.append(None)
    if len(actual_rows) == len(expected_rows):
        for index, (actual, expected) in enumerate(zip(actual_rows, expected_rows)):
            if not isinstance(actual, dict) or not same_row(actual, expected):
                errors.append(f"replay_mismatch:{index}")
                if len(errors) >= 20:
                    break
    else:
        errors.append("complete_assignment_cover_missing")

    mutations = []
    if expected_rows:
        target = expected_rows[0]
        for key, bad in (("naive_stop_time", 1), ("cs_stop_time", 1),
                         ("fixed_beta_final_mean", 999.0), ("leaky_final_mean", 999.0)):
            altered = dict(target)
            altered[key] = bad
            mutations.append(not same_row(altered, target))

    grouped = {case: [] for case in fixture["deltas"]}
    if len(actual_rows) == expected_count:
        for row in actual_rows:
            if isinstance(row, dict) and row.get("case") in grouped:
                grouped[row["case"]].append(row)
    metrics = {}
    for case, rows in grouped.items():
        denom = fixture["streams_per_case"]
        metrics[case] = {
            "streams": len(rows),
            "naive_stops": sum(row.get("naive_stop_time") is not None for row in rows),
            "naive_stop_rate": sum(row.get("naive_stop_time") is not None for row in rows) / denom,
            "cs_stops": sum(row.get("cs_stop_time") is not None for row in rows),
            "cs_stop_rate": sum(row.get("cs_stop_time") is not None for row in rows) / denom,
            "leaky_stops": sum(row.get("leaky_stop_time") is not None for row in rows),
            "leaky_stop_rate": sum(row.get("leaky_stop_time") is not None for row in rows) / denom,
            "leaky_max_abs_mean": max((abs(row.get("leaky_final_mean", math.inf)) for row in rows), default=math.inf)
        }
    gate = fixture["decision"]
    null = metrics.get("null", {})
    positive = metrics.get("positive", {})
    qualifies = (
        null.get("naive_stop_rate", 0) >= gate["null_naive_false_stop_min"]
        and null.get("cs_stop_rate", 1) <= gate["null_cs_false_stop_max"]
        and positive.get("cs_stop_rate", 0) >= gate["positive_cs_detection_min"]
        and positive.get("leaky_stop_rate", 0) <= gate["leaky_positive_detection_max"]
        and positive.get("leaky_max_abs_mean", math.inf) <= gate["leaky_estimate_abs_max"]
    )
    disposition = "HOLD_AUDIT" if errors or not all(mutations) else (
        "PASS_METHOD_SCOPED" if qualifies else "FAIL_METHOD_GATE")
    result = {
        "allocation": fixture["allocation"],
        "raw_rows": len(raw_lines),
        "expected_rows": expected_count,
        "replay_mismatches": sum(error.startswith("replay_mismatch:") for error in errors),
        "errors": errors,
        "corruption_controls_rejected": sum(mutations),
        "corruption_controls_total": len(mutations),
        "metrics": metrics,
        "frozen_gate_pass": qualifies,
        "disposition": disposition
    }
    Path(audit_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if disposition in ("PASS_METHOD_SCOPED", "FAIL_METHOD_GATE") and not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py FIXTURE.json RAW.jsonl AUDIT.json")
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))

