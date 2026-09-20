"""Independent audit for the source-instrumented tic-entry construction run."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw_path: Path) -> dict:
    rows = json.loads(raw_path.read_text())
    errors: list[str] = []
    summaries = []
    for i, row in enumerate(rows):
        if row.get("repetition") != i:
            errors.append(f"row {i}: repetition mismatch")
        if row.get("setup") != "initialized" or row.get("mode") != "Mode.ASYNC_SPECTATOR":
            errors.append(f"row {i}: setup or mode mismatch")
        if row.get("ticrate") != 35 or row.get("wad_sha256") != "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b":
            errors.append(f"row {i}: fixture mismatch")
        if row.get("scorer_status") != "returned" or not row.get("closed"):
            errors.append(f"row {i}: scorer or cleanup incomplete")
        if row.get("advancing_api_calls") != 0:
            errors.append(f"row {i}: advancing API call observed")
        if row.get("initial_api_tic") != row.get("final_api_tic"):
            errors.append(f"row {i}: API tic changed during passive interval")
        entries = row.get("tic_entries", [])
        if len(entries) < 10:
            errors.append(f"row {i}: too few engine entry records ({len(entries)})")
        times = [e["monotonic_ns"] for e in entries]
        if any(b <= a for a, b in zip(times, times[1:])):
            errors.append(f"row {i}: entry timestamps are not strictly increasing")
        if any(b["viz_time"] != a["viz_time"] + 1 for a, b in zip(entries, entries[1:])):
            errors.append(f"row {i}: viz_time sequence is not contiguous")
        api_trace = row.get("scorer_api_trace", [])
        if len(api_trace) != 8:
            errors.append(f"row {i}: expected 8 exact scorer getter records, got {len(api_trace)}")
        gaps = [b - a for a, b in zip(times, times[1:])]
        getter_results = []
        for call in api_trace:
            start = call.get("start_ns")
            if start is None:
                errors.append(f"row {i}: getter has no start timestamp")
                continue
            left_candidates = [j for j, t in enumerate(times) if t <= start]
            right = next((j for j, t in enumerate(times) if t > start), None)
            left = left_candidates[-1] if left_candidates else None
            if left is None or right is None or right != left + 1:
                errors.append(f"row {i}: getter not bracketed by adjacent tic-entry records")
                continue
            period = times[right] - times[left]
            getter_results.append({
                "getter": call.get("name"), "preceding_viz_time": entries[left]["viz_time"],
                "following_viz_time": entries[right]["viz_time"],
                "elapsed_after_entry_ns": start - times[left],
                "period_ns": period,
                "phase_fraction": (start - times[left]) / period,
                "call_span_ns": call["end_ns"] - start,
                "between_entry_clock_samples": True,
            })
        summaries.append({
            "repetition": i, "entry_count": len(entries),
            "entry_interval_min_ns": min(gaps) if gaps else None,
            "entry_interval_median_ns": statistics.median(gaps) if gaps else None,
            "entry_interval_max_ns": max(gaps) if gaps else None,
            "scorer_getters": getter_results,
        })
    return {
        "schema": "source-instrumented-viz-tic-entry-audit-v1",
        "decision": "PASS_CONSTRUCTION_ONLY_ENTRY_CLOCK_CORRELATION" if not errors else "FAIL_AUDIT",
        "formal_allocation": False, "errors": errors,
        "limitations": [
            "The CLOCK_MONOTONIC sample is the first operation in a helper called at VIZ_Tic entry, not a hardware function-entry timestamp; the sample occurs after function entry and call/clock-read latency is not bounded by this construction.",
            "The trace file append happens after timestamp acquisition but still perturbs engine scheduling; it is not an uninstrumented formal distribution.",
            "CLOCK_MONOTONIC is shared across processes on this Linux fixture; this does not establish portability or hard-real-time timing.",
            "The three construction sessions do not fill the frozen 120-row schedule or authorize formal collection.",
        ],
        "raw_sha256": sha(raw_path), "rows": summaries,
    }


if __name__ == "__main__":
    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    report = audit(source)
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": report["decision"], "errors": report["errors"],
                      "formal_allocation": False,
                      "rows": len(report["rows"])}, sort_keys=True))
    raise SystemExit(bool(report["errors"]))
