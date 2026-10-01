#!/usr/bin/env python3
"""Posthoc display/scorer alignment diagnosis for the retained transfer v2 run."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

OBS_KINDS = {"decision_start", "planner_return", "guard_invalid"}


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagnose(root: Path, threshold: float = 0.03, lookback_ms: float = 80.0) -> dict:
    summary = json.loads((root / "summary.json").read_text())
    for rel, expected in summary["raw_sha256"].items():
        actual = sha256(root / rel)
        if actual != expected:
            raise ValueError(f"raw hash mismatch {rel}: {actual} != {expected}")

    records = []
    for arm in sorted(path for path in root.iterdir() if path.is_dir()):
        score = load(arm / "score.jsonl")
        ctrl = load(arm / "controller.jsonl")
        for row in ctrl:
            if row.get("kind") not in OBS_KINDS:
                continue
            observed_x = (
                row.get("source_x") if row["kind"] == "decision_start"
                else row.get("current_x") if row["kind"] == "planner_return"
                else row.get("x")
            )
            capture_ns = row.get("capture_ns", row.get("observed_ns", row["ns"]))
            nearest = min(score, key=lambda sample: abs(sample["ns"] - capture_ns))
            priors = [
                sample for sample in score
                if 0 <= capture_ns - sample["ns"] <= int(lookback_ms * 1e6)
            ]
            prior = min(priors, key=lambda sample: abs(sample["x"] - observed_x)) if priors else None
            records.append({
                "arm": arm.name,
                "kind": row["kind"],
                "decision": row.get("decision"),
                "observed_x": observed_x,
                "capture_ns": capture_ns,
                "nearest_scorer_ns": nearest["ns"],
                "nearest_scorer_x": nearest["x"],
                "nearest_error": abs(observed_x - nearest["x"]),
                "nearest_dt_ms": (capture_ns - nearest["ns"]) / 1e6,
                "best_prior_scorer_ns": prior["ns"] if prior else None,
                "best_prior_scorer_x": prior["x"] if prior else None,
                "best_prior_error": abs(observed_x - prior["x"]) if prior else None,
                "best_prior_lag_ms": (capture_ns - prior["ns"]) / 1e6 if prior else None,
            })

    failed = [record for record in records if record["nearest_error"] >= threshold]
    return {
        "schema": "container-x11-bounded-recovery-transfer-v2-display-diagnosis-v1",
        "formal_disposition_preserved": summary["disposition"],
        "formal_threshold": threshold,
        "lookback_ms_posthoc": lookback_ms,
        "raw_streams_verified": len(summary["raw_sha256"]),
        "observation_count": len(records),
        "formal_threshold_failure_count": len(failed),
        "formal_nearest_error_max": max(record["nearest_error"] for record in records),
        "failed_best_prior_error_max": max((record["best_prior_error"] for record in failed), default=None),
        "failed_best_prior_lag_ms": [record["best_prior_lag_ms"] for record in failed],
        "failed_best_prior_lag_median_ms": (
            statistics.median(record["best_prior_lag_ms"] for record in failed)
            if failed else None
        ),
        "failed_observations": failed,
        "interpretation": (
            "Posthoc only. Failure observations align much more closely to scorer states tens of "
            "milliseconds before capture, consistent with asynchronous Tk/X11 presentation relative "
            "to scorer timestamps. This does not retroactively pass the frozen nearest-timestamp safety gate."
        ),
        "next_measurement": (
            "Bind scorer state to presented visual epoch (for example an on-screen render sequence "
            "or frame-present acknowledgement) rather than loosening the frozen 0.03 threshold."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = diagnose(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
