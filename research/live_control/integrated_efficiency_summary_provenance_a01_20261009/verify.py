#!/usr/bin/env python3
"""Independent receipt/hash and outcome verifier for provenance audit A01."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARMS = ("plain", "ephemeral", "persistent")
EXPECTED = {
    "plain": (63128, 131517),
    "ephemeral": (63779, 136473),
    "persistent": (26563, 56403),
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    freeze = read(HERE / "FREEZE.json")
    errors = []
    for row in freeze["inputs"]:
        path = HERE / row["path"] if row["path"].startswith(("audit.py", "verify.py", "manifest.py", "EXECUTION.json", "CONSTRUCTION_FAILURE", "inputs/")) else ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            errors.append(f"frozen input mismatch: {row['path']}")

    api_files = {row["filename"] for row in read(HERE / "inputs/pr-2962-files.json")}
    git_files = set((HERE / "inputs/merge-commit-paths.txt").read_text(
        encoding="utf-8-sig").splitlines())
    if api_files != git_files:
        errors.append("GitHub PR files and frozen merge-commit path list differ")
    if any(name.endswith(("result.json", "events.jsonl", "trace.json")) for name in api_files):
        errors.append("PR diff contains an unexpected per-call receipt path")

    result = read(HERE / "result.json")
    if result.get("errors") != []:
        errors.append("candidate audit has errors")
    if result.get("disposition") != "ALLOCATION_ORIGIN_IDENTIFIED_RAW_USAGE_NOT_RECONSTRUCTABLE":
        errors.append("unexpected candidate disposition")
    for arm in ARMS:
        row = result["per_arm"][arm]
        if (row["trace_plus_preflight_input_tokens"],
                row["separate_allocation_summary_input_tokens"]) != EXPECTED[arm]:
            errors.append(f"unexpected token totals for {arm}")
        if row["trace_plus_preflight_input_tokens"] != row["report_final_input_tokens"]:
            errors.append(f"trace/report mismatch for {arm}")
        if row["raw_model_result_count_joined"] != (6 if arm != "persistent" else 2):
            errors.append(f"raw call join count mismatch for {arm}")

    summary = read(ROOT / "research/live_control/results/integrated-efficiency-live-01-summary.json")
    trace = read(ROOT / "research/live_control/results/integrated-efficiency-live-01/trace.json")
    for arm in ARMS:
        calls = [trace["preflight_calls"][arm]]
        calls += [call for task in trace["arms"][arm] for call in task["model_calls"]]
        total = sum(call["usage"]["input_tokens"] for call in calls)
        legacy = next(row["input_tokens_total"] for row in summary["arms"] if row["arm"] == arm)
        if (total, legacy) != EXPECTED[arm]:
            errors.append(f"independent trace/summary recount mismatch for {arm}")

    output = {"verifier": "PASS" if not errors else "FAIL",
              "frozen_inputs_checked": len(freeze["inputs"]),
              "api_merge_file_lists_match": api_files == git_files,
              "arms_checked": len(ARMS), "errors": errors}
    if args.write:
        (HERE / "verification.json").write_text(json.dumps(output, indent=2) + "\n",
                                                encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
