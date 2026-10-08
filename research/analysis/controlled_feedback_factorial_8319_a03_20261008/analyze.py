#!/usr/bin/env python3
"""Analyze the immutable #8319 A01 factorial rows without rerunning its candidate."""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_SHA256 = "ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d"
FEEDBACKS = ("CONTROLLED", "FULL")
UPDATERS = ("CASE_PATCH", "STRATUM_PATCH")
METRICS = ("dev_accuracy", "fresh_accuracy", "optimism")
SEEDS = tuple(range(100))


def _exact_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    return value


def validate_rows(rows: object) -> dict[tuple[str, str, int], dict[str, object]]:
    if type(rows) is not list or len(rows) != 400:
        raise ValueError("expected exactly 400 raw rows")
    indexed: dict[tuple[str, str, int], dict[str, object]] = {}
    for row in rows:
        if type(row) is not dict:
            raise ValueError("every row must be an object")
        updater = row.get("updater")
        feedback = row.get("feedback")
        seed = _exact_int(row.get("seed"), "seed")
        if updater not in UPDATERS or feedback not in FEEDBACKS or seed not in SEEDS:
            raise ValueError("unknown factorial cell or seed")
        key = (updater, feedback, seed)
        if key in indexed:
            raise ValueError(f"duplicate factorial row {key!r}")
        if (_exact_int(row.get("query_count"), "query_count") != 5 or
                _exact_int(row.get("safety_veto_count"), "safety_veto_count") != 1 or
                row.get("candidate_locked_before_fresh") is not True or
                row.get("raw_released_after_lock") is not True):
            raise ValueError(f"frozen accounting invariant failed for {key!r}")
        dev = Fraction(_exact_int(row.get("dev_correct"), "dev_correct"),
                       _exact_int(row.get("dev_total"), "dev_total"))
        fresh = Fraction(_exact_int(row.get("fresh_correct"), "fresh_correct"),
                          _exact_int(row.get("fresh_total"), "fresh_total"))
        if row.get("dev_total") != 32 or row.get("fresh_total") != 32:
            raise ValueError(f"unexpected cohort denominator for {key!r}")
        optimism = Fraction(str(row.get("optimism")))
        if optimism != dev - fresh:
            raise ValueError(f"optimism does not equal development minus fresh for {key!r}")
        indexed[key] = row
    expected = {(u, f, s) for u in UPDATERS for f in FEEDBACKS for s in SEEDS}
    if set(indexed) != expected:
        raise ValueError("factorial cell/seed frame is incomplete")
    return indexed


def _metric(row: dict[str, object], name: str) -> Fraction:
    if name == "dev_accuracy":
        return Fraction(row["dev_correct"], row["dev_total"])
    if name == "fresh_accuracy":
        return Fraction(row["fresh_correct"], row["fresh_total"])
    if name == "optimism":
        return Fraction(str(row["optimism"]))
    raise ValueError(f"unknown metric {name}")


def _distribution(values: list[Fraction]) -> dict[str, object]:
    if len(values) != 100:
        raise ValueError("each registered contrast must contain 100 paired seeds")
    ordered = sorted(values)
    middle = (ordered[49] + ordered[50]) / 2
    return {
        "n": len(values),
        "mean_fraction": str(sum(values, Fraction()) / len(values)),
        "median_fraction": str(middle),
        "min_fraction": str(ordered[0]),
        "max_fraction": str(ordered[-1]),
        "positive": sum(value > 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "negative": sum(value < 0 for value in values),
    }


def summarize(rows: object, input_sha256: str) -> dict[str, object]:
    indexed = validate_rows(rows)
    cells: dict[str, object] = {}
    for updater in UPDATERS:
        cells[updater] = {}
        for feedback in FEEDBACKS:
            cell = [indexed[(updater, feedback, seed)] for seed in SEEDS]
            cells[updater][feedback] = {
                "n": len(cell),
                "metrics": {
                    metric: _distribution([_metric(row, metric) for row in cell])
                    for metric in METRICS
                },
                "safety_vetoes": sum(row["safety_veto_count"] for row in cell),
            }

    feedback_effects: dict[str, object] = {}
    for updater in UPDATERS:
        feedback_effects[updater] = {
            metric: _distribution([
                _metric(indexed[(updater, "FULL", seed)], metric) -
                _metric(indexed[(updater, "CONTROLLED", seed)], metric)
                for seed in SEEDS
            ]) for metric in METRICS
        }

    update_rule_effects: dict[str, object] = {}
    for feedback in FEEDBACKS:
        update_rule_effects[feedback] = {
            metric: _distribution([
                _metric(indexed[("CASE_PATCH", feedback, seed)], metric) -
                _metric(indexed[("STRATUM_PATCH", feedback, seed)], metric)
                for seed in SEEDS
            ]) for metric in METRICS
        }

    interactions = {
        metric: _distribution([
            (_metric(indexed[("CASE_PATCH", "FULL", seed)], metric) -
             _metric(indexed[("CASE_PATCH", "CONTROLLED", seed)], metric)) -
            (_metric(indexed[("STRATUM_PATCH", "FULL", seed)], metric) -
             _metric(indexed[("STRATUM_PATCH", "CONTROLLED", seed)], metric))
            for seed in SEEDS
        ]) for metric in METRICS
    }
    return {
        "schema": "feedback-update-rule-factorial-analysis-v1",
        "input_sha256": input_sha256,
        "rows": len(indexed),
        "seeds_per_cell": len(SEEDS),
        "cell_summaries": cells,
        "feedback_full_minus_controlled_within_updater": feedback_effects,
        "update_case_minus_stratum_within_feedback": update_rule_effects,
        "interaction_case_minus_stratum_of_feedback_effect": interactions,
        "inference": "finite authored 100-seed fixture only; no p-value or population inference",
    }


def analyze(input_path: Path, output_path: Path) -> dict[str, object]:
    raw_bytes = input_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("immutable A01 raw SHA-256 mismatch")
    rows = json.loads(raw_bytes.decode("utf-8"))
    result = summarize(rows, digest)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: analyze.py IMMUTABLE_A01_RAW.json ANALYSIS.json", file=sys.stderr)
        return 2
    try:
        result = analyze(Path(argv[1]), Path(argv[2]))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"STOP_ANALYSIS_INPUT_OR_CONTRACT: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS_ANALYSIS_SCOPED", "rows": result["rows"],
                      "input_sha256": result["input_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
