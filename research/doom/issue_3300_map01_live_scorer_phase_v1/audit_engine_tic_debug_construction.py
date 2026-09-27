"""Audit VIZ_Tic engine progress brackets from a construction stdout capture."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TIC_RE = re.compile(r"VIZ_Tic: tic: (\d+), vizTime: (\d+)")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw_path: Path, log_path: Path) -> dict:
    raw = json.loads(raw_path.read_text())
    lines = log_path.read_text(errors="replace").splitlines()
    errors = []
    if len(raw) != 3:
        errors.append(f"expected 3 raw sessions, found {len(raw)}")
    summaries = []
    for repetition, row in enumerate(raw):
        begin_marker = f"RUN31_PASSIVE_BEGIN repetition={repetition}"
        end_marker = f"RUN31_PASSIVE_END repetition={repetition}"
        begin_matches = [i for i, line in enumerate(lines) if line == begin_marker]
        if len(begin_matches) != 1:
            errors.append(f"row {repetition}: expected exactly one begin marker")
            continue
        begin = begin_matches[0]
        end_matches = [i for i in range(begin + 1, len(lines)) if lines[i] == end_marker]
        if len(end_matches) != 1:
            errors.append(f"row {repetition}: expected exactly one end marker")
            continue
        end = end_matches[0]
        if row.get("repetition") != repetition or row.get("setup") != "initialized":
            errors.append(f"row {repetition}: raw identity/setup mismatch")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"row {repetition}: mode/ticrate mismatch")
        if row.get("advancing_api_calls") != 0:
            errors.append(f"row {repetition}: advancement call was recorded")
        if row.get("scorer_status") != "returned" or not row.get("closed"):
            errors.append(f"row {repetition}: scorer/cleanup gate failed")
        if row.get("initial_api_tic") != row.get("final_api_tic"):
            errors.append(f"row {repetition}: exposed API tic changed")
        if any(s.get("api_tic") != row.get("initial_api_tic") for s in row.get("samples", [])):
            errors.append(f"row {repetition}: API tic changed within samples")
        ticks = []
        for line in lines[begin + 1:end]:
            match = TIC_RE.search(line)
            if match:
                ticks.append((int(match.group(1)), int(match.group(2))))
        contiguous = all(
            ticks[i + 1][0] == ticks[i][0] + 1
            and ticks[i + 1][1] == ticks[i][1] + 1
            for i in range(len(ticks) - 1)
        )
        if len(ticks) < 40 or not contiguous:
            errors.append(f"row {repetition}: internal tic trace is short or non-contiguous")
        elapsed = row.get("elapsed_ns", 0)
        increments = max(0, ticks[-1][0] - ticks[0][0]) if ticks else 0
        min_rate = increments / (elapsed / 1e9) if elapsed else None
        summaries.append({
            "repetition": repetition,
            "passive_elapsed_ns": elapsed,
            "samples": len(row.get("samples", [])),
            "python_api_tic": row.get("initial_api_tic"),
            "internal_tic_log_count": len(ticks),
            "internal_tic_first_last": [ticks[0], ticks[-1]] if ticks else None,
            "internal_tic_consecutive": contiguous,
            "within_window_minimum_mean_tic_rate_hz": min_rate,
            "scorer_status": row.get("scorer_status"),
            "closed": row.get("closed"),
        })
    if errors:
        decision = "FAIL_AUDIT"
    else:
        decision = "PASS_CONSTRUCTION_ONLY_INTERNAL_TIC_PROGRESS_API_SNAPSHOT_STALE"
    return {
        "schema": "engine-tic-debug-construction-audit-v1",
        "decision": decision,
        "formal_allocation": False,
        "instrumentation": "ViZDoom 1.3.0 VIZ_Tic debug level 2 with stdbuf line-buffered stdout",
        "limitations": [
            "debug printf can perturb scheduling; this is not formal allocation evidence",
            "ordered log boundaries establish progression/count, not sub-tic phase timestamps",
            "Python-visible MAP_TIC remained a stale snapshot throughout each interval",
        ],
        "rows": summaries,
        "errors": errors,
        "raw_sha256": sha(raw_path),
        "container_log_sha256": sha(log_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("container_log", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    report = audit(args.raw, args.container_log)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
