"""Audit same-container strace tic-log to Python-clock correlation (construction only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

TIC_RE = re.compile(
    r'^\s*(\d+)\s+(\d+\.\d+) write\(1, "VIZ_Tic: tic: (\d+), vizTime: (\d+)\\n",'
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_events(trace_path: Path) -> tuple[list[dict], int]:
    events = []
    precision_ns = 1
    for line in trace_path.read_text(errors="replace").splitlines():
        match = TIC_RE.search(line)
        if not match:
            continue
        pid, timestamp, tic, viz_time = match.groups()
        fractional = timestamp.partition(".")[2]
        resolution_ns = 10 ** max(0, 9 - len(fractional))
        precision_ns = max(precision_ns, resolution_ns)
        wall_ns = int(Decimal(timestamp) * Decimal(1_000_000_000))
        events.append({"pid": int(pid), "wall_ns": wall_ns,
                       "tic": int(tic), "viz_time": int(viz_time),
                       "resolution_ns": resolution_ns})
    return events, precision_ns


def audit(raw_path: Path, trace_path: Path) -> dict:
    rows = json.loads(raw_path.read_text())
    all_events, precision_ns = read_events(trace_path)
    errors = []
    if len(rows) != 3:
        errors.append(f"expected 3 repetitions, got {len(rows)}")
    summaries = []
    for repetition, row in enumerate(rows):
        if row.get("repetition") != repetition:
            errors.append(f"row {repetition}: repetition identity mismatch")
        if row.get("setup") != "initialized" or row.get("mode") != "Mode.ASYNC_SPECTATOR":
            errors.append(f"row {repetition}: setup/mode mismatch")
        if row.get("ticrate") != 35 or row.get("wad_sha256") != "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b":
            errors.append(f"row {repetition}: fixture identity mismatch")
        if row.get("scorer_status") != "returned" or not row.get("closed"):
            errors.append(f"row {repetition}: scorer/cleanup failed")
        if row.get("advancing_api_calls") != 0:
            errors.append(f"row {repetition}: advancing API call present")
        if row.get("initial_api_tic") != row.get("final_api_tic"):
            errors.append(f"row {repetition}: API tic changed")
        anchors = list(row.get("anchors", [])) + [
            row.get("scorer_call_start_anchor", {}),
            row.get("scorer_call_end_anchor", {}),
        ]
        offsets = []
        for anchor in anchors:
            if not all(k in anchor for k in ("wall_before_ns", "wall_after_ns", "monotonic_ns")):
                errors.append(f"row {repetition}: incomplete clock anchor")
                continue
            if anchor["wall_after_ns"] < anchor["wall_before_ns"]:
                errors.append(f"row {repetition}: reversed wall anchor")
            offsets.extend((anchor["wall_before_ns"] - anchor["monotonic_ns"],
                            anchor["wall_after_ns"] - anchor["monotonic_ns"]))
        if not offsets:
            continue
        offset_lo, offset_hi = min(offsets), max(offsets)
        local_anchors = [row.get("scorer_call_start_anchor", {}),
                         row.get("scorer_call_end_anchor", {})]
        local_offsets = []
        for anchor in local_anchors:
            if "monotonic_ns" in anchor:
                local_offsets.extend((anchor["wall_before_ns"] - anchor["monotonic_ns"],
                                      anchor["wall_after_ns"] - anchor["monotonic_ns"]))
        wall_lo = row["anchors"][0]["wall_before_ns"]
        end_anchor = row.get("post_scorer_end", row["scorer_call_end_anchor"])
        wall_hi = end_anchor["wall_after_ns"]
        events = [e for e in all_events if wall_lo <= e["wall_ns"] <= wall_hi]
        ticks = [e["tic"] for e in events]
        contiguous = all(b == a + 1 for a, b in zip(ticks, ticks[1:]))
        if len(events) < 40 or not contiguous:
            errors.append(f"row {repetition}: insufficient/non-contiguous tic log records ({len(events)})")
        mapped = []
        for event in events:
            half_res = (event["resolution_ns"] + 1) // 2
            mapped.append({
                **event,
                "mono_lo_ns": event["wall_ns"] - offset_hi - half_res,
                "mono_hi_ns": event["wall_ns"] - offset_lo + half_res,
            })
        interval_ns = [b["wall_ns"] - a["wall_ns"] for a, b in zip(events, events[1:])]
        getter_positions = []
        trace = row.get("scorer_api_trace", [])
        for getter in trace:
            start = getter.get("start_ns")
            if start is None:
                continue
            prior = [e for e in mapped if e["mono_hi_ns"] < start]
            following = [e for e in mapped if e["mono_lo_ns"] > start]
            overlap = [e for e in mapped if e["mono_lo_ns"] <= start <= e["mono_hi_ns"]]
            getter_positions.append({
                "getter": getter.get("name"), "start_ns": start,
                "preceding_logged_tic": prior[-1]["tic"] if prior else None,
                "next_logged_tic": following[0]["tic"] if following else None,
                "preceding_log_to_getter_start_ns_interval": (
                    [start - prior[-1]["mono_hi_ns"], start - prior[-1]["mono_lo_ns"]]
                    if prior else None
                ),
                "getter_start_to_next_log_ns_interval": (
                    [following[0]["mono_lo_ns"] - start,
                     following[0]["mono_hi_ns"] - start]
                    if following else None
                ),
                "timestamp_interval_overlap": bool(overlap),
            })
        summaries.append({
            "repetition": repetition,
            "api_tic": row.get("final_api_tic"),
            "passive_elapsed_ns": row.get("elapsed_ns"),
            "tic_write_count": len(events),
            "tic_first_last": [ticks[0], ticks[-1]] if ticks else None,
            "tic_sequence_contiguous": contiguous,
            "logged_tic_interval_min_ns": min(interval_ns) if interval_ns else None,
            "logged_tic_interval_median_ns": sorted(interval_ns)[len(interval_ns)//2] if interval_ns else None,
            "logged_tic_interval_max_ns": max(interval_ns) if interval_ns else None,
            "realtime_monotonic_offset_observed_width_ns": offset_hi - offset_lo,
            "scorer_local_clock_offset_observed_width_ns": (
                max(local_offsets) - min(local_offsets) if local_offsets else None
            ),
            "strace_timestamp_resolution_ns": precision_ns,
            "scorer_getter_positions_vs_logged_tics": getter_positions,
            "scorer_status": row.get("scorer_status"),
            "closed": row.get("closed"),
        })
    return {
        "schema": "strace-phase-construction-audit-v1",
        "decision": "FAIL_AUDIT" if errors else "PASS_CONSTRUCTION_ONLY_SAME_CLOCK_TIC_LOG_CORRELATION",
        "formal_allocation": False,
        "errors": errors,
        "limitations": [
            "VIZ_Tic records are timestamped at write syscall entry after the logger formats the line, not at function entry; pre-syscall logger latency is not independently bounded",
            "strace ptrace and line-buffered debug output perturb timing; this is construction-only",
            "the recorded values are positions relative to logged tic events, not validated formal phase intervals",
            "wall-to-monotonic offset bounds only cover the observed paired anchors and do not prove no clock step between them",
        ],
        "strace_event_count": len(all_events),
        "strace_timestamp_resolution_ns": precision_ns,
        "rows": summaries,
        "raw_sha256": digest(raw_path),
        "strace_sha256": digest(trace_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("strace", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    report = audit(args.raw, args.strace)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
