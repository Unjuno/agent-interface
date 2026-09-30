"""Run the bounded host-only TOCTOU comparison once and retain its raw output."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import race_guard
from test_race_guard import _trial, original


ROOT = Path(__file__).resolve().parents[3]
ALLOCATION_SOURCE = (
    "research/live_control/owner_keyup_formal_x11_5156_20261001_06/"
    "invoke_allocation.py"
)
GUARD_SOURCE = "research/analysis/owner_keyup_invocation_race_5156_t1_20261001/race_guard.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite an existing raw result; no retry")

    baseline = _trial(original.run_one_shot, rendezvous_after_gate=True)
    reserved = _trial(race_guard.run_reserved)
    paths = [ALLOCATION_SOURCE, GUARD_SOURCE]
    hashes = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in paths
    }
    raw = {
        "schema": "owner_keyup_invocation_race_5156_t1_v1",
        "hypothesis": "The check-then-write one-shot gate can admit two same-process concurrent dispatches; an atomic exclusive claim permits at most one.",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "observed_main": subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=ROOT, text=True
        ).strip(),
        "source_paths": {path: path for path in paths},
        "source_hashes": hashes,
        "test_schedule": {
            "baseline": "two threads rendezvous after both read the gate as clear, then dispatch against one shared temporary results directory",
            "atomic_claim": "two threads start together and contend on O_CREAT|O_EXCL reservation in one shared temporary directory",
        },
        "baseline": {
            "candidate_invocations": baseline["counts"]["candidate"],
            "audit_invocations": baseline["counts"]["audit"],
            "statuses": baseline["statuses"],
        },
        "atomic_claim": {
            "candidate_invocations": reserved["counts"]["candidate"],
            "audit_invocations": reserved["counts"]["audit"],
            "statuses": reserved["statuses"],
            "claim_state": reserved.get("INVOCATION_CLAIM.json", {}).get("state"),
        },
        "docker_invocations": 0,
        "x11_input_invocations": 0,
        "model_calls": 0,
        "interpretation": "Host-only deterministic schedule experiment. The frozen Allocation 06 package and its STOP record were read but not modified; this is not a formal X11 allocation result.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "baseline_candidates": raw["baseline"]["candidate_invocations"],
        "atomic_claim_candidates": raw["atomic_claim"]["candidate_invocations"],
        "raw": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
