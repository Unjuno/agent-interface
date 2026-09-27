#!/usr/bin/env python3
"""Fail-closed ownership selection for one-shot GitHub Actions allocations.

Ownership is observational only: among runs for one explicit workflow path + head SHA,
the earliest distinct run owns the launch. Later runs must stop before the formal step.
Completed prior runs continue to own the consumed allocation, preventing an accidental
second execution from becoming legitimate after the first job finishes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _runs(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("workflow_runs"), list):
        return payload["workflow_runs"]
    raise ValueError("expected list or workflow_runs[]")


def _rank(run: dict[str, Any]) -> tuple[int, int]:
    try:
        number = int(run["run_number"])
    except (KeyError, TypeError, ValueError):
        number = 2**63 - 1
    return number, int(run["id"])


def select_owner(payload: Any, *, current_run_id: int, workflow_path: str, head_sha: str, allocation_id: str) -> dict[str, Any]:
    current_run_id = int(current_run_id)
    unique: dict[int, dict[str, Any]] = {}
    malformed_matching = 0
    for raw in _runs(payload):
        if not isinstance(raw, dict):
            continue
        if raw.get("path") != workflow_path or raw.get("head_sha") != head_sha:
            continue
        try:
            run_id = int(raw["id"])
        except (KeyError, TypeError, ValueError):
            malformed_matching += 1
            continue
        unique[run_id] = raw
    if malformed_matching:
        return {"schema":"formal-allocation-launch-owner-v1","allocation_id":allocation_id,"workflow_path":workflow_path,"head_sha":head_sha,"current_run_id":current_run_id,"result_class":"UNCERTAIN_MALFORMED_MATCHING_RUN","may_enter_formal_step":False,"malformed_matching_count":malformed_matching}
    if current_run_id not in unique:
        return {"schema":"formal-allocation-launch-owner-v1","allocation_id":allocation_id,"workflow_path":workflow_path,"head_sha":head_sha,"current_run_id":current_run_id,"result_class":"UNCERTAIN_CURRENT_RUN_NOT_VISIBLE","may_enter_formal_step":False,"matching_run_ids":sorted(unique)}
    ordered = sorted(unique.values(), key=_rank)
    owner = ordered[0]
    owner_id = int(owner["id"])
    result_class = "PASS_CANONICAL_OWNER" if owner_id == current_run_id else "FAIL_NOT_CANONICAL_OWNER"
    return {"schema":"formal-allocation-launch-owner-v1","allocation_id":allocation_id,"workflow_path":workflow_path,"head_sha":head_sha,"current_run_id":current_run_id,"owner_run_id":owner_id,"owner_run_number":owner.get("run_number"),"matching_run_ids":[int(run["id"]) for run in ordered],"matching_run_count":len(ordered),"prior_completed_owner":owner_id != current_run_id and owner.get("status") == "completed","result_class":result_class,"may_enter_formal_step":owner_id == current_run_id,"claim_scope":"launch ownership only; no experiment success, authority, or cancellation claim"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_json", type=Path)
    ap.add_argument("--current-run-id", type=int, required=True)
    ap.add_argument("--workflow-path", required=True)
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--allocation-id", required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    payload = json.loads(args.runs_json.read_text(encoding="utf-8"))
    result = select_owner(payload,current_run_id=args.current_run_id,workflow_path=args.workflow_path,head_sha=args.head_sha,allocation_id=args.allocation_id)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["result_class"] == "PASS_CANONICAL_OWNER" else 2


if __name__ == "__main__":
    raise SystemExit(main())
