from __future__ import annotations
import argparse
import json
import statistics
from pathlib import Path

ARMS = ("coast_control", "bounded_recovery")
PAIRS = (1, 2, 3)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def audit(root: Path) -> dict:
    construction = load(root / "construction.json")
    summary = load(root / "summary.json")
    failures = []
    if construction.get("allocation_id") != "map01-recovery-cover-mechanism-live-v3-01":
        failures.append("allocation_id")
    if construction.get("model_calls") != 0:
        failures.append("model_calls_nonzero")
    pairs = summary.get("pairs") or []
    if len(pairs) != 3:
        failures.append("pair_count")
    reductions = []
    negative = 0
    positive = 0
    for pair in pairs:
        index = pair.get("pair_index")
        if pair.get("failures"):
            failures.append(f"pair{index}:runner_failures")
        coast = pair.get("coast_no_retained_input_upper_ns")
        recovery = pair.get("recovery_no_retained_input_upper_ns")
        if not isinstance(coast, int) or not isinstance(recovery, int) or coast <= 0:
            failures.append(f"pair{index}:bounds")
        else:
            reduction = (coast - recovery) / coast
            reductions.append(reduction)
            if not recovery < coast:
                failures.append(f"pair{index}:continuity_not_improved")
        negative += int(pair.get("recovery_negative_event_count") or 0)
        positive += int(pair.get("recovery_positive_event_count") or 0)
    median = statistics.median(reductions) if reductions else None
    if median is None or median < 0.10:
        failures.append("median_reduction_below_10pct")
    if negative:
        failures.append("recovery_negative_event")

    arm_checks = []
    for index in PAIRS:
        for arm in ARMS:
            runtime = root / f"pair-{index:02d}" / arm / "runtime"
            events = jsonl(runtime / "events.jsonl")
            delivered = jsonl(runtime / "delivered.jsonl")
            if events != delivered:
                failures.append(f"pair{index}:{arm}:events_delivered_mismatch")
            leak = sum(
                1 for row in events
                if isinstance(row.get("schema"), str)
                and row["schema"].startswith("independent-progress-")
            )
            scorer = load(runtime / "scorer-summary.json")
            missed = (scorer.get("scheduler") or {}).get("missed_sample_periods")
            terminal_audit = load(root / f"pair-{index:02d}" / arm / "terminal-score-audit.json")
            terminal_ok = terminal_audit.get("pass") is True or terminal_audit.get("result") == "PASS"
            if leak:
                failures.append(f"pair{index}:{arm}:scorer_leak")
            if missed != 0:
                failures.append(f"pair{index}:{arm}:missed_periods")
            if not terminal_ok:
                failures.append(f"pair{index}:{arm}:terminal_score")
            arm_checks.append({
                "pair": index,
                "arm": arm,
                "scorer_leak_count": leak,
                "missed_sample_periods": missed,
                "terminal_score_agreement": terminal_ok,
            })

    if failures:
        decision = "FAIL" if any(
            "recovery_negative_event" in item
            or "runner_failures" in item
            or "terminal_score" in item
            for item in failures
        ) else "HOLD"
    else:
        decision = "PASS_MECHANISM_ONLY"
    return {
        "schema": "map01-recovery-cover-mechanism-v3-audit",
        "decision": decision,
        "pass": not failures,
        "failures": failures,
        "paired_reduction_fractions": reductions,
        "paired_median_reduction_fraction": median,
        "recovery_positive_event_count": positive,
        "recovery_negative_event_count": negative,
        "arm_checks": arm_checks,
        "claim_scope": "causal bounded-recovery mechanism under fixed simulated planner delay; zero model calls; not frontier-model efficacy",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
