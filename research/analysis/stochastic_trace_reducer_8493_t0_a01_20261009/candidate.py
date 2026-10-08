#!/usr/bin/env python3
"""One-shot candidate: compare pooled and temporal-block confirmation rules."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from spec import (
    alpha_tail, decision, digest_file, load_fixture, paired_counts, response,
    risk_difference_interval,
)


def summarize(rows: list[dict], windows: list[dict], fixture: dict) -> dict:
    alpha = alpha_tail(fixture)
    pooled_counts = paired_counts(rows)
    pooled_interval = risk_difference_interval(pooled_counts, alpha)
    pooled_decision = decision(pooled_interval, fixture["noninferiority_margin"])
    window_results = []
    for window in windows:
        block_rows = [row for row in rows if row["window_id"] == window["id"]]
        counts = paired_counts(block_rows)
        interval = risk_difference_interval(counts, alpha)
        window_results.append({"window_id": window["id"], "kind": window["kind"],
                               "counts": counts, "interval": interval,
                               "decision": decision(interval, fixture["noninferiority_margin"])})
    if any(item["kind"] == "ambiguous" for item in window_results):
        block_decision = "UNKNOWN_TRANSITION_WINDOW"
    elif any(item["counts"]["n"] < fixture["minimum_block_support"] for item in window_results):
        block_decision = "UNKNOWN_INSUFFICIENT_BLOCK_SUPPORT"
    elif any(item["decision"] == "FAIL_NONINFERIORITY" for item in window_results):
        block_decision = "FAIL_BLOCK_NONINFERIORITY"
    elif all(item["decision"] == "PASS_NONINFERIOR" for item in window_results):
        block_decision = "PASS_ALL_BLOCKS_NONINFERIOR"
    else:
        block_decision = "UNKNOWN_BLOCK_INTERVAL"
    return {"pooled": {"counts": pooled_counts, "interval": pooled_interval,
                       "decision": pooled_decision},
            "blocks": window_results, "block_decision": block_decision}


def build_raw(fixture: dict, fixture_digest: str) -> dict:
    cases = []
    for case in fixture["cases"]:
        rows = []
        for window in case["windows"]:
            for offset in range(window["n"]):
                slot = window["start"] + offset
                seed = window["seed_start"] + offset
                base = response(fixture["base_trace"], seed, window, fixture)
                reduced = response(fixture["reduced_trace"], seed, window, fixture)
                rows.append({"case_id": case["id"], "window_id": window["id"],
                             "window_kind": window["kind"], "slot": slot, "seed": seed,
                             "base_events": list(fixture["base_trace"]),
                             "reduced_events": list(fixture["reduced_trace"]),
                             "base": base, "reduced": reduced})
        summary = summarize(rows, case["windows"], fixture)
        cases.append({"case_id": case["id"], "role": case["role"],
                      "rows": rows, "summary": summary})
    return {"schema": "unjuno.issue8493.candidate.raw.v1",
            "fixture_sha256": fixture_digest,
            "expected_fixture_sha256": fixture_digest,
            "methods": ["POOLED_CONFIRMATION", "BLOCK_CONDITIONAL_CONFIRMATION"],
            "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze-digest", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    freeze_path = package / "FREEZE.json"
    freeze_digest = digest_file(freeze_path)
    if freeze_digest != args.freeze_digest:
        raise SystemExit("FREEZE_DIGEST_MISMATCH")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for rel, expected in freeze["files"].items():
        if digest_file(package / rel) != expected:
            raise SystemExit("FROZEN_SOURCE_MISMATCH:" + rel)
    fixture_path = package / "fixture.json"
    fixture_digest = digest_file(fixture_path)
    if fixture_digest != freeze["fixture_sha256"]:
        raise SystemExit("FIXTURE_DIGEST_MISMATCH")
    raw = build_raw(load_fixture(), fixture_digest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": "complete", "case_count": len(raw["cases"]),
                      "paired_rows": sum(len(c["rows"]) for c in raw["cases"]),
                      "fixture_sha256": fixture_digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
