"""Reconcile the retained #57 live report, model usage, and legacy summary.

This is read-only with respect to the frozen experiment. With --write it writes
only a new versioned reconciliation result beside the retained study artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-01"
SUMMARY = HERE / "results" / "integrated-efficiency-live-01-summary.json"
RESULT = HERE / "results" / "integrated-efficiency-live-01-summary-reconciliation-v1.json"
ARMS = ("plain", "ephemeral", "persistent")
FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_output_tokens")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_digest(repo: Path, relative_path: str) -> str | None:
    result = subprocess.run(["git", "show", f"HEAD:{relative_path}"], cwd=repo,
                            capture_output=True)
    if result.returncode:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    trace = read(OUT / "trace.json")
    report = read(OUT / "report.json")
    prior_audit = read(OUT / "audit.json")
    summary = read(SUMMARY)
    raw_by_id = {}
    duplicate_raw_ids = []
    for path in sorted((OUT / "model-calls").rglob("result.json")):
        row = read(path)
        call_id = row.get("call_id")
        if not call_id or call_id in raw_by_id:
            duplicate_raw_ids.append(str(path.relative_to(OUT)))
            continue
        raw_by_id[call_id] = {"usage": row.get("usage"),
                              "path": str(path.relative_to(OUT))}

    totals = {field: 0 for field in FIELDS}
    per_arm = {}
    call_ids = []
    mismatched_calls = []
    mismatched_report_totals = []
    for arm in ARMS:
        preflight = trace["preflight_calls"][arm]
        calls = [preflight]
        calls.extend(call for task in trace["arms"][arm]
                     for call in task["model_calls"])
        arm_totals = {field: 0 for field in FIELDS}
        arm_ids = []
        for call in calls:
            call_id = call["call_id"]
            call_ids.append(call_id)
            arm_ids.append(call_id)
            usage = call["usage"]
            if call["stage"] != "schema_preflight":
                raw = raw_by_id.get(call_id)
                if raw is None or raw["usage"] != usage:
                    mismatched_calls.append(call_id)
            for field in FIELDS:
                arm_totals[field] += usage[field]
                totals[field] += usage[field]
        expected_input = report["evaluation"]["arms"][arm]["cumulative_input_tokens"][-1]
        prior_input = prior_audit["final_input_tokens"][arm]
        summary_input = next(row["input_tokens_total"] for row in summary["arms"]
                             if row["arm"] == arm)
        if arm_totals["input_tokens"] != expected_input or prior_input != expected_input:
            mismatched_report_totals.append(arm)
        per_arm[arm] = {
            "trace_plus_preflight_usage": arm_totals,
            "report_final_input_tokens": expected_input,
            "prior_audit_final_input_tokens": prior_input,
            "legacy_summary_input_tokens": summary_input,
            "summary_delta_vs_report": summary_input - expected_input,
            "report_audit_and_attempt_usage_match": arm_totals["input_tokens"] == expected_input == prior_input,
            "raw_result_records_joined": sum(call_id in raw_by_id for call_id in arm_ids
                                              if call_id != preflight["call_id"]),
            "call_attempts_including_preflight": len(calls),
        }

    expected_from_raw = {field: 0 for field in FIELDS}
    for row in raw_by_id.values():
        for field in FIELDS:
            expected_from_raw[field] += row["usage"][field]
    for arm in ARMS:
        for field in FIELDS:
            expected_from_raw[field] += trace["preflight_calls"][arm]["usage"][field]

    pins = read(OUT / "preregistration.json")["sources"]
    root = HERE.parents[1]
    archived_prefixes = (
        "research/integration/compiled_comparison_57_4d74_20261004/source/research/live_control",
        "research/integration/planner_contract_56_4d74_20261004/source/research/live_control",
    )
    pin_status = {}
    for name, expected in pins.items():
        candidates = {"current_main": file_digest(HERE / name)}
        for index, candidate_root in enumerate(archived_prefixes, start=1):
            candidates[f"archive_{index}"] = git_digest(root, f"{candidate_root}/{name}")
        pin_status[name] = {
            "expected_sha256": expected,
            "available_sha256": candidates,
            "exact_copy_available": expected in candidates.values(),
        }

    report_input = {arm: per_arm[arm]["report_final_input_tokens"] for arm in ARMS}
    summary_input = {arm: per_arm[arm]["legacy_summary_input_tokens"] for arm in ARMS}
    output = {
        "schema": "integrated_efficiency_summary_reconciliation_v1",
        "study": "integrated-efficiency-live-01",
        "summary_source_main_commit": summary.get("source_main_commit"),
        "trace_usage_totals": totals,
        "raw_result_plus_preflight_usage_totals": expected_from_raw,
        "prior_audit_usage_totals": prior_audit["actual_usage_totals"],
        "raw_result_count": len(raw_by_id),
        "trace_call_count_including_preflights": len(call_ids),
        "trace_call_ids_unique": len(call_ids) == len(set(call_ids)),
        "raw_duplicate_ids": duplicate_raw_ids,
        "raw_usage_join_mismatches": mismatched_calls,
        "per_arm": per_arm,
        "legacy_summary_matches_report": summary_input == report_input,
        "report_usage_total_mismatches": mismatched_report_totals,
        "cached_input_semantics": "cached_input_tokens are reported as a subset of input_tokens and are not added to input totals",
        "pinned_source_hashes_all_reavailable": all(row["exact_copy_available"] for row in pin_status.values()),
        "pinned_source_hash_status": pin_status,
        "historical_allocation_disposition": prior_audit["disposition"],
        "independent_replay_disposition": "HOLD_SUMMARY_AND_FROZEN_SOURCE_RECONCILIATION",
    }
    if args.write:
        RESULT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    complete = (len(raw_by_id) == 14 and not duplicate_raw_ids
                and not mismatched_calls and len(call_ids) == len(set(call_ids))
                and not mismatched_report_totals
                and expected_from_raw == totals == prior_audit["actual_usage_totals"])
    # Exit 2 deliberately records a reproducible HOLD when retained summaries or
    # frozen source bytes do not reconcile. It never changes the historical result.
    return 0 if complete and output["legacy_summary_matches_report"] \
        and output["pinned_source_hashes_all_reavailable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
