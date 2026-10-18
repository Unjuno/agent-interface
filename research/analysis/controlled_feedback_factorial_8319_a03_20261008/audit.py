#!/usr/bin/env python3
"""Independent raw-only audit of the #8319 A03 contrast analysis."""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_SHA256 = "ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d"
EXPECTED_ROWS = 400
SEED_VALUES = range(100)
CELL_NAMES = (("CASE_PATCH", "CONTROLLED"), ("CASE_PATCH", "FULL"),
              ("STRATUM_PATCH", "CONTROLLED"), ("STRATUM_PATCH", "FULL"))
OUTCOMES = ("dev_accuracy", "fresh_accuracy", "optimism")


def _exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{field} must be an exact integer")
    return value


def _outcome(row: dict[str, object], name: str) -> Fraction:
    if name == "dev_accuracy":
        return Fraction(row["dev_correct"], row["dev_total"])
    if name == "fresh_accuracy":
        return Fraction(row["fresh_correct"], row["fresh_total"])
    return Fraction(str(row["optimism"]))


def _dist(values: list[Fraction]) -> dict[str, object]:
    values = sorted(values)
    if len(values) != 100:
        raise ValueError("audit expected 100 paired values")
    return {
        "n": 100,
        "mean_fraction": str(sum(values, Fraction()) / 100),
        "median_fraction": str((values[49] + values[50]) / 2),
        "min_fraction": str(values[0]),
        "max_fraction": str(values[-1]),
        "positive": sum(value > 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "negative": sum(value < 0 for value in values),
    }


def _rebuild(raw: object, digest: str) -> dict[str, object]:
    if type(raw) is not list or len(raw) != EXPECTED_ROWS:
        raise ValueError("raw row count mismatch")
    by_cell: dict[tuple[str, str], dict[int, dict[str, object]]] = defaultdict(dict)
    for row in raw:
        if type(row) is not dict:
            raise ValueError("raw row is not an object")
        cell = (row.get("updater"), row.get("feedback"))
        seed = row.get("seed")
        if cell not in CELL_NAMES or type(seed) is not int or seed not in SEED_VALUES:
            raise ValueError("raw cell or seed is invalid")
        if seed in by_cell[cell]:
            raise ValueError("duplicate row in factorial cell")
        if (_exact_int(row.get("query_count"), "query_count") != 5 or
                _exact_int(row.get("safety_veto_count"), "safety_veto_count") != 1 or
                row.get("candidate_locked_before_fresh") is not True or
                row.get("raw_released_after_lock") is not True):
            raise ValueError("raw protocol invariant mismatch")
        if (_exact_int(row.get("dev_total"), "dev_total") != 32 or
                _exact_int(row.get("fresh_total"), "fresh_total") != 32 or
                type(row.get("dev_correct")) is not int or
                type(row.get("fresh_correct")) is not int):
            raise ValueError("raw outcome fields are invalid")
        expected_optimism = Fraction(row["dev_correct"] - row["fresh_correct"], 32)
        if Fraction(str(row.get("optimism"))) != expected_optimism:
            raise ValueError("raw optimism field mismatch")
        by_cell[cell][seed] = row
    expected_seeds = set(SEED_VALUES)
    if len(by_cell) != 4 or any(set(by_cell[cell]) != expected_seeds for cell in CELL_NAMES):
        raise ValueError("one or more cells lack exactly one row for each seed")

    cell_table: dict[str, object] = {}
    for updater, feedback in CELL_NAMES:
        group = list(by_cell[(updater, feedback)].values())
        metrics = {}
        for outcome in OUTCOMES:
            metrics[outcome] = _dist([_outcome(row, outcome) for row in group])
        cell_table.setdefault(updater, {})[feedback] = {
            "n": len(group), "metrics": metrics,
            "safety_vetoes": sum(row["safety_veto_count"] for row in group),
        }

    feedback_table: dict[str, object] = {}
    for updater in ("CASE_PATCH", "STRATUM_PATCH"):
        feedback_table[updater] = {}
        for outcome in OUTCOMES:
            differences = []
            for seed in SEED_VALUES:
                full = by_cell[(updater, "FULL")][seed]
                controlled = by_cell[(updater, "CONTROLLED")][seed]
                differences.append(_outcome(full, outcome) - _outcome(controlled, outcome))
            feedback_table[updater][outcome] = _dist(differences)

    update_table: dict[str, object] = {}
    for feedback in ("CONTROLLED", "FULL"):
        update_table[feedback] = {}
        for outcome in OUTCOMES:
            differences = []
            for seed in SEED_VALUES:
                exact = by_cell[("CASE_PATCH", feedback)][seed]
                transfer = by_cell[("STRATUM_PATCH", feedback)][seed]
                differences.append(_outcome(exact, outcome) - _outcome(transfer, outcome))
            update_table[feedback][outcome] = _dist(differences)

    interaction_table = {}
    for outcome in OUTCOMES:
        values = []
        for seed in SEED_VALUES:
            case = (_outcome(by_cell[("CASE_PATCH", "FULL")][seed], outcome) -
                    _outcome(by_cell[("CASE_PATCH", "CONTROLLED")][seed], outcome))
            stratum = (_outcome(by_cell[("STRATUM_PATCH", "FULL")][seed], outcome) -
                       _outcome(by_cell[("STRATUM_PATCH", "CONTROLLED")][seed], outcome))
            values.append(case - stratum)
        interaction_table[outcome] = _dist(values)
    return {
        "schema": "feedback-update-rule-factorial-analysis-v1",
        "input_sha256": digest,
        "rows": EXPECTED_ROWS,
        "seeds_per_cell": 100,
        "cell_summaries": cell_table,
        "feedback_full_minus_controlled_within_updater": feedback_table,
        "update_case_minus_stratum_within_feedback": update_table,
        "interaction_case_minus_stratum_of_feedback_effect": interaction_table,
        "inference": "finite authored 100-seed fixture only; no p-value or population inference",
    }


def _analysis_matches(supplied: object, expected: object) -> bool:
    return supplied == expected


def audit(raw_path: Path, analysis_path: Path, audit_path: Path) -> dict[str, object]:
    raw_bytes = raw_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    errors: list[str] = []
    if digest != EXPECTED_SHA256:
        errors.append("immutable_input_sha256_mismatch")
    try:
        reconstructed = _rebuild(json.loads(raw_bytes.decode("utf-8")), digest)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"raw_reconstruction:{type(exc).__name__}:{exc}")
        reconstructed = None
    try:
        supplied = json.loads(analysis_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"analysis_output:{type(exc).__name__}:{exc}")
        supplied = None
    if reconstructed is not None and not _analysis_matches(supplied, reconstructed):
        errors.append("analysis_output_differs_from_independent_reconstruction")

    mutations_rejected = 0
    mutation_total = 5
    if reconstructed is not None:
        probes = []
        altered = json.loads(json.dumps(reconstructed))
        altered["rows"] = 399
        probes.append(altered)
        altered = json.loads(json.dumps(reconstructed))
        del altered["cell_summaries"]["CASE_PATCH"]["FULL"]
        probes.append(altered)
        altered = json.loads(json.dumps(reconstructed))
        altered["interaction_case_minus_stratum_of_feedback_effect"]["optimism"]["mean_fraction"] = "0/1"
        probes.append(altered)
        altered = json.loads(json.dumps(reconstructed))
        altered["input_sha256"] = "0" * 64
        probes.append(altered)
        altered = json.loads(json.dumps(reconstructed))
        altered["feedback_full_minus_controlled_within_updater"]["CASE_PATCH"]["fresh_accuracy"]["n"] = 99
        probes.append(altered)
        for probe in probes:
            if not _analysis_matches(probe, reconstructed):
                mutations_rejected += 1
    status = "PASS_ANALYSIS_AUDIT_SCOPED" if not errors and mutations_rejected == mutation_total else "FAIL_ANALYSIS_AUDIT"
    record = {
        "status": status,
        "input_sha256": digest,
        "rows_reconstructed": EXPECTED_ROWS if reconstructed is not None and not errors else 0,
        "analysis_output_matches": reconstructed is not None and _analysis_matches(supplied, reconstructed),
        "mutation_controls": mutation_total,
        "mutations_rejected": mutations_rejected,
        "errors": errors,
        "scope": "independent reconstruction of retained finite raw; no candidate rerun or population inference",
    }
    audit_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: audit.py IMMUTABLE_RAW.json ANALYSIS.json AUDIT.json", file=sys.stderr)
        return 2
    try:
        record = audit(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    except OSError as exc:
        print(f"STOP_AUDIT_IO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": record["status"], "rows": record["rows_reconstructed"],
                      "mutations_rejected": record["mutations_rejected"], "errors": record["errors"]},
                     sort_keys=True))
    return 0 if record["status"] == "PASS_ANALYSIS_AUDIT_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
