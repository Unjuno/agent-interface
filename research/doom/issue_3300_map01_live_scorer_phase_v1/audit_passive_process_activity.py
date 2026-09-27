"""Independent structural audit for construction-clock-30; never formal data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw_path: Path) -> dict:
    rows = json.loads(raw_path.read_text())
    errors = []
    if len(rows) != 3:
        errors.append(f"expected 3 sessions, found {len(rows)}")
    reps = [r.get("repetition") for r in rows]
    if reps != [0, 1, 2]:
        errors.append(f"unexpected repetition sequence: {reps}")
    summaries = []
    for row in rows:
        n = row.get("repetition")
        if row.get("setup") != "initialized":
            errors.append(f"row {n}: setup did not initialize")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR":
            errors.append(f"row {n}: wrong mode")
        if row.get("ticrate_readback") != 35:
            errors.append(f"row {n}: wrong ticrate")
        if row.get("wad_sha256") != "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b":
            errors.append(f"row {n}: wrong WAD")
        if row.get("advancing_api_calls") != 0:
            errors.append(f"row {n}: advancement API call count is not zero")
        if not row.get("closed"):
            errors.append(f"row {n}: cleanup did not close game")
        if row.get("scorer_status") != "returned":
            errors.append(f"row {n}: exact scorer did not return")
        samples = row.get("samples", [])
        if len(samples) < 20:
            errors.append(f"row {n}: fewer than 20 passive samples")
        if not row.get("process_clk_tck") or row.get("elapsed_ns", 0) < 1_400_000_000:
            errors.append(f"row {n}: incomplete process-clock calibration/window")
        for sample in samples:
            if sample.get("tic") != row.get("initial_tic"):
                errors.append(f"row {n}: exposed tic changed during passive interval")
        children = row.get("child_cpu_deltas", [])
        doom = [p for p in children if p.get("comm") == "vizdoom"]
        if len(doom) != 1:
            errors.append(f"row {n}: expected one matched ViZDoom child process")
        if any(p.get("end_state") not in ("S", "R") for p in doom):
            errors.append(f"row {n}: unexpected process state")
        if row.get("clock_progress_observed") is not False:
            errors.append(f"row {n}: clock-progress classification inconsistent")
        summaries.append({
            "repetition": n,
            "samples": len(samples),
            "initial_tic": row.get("initial_tic"),
            "final_tic": row.get("final_tic"),
            "elapsed_ns": row.get("elapsed_ns"),
            "process_clk_tck": row.get("process_clk_tck"),
            "child_cpu_deltas": children,
            "scorer_call_span_ns": row.get("scorer_call_span_ns"),
            "closed": row.get("closed"),
        })
    if errors:
        decision = "FAIL_AUDIT"
    elif all(r.get("final_tic") == r.get("initial_tic") for r in rows):
        decision = "HOLD_API_TIC_STATIC_PROCESS_ACTIVITY_UNRESOLVED"
    else:
        decision = "HOLD_PROCESS_ACTIVITY_DIAGNOSTIC_INCONCLUSIVE"
    return {
        "schema": "passive-process-activity-audit-v1",
        "scope": "construction-only; excluded from formal 120-row allocation",
        "decision": decision,
        "formal_allocation": False,
        "rows": summaries,
        "errors": errors,
        "raw_sha256": sha(raw_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    report = audit(args.raw)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
