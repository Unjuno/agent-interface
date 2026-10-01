#!/usr/bin/env python3
"""Detect concurrent duplicate GitHub Actions executions for one frozen allocation.

The guard is deliberately narrow: it only reasons about GitHub Actions run metadata
for an explicitly supplied workflow path, head SHA, and allocation identifier. It
never infers task success, cancels runs, or treats completed historical runs as an
active conflict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ACTIVE = {"queued", "in_progress", "waiting", "requested", "pending"}


def _as_runs(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("workflow_runs"), list):
        return payload["workflow_runs"]
    raise ValueError("expected a run list or an object with workflow_runs[]")


def inspect_runs(
    payload: Any,
    *,
    workflow_path: str,
    head_sha: str,
    allocation_id: str,
) -> dict[str, Any]:
    runs = _as_runs(payload)
    unique: dict[int, dict[str, Any]] = {}
    malformed: list[dict[str, Any]] = []

    for run in runs:
        try:
            run_id = int(run["id"])
            path = str(run["path"])
            sha = str(run["head_sha"])
            status = str(run["status"])
        except (KeyError, TypeError, ValueError):
            malformed.append(run if isinstance(run, dict) else {"raw": repr(run)})
            continue
        if path != workflow_path or sha != head_sha:
            continue
        unique[run_id] = run

    active = sorted(
        (
            {
                "id": run_id,
                "run_number": run.get("run_number"),
                "run_attempt": run.get("run_attempt"),
                "event": run.get("event"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
            }
            for run_id, run in unique.items()
            if str(run.get("status")) in ACTIVE
        ),
        key=lambda row: row["id"],
    )

    result_class = "PASS_SINGLE_ACTIVE" if len(active) <= 1 else "FAIL_DUPLICATE_ACTIVE"
    return {
        "schema": "duplicate-formal-allocation-guard-v1",
        "allocation_id": allocation_id,
        "workflow_path": workflow_path,
        "head_sha": head_sha,
        "matching_unique_runs": len(unique),
        "active_matching_runs": active,
        "active_count": len(active),
        "malformed_count": len(malformed),
        "result_class": result_class,
        "safe_to_launch_another": len(active) == 0,
        "claim_scope": (
            "GitHub Actions launch multiplicity only; no claim about experiment validity, "
            "task outcome, or whether an already-running job should be cancelled."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_json", type=Path)
    parser.add_argument("--workflow-path", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--allocation-id", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.runs_json.read_text(encoding="utf-8"))
    result = inspect_runs(
        payload,
        workflow_path=args.workflow_path,
        head_sha=args.head_sha,
        allocation_id=args.allocation_id,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 2 if result["result_class"] == "FAIL_DUPLICATE_ACTIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
