"""Decision audit for the formal MAP01 bounded-recovery mechanism v4 block."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v4-01"
ARMS = ("coast_control", "bounded_recovery")
PAIRS = (1, 2, 3)


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _terminal_ok(path: Path) -> bool:
    row = load(path)
    return row.get("pass") is True or row.get("result") == "PASS"


def audit(root: Path) -> dict:
    root = Path(root)
    construction = load(root / "construction.json")
    summary = load(root / "summary.json")
    hard_failures: list[str] = []
    hold_reasons: list[str] = []
    reductions: list[float] = []
    recovery_positive = 0
    recovery_negative = 0
    arm_checks = []

    if construction.get("allocation_id") != ALLOCATION_ID:
        hard_failures.append("allocation_id")
    if construction.get("model_calls") != 0:
        hard_failures.append("model_calls_nonzero")
    if construction.get("planner_wait_ms") != 600:
        hard_failures.append("planner_wait_changed")

    pairs = summary.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 3:
        hard_failures.append("pair_count")
        pairs = []

    for pair in pairs:
        index = pair.get("pair_index")
        inherited = [x for x in (pair.get("failures") or []) if not str(x).endswith(":scorer_missed_period")]
        if inherited:
            hard_failures.append(f"pair{index}:runner_failures:{','.join(map(str, inherited))}")
        coast = pair.get("coast_no_retained_input_upper_ns")
        recovery = pair.get("recovery_no_retained_input_upper_ns")
        if not isinstance(coast, int) or not isinstance(recovery, int) or coast <= 0:
            hard_failures.append(f"pair{index}:bounds")
        else:
            reduction = (coast - recovery) / coast
            reductions.append(reduction)
            if recovery >= coast:
                hold_reasons.append(f"pair{index}:continuity_not_improved")
        recovery_positive += int(pair.get("recovery_positive_event_count") or 0)
        neg = int(pair.get("recovery_negative_event_count") or 0)
        recovery_negative += neg
        if neg:
            hard_failures.append(f"pair{index}:recovery_negative_event")

    missed_periods = []
    for index in PAIRS:
        for arm in ARMS:
            arm_root = root / f"pair-{index:02d}" / arm
            runtime = arm_root / "runtime"
            try:
                events = jsonl(runtime / "events.jsonl")
                delivered = jsonl(runtime / "delivered.jsonl")
                arm_summary = load(arm_root / "arm-summary.json")
                scorer = load(runtime / "scorer-summary.json")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                hard_failures.append(f"pair{index}:{arm}:missing_or_malformed:{type(exc).__name__}")
                continue
            if events != delivered:
                hard_failures.append(f"pair{index}:{arm}:events_delivered_mismatch")
            leak = sum(
                1 for row in events
                if isinstance(row.get("schema"), str)
                and row["schema"].startswith("independent-progress-")
            )
            if leak:
                hard_failures.append(f"pair{index}:{arm}:scorer_leak")
            terminal_path = arm_root / "terminal-score-audit.json"
            if not terminal_path.is_file() or not _terminal_ok(terminal_path):
                hard_failures.append(f"pair{index}:{arm}:terminal_score")
            if arm_summary.get("terminal_release_verified") is not True:
                hard_failures.append(f"pair{index}:{arm}:terminal_release")
            bounds = arm_summary.get("input_bounds") or {}
            if bounds.get("valid") is not True:
                hard_failures.append(f"pair{index}:{arm}:input_bounds")
            admissions = bounds.get("admission_count")
            if arm == "coast_control" and admissions != 0:
                hard_failures.append(f"pair{index}:{arm}:unexpected_input")
            if arm == "bounded_recovery" and (type(admissions) is not int or admissions < 1):
                hard_failures.append(f"pair{index}:{arm}:recovery_not_exposed")
            missed = (scorer.get("scheduler") or {}).get("missed_sample_periods")
            if type(missed) is not int or missed < 0:
                hard_failures.append(f"pair{index}:{arm}:invalid_missed_periods")
            else:
                missed_periods.append({"pair": index, "arm": arm, "missed": missed})
            arm_checks.append({
                "pair": index,
                "arm": arm,
                "admission_count": admissions,
                "measurement_class": bounds.get("measurement_class"),
                "scorer_leak_count": leak,
                "missed_sample_periods": missed,
            })

    median = statistics.median(reductions) if len(reductions) == 3 else None
    if median is None:
        hard_failures.append("reduction_count")
    elif median < 0.10:
        hold_reasons.append("paired_median_reduction_below_10pct")

    if hard_failures:
        decision = "FAIL"
    elif hold_reasons:
        decision = "HOLD"
    else:
        decision = "PASS_MECHANISM_ONLY"

    return {
        "schema": "map01-recovery-cover-mechanism-v4-audit",
        "allocation_id": ALLOCATION_ID,
        "decision": decision,
        "valid_experiment": not hard_failures,
        "promotable_mechanism_result": decision == "PASS_MECHANISM_ONLY",
        "hard_failures": hard_failures,
        "hold_reasons": hold_reasons,
        "paired_reduction_fractions": reductions,
        "paired_median_reduction_fraction": median,
        "recovery_positive_event_count": recovery_positive,
        "recovery_negative_event_count": recovery_negative,
        "scorer_missed_periods": missed_periods,
        "arm_checks": arm_checks,
        "claim_scope": "zero-model real-MAP01 bounded-recovery mechanism only; not frontier-model efficacy",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    return 0 if result["valid_experiment"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
