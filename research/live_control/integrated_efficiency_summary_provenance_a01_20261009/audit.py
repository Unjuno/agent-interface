#!/usr/bin/env python3
"""Bounded provenance audit for the legacy #2558 integrated-efficiency summary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
RESULTS = ROOT / "research/live_control/results"
SUMMARY = RESULTS / "integrated-efficiency-live-01-summary.json"
TRACE_DIR = RESULTS / "integrated-efficiency-live-01"
EXPECTED_FILES = {
    "research/live_control/formal_host_exec_broker_v1.py",
    "research/live_control/results/integrated-efficiency-live-01-summary.json",
}
ARMS = ("plain", "ephemeral", "persistent")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    pr = read(INPUTS / "pr-2962.json")
    pr_files = read(INPUTS / "pr-2962-files.json")
    issue_comment = read(INPUTS / "issue-2558-final-comment.json")
    summary = read(SUMMARY)
    trace = read(TRACE_DIR / "trace.json")
    report = read(TRACE_DIR / "report.json")
    prior_reconciliation = read(RESULTS / "integrated-efficiency-live-01-summary-reconciliation-v1.json")

    changed_files = {row["filename"] for row in pr_files}
    commit_files = set((INPUTS / "merge-commit-paths.txt").read_text(
        encoding="utf-8-sig").splitlines())
    pr_body = pr.get("body", "")
    comment_body = issue_comment.get("body", "")

    require(pr.get("number") == 2962 and pr.get("merged") is True,
            "PR #2962 is not the retained merged source", errors)
    require(changed_files == EXPECTED_FILES and commit_files == EXPECTED_FILES,
            "PR/merge diff is not exactly broker + aggregate summary", errors)
    require("fresh Docker allocation" in pr_body
            and ("新規allocation" in comment_body or "new allocation" in comment_body.lower()),
            "primary records do not identify a separate fresh allocation", errors)
    require(summary.get("source_main_commit") == "9c9d7cf2bea50e47638c63effa72a5059fdb4e58",
            "summary source-main identity differs from PR source", errors)
    require(summary["source_main_commit"] in pr_body
            and summary["source_main_commit"][:7] in comment_body,
            "source-main identity is not corroborated by both publication records", errors)
    require(summary.get("study") == "integrated-efficiency-live-01"
            and summary.get("seed") == 991028, "summary study identity mismatch", errors)

    raw_by_id = {}
    for path in sorted((TRACE_DIR / "model-calls").rglob("result.json")):
        row = read(path)
        call_id = row.get("call_id")
        require(bool(call_id) and call_id not in raw_by_id,
                f"missing/duplicate raw call id at {path.relative_to(ROOT)}", errors)
        if call_id:
            raw_by_id[call_id] = row

    per_arm = {}
    trace_ids = []
    for arm in ARMS:
        preflight = trace["preflight_calls"][arm]
        calls = [preflight]
        calls.extend(call for task in trace["arms"][arm] for call in task["model_calls"])
        trace_ids.extend(call["call_id"] for call in calls)
        raw_joined = [raw_by_id.get(call["call_id"]) for call in calls
                      if call.get("stage") != "schema_preflight"]
        require(all(row is not None for row in raw_joined),
                f"missing per-call raw result for {arm}", errors)
        require(all(row["usage"] == call["usage"] for row, call in zip(
            raw_joined, [call for call in calls if call.get("stage") != "schema_preflight"]
        ) if row is not None), f"raw usage join mismatch for {arm}", errors)
        trace_input = sum(call["usage"]["input_tokens"] for call in calls)
        report_input = report["evaluation"]["arms"][arm]["cumulative_input_tokens"][-1]
        summary_input = next(row["input_tokens_total"] for row in summary["arms"]
                             if row["arm"] == arm)
        prior_input = prior_reconciliation["per_arm"][arm]["trace_plus_preflight_usage"]["input_tokens"]
        per_arm[arm] = {
            "trace_plus_preflight_input_tokens": trace_input,
            "report_final_input_tokens": report_input,
            "prior_raw_reconciliation_input_tokens": prior_input,
            "separate_allocation_summary_input_tokens": summary_input,
            "summary_minus_reconciled_delta": summary_input - trace_input,
            "raw_model_result_count_joined": len(raw_joined),
        }
        require(trace_input == report_input == prior_input,
                f"detailed retained run does not reconcile for {arm}", errors)
        require(summary_input != trace_input,
                f"summary unexpectedly matches detailed run for {arm}", errors)

    require(len(trace_ids) == len(set(trace_ids)), "trace call IDs are not globally unique", errors)
    require(len(raw_by_id) == 14, "detailed-run raw result count changed from 14", errors)
    require(issue_comment.get("id") == 5744587624,
            "captured Issue #2558 result comment identity mismatch", errors)

    output = {
        "schema": "integrated_efficiency_summary_provenance_a01_v1",
        "disposition": "ALLOCATION_ORIGIN_IDENTIFIED_RAW_USAGE_NOT_RECONSTRUCTABLE",
        "scope": "Read-only audit of public repository, merged PR #2962 and its linked Issue #2558 outcome; no model, GUI, container, or formal allocation run.",
        "pr_number": pr["number"],
        "pr_merge_commit": "13d0ccbf2559cc1f70aa2652497ae941ceb13eb7",
        "checked_repository_head": "743ae74ec5be2472ff27fa06fe13d5ecf8534de5",
        "pr_changed_files": sorted(changed_files),
        "summary_source_main_commit": summary["source_main_commit"],
        "summary_study_seed": [summary["study"], summary["seed"]],
        "separate_allocation_claim_present_in_pr_and_issue": not any(
            "primary records do not identify a separate fresh allocation" == error for error in errors
        ),
        "per_arm": per_arm,
        "detailed_raw_model_result_records": len(raw_by_id),
        "summary_allocation_per_call_receipts_in_pr_diff": any(
            name.endswith(("result.json", "events.jsonl", "trace.json"))
            for name in changed_files
        ),
        "retained_summary_values_recomputed_from_that_allocation": False,
        "no_pooling_or_relabeling": True,
        "errors": errors,
    }
    if args.write:
        (HERE / "result.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
