"""Independent stdlib reconciliation for the excluded passive-clock probes."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def xwd_pixels(path: Path):
    payload = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    if len(payload) < 100:
        raise ValueError(f"short XWD: {path}")
    header = struct.unpack(">25I", payload[:100])
    header_size, width, height, bits_per_pixel, bytes_per_line, ncolors = (
        header[0], header[4], header[5], header[11], header[12], header[19]
    )
    pixel_offset = header_size + 12 * ncolors
    pixels = payload[pixel_offset:]
    if bits_per_pixel != 32 or len(pixels) != bytes_per_line * height:
        raise ValueError(f"unexpected XWD pixel layout: {path}")
    return width, height, bytes_per_line, pixels


def differing_pixels(left, right, width, height, stride):
    changed = []
    for y in range(height):
        for x in range(width):
            offset = y * stride + x * 4
            if left[offset:offset + 4] != right[offset:offset + 4]:
                changed.append((x, y))
    bounds = None if not changed else [
        min(x for x, _ in changed), min(y for _, y in changed),
        max(x for x, _ in changed), max(y for _, y in changed),
    ]
    return {"changed_pixels": len(changed), "total_pixels": width * height, "bbox": bounds}


def run(root: Path):
    results = root / "results"
    errors = []
    summary = {"schema": "map01-passive-clock-witness-audit-v1", "formal_allocation": False}
    runs = {}
    for number in range(8, 18):
        path = results / f"construction-clock-{number:02d}" / "raw.json"
        rows = read_json(path)
        runs[number] = rows
        if len(rows) != 3:
            errors.append(f"run{number}:expected_3_rows_got_{len(rows)}")
        if any(row.get("setup") != "initialized" or row.get("closed") is not True for row in rows):
            errors.append(f"run{number}:setup_or_cleanup_not_complete")

    for number in range(8, 12):
        if any(row.get("after_tic") != row.get("before_tic") or row.get("elapsed_ns", 0) < 1_900_000_000 for row in runs[number]):
            errors.append(f"run{number}:passive_tic_snapshot_changed_or_window_short")
    summary["passive_snapshot_stable_rows_1_2"] = sum(len(runs[n]) for n in range(8, 12))

    catchup = []
    for number in range(12, 16):
        for row in runs[number]:
            refresh = row.get("post_interval_refresh") or {}
            delta = refresh.get("tic", 0) - row.get("before_tic", 0)
            catchup.append({"run": number, "repetition": row.get("repetition"), "passive_tic_delta": row.get("after_tic", 0) - row.get("before_tic", 0), "refresh_tic_delta": delta, "refresh_span_ns": refresh.get("span_ns")})
            if row.get("after_tic") != row.get("before_tic") or delta < 70 or not (0 < refresh.get("span_ns", 0) < 60_000_000):
                errors.append(f"run{number}:unexpected_action_refresh_catchup")
    summary["one_tic_action_refresh_catchup"] = catchup

    zero_tic = []
    for row in runs[16]:
        refresh_tic = (row.get("post_interval_refresh") or {}).get("tic")
        zero_tic.append({"repetition": row.get("repetition"), "before_tic": row.get("before_tic"), "refresh_tic": refresh_tic})
        if refresh_tic != row.get("before_tic"):
            errors.append("run16:zero_tic_call_changed_reported_time")
    summary["zero_tic_refresh"] = zero_tic

    scorer_rows = []
    for row in runs[17]:
        trace = row.get("scorer_api_trace", [])
        tic_reads = [event["value"] for event in trace if event.get("name") == "get_episode_time"]
        call_span = row.get("scorer_end_ns", 0) - row.get("scorer_start_ns", 0)
        scorer_rows.append({"repetition": row.get("repetition"), "status": row.get("scorer_status"), "tic_reads": tic_reads, "attempt_getter_events": len(trace), "scorer_span_ns": call_span, "returned": row.get("scorer_return")})
        if row.get("scorer_status") != "returned" or len(tic_reads) != 2 or tic_reads[0] != tic_reads[1] or not 100_000 <= call_span <= 150_000:
            errors.append("run17:scorer_trace_or_span_mismatch")
    summary["exact_scorer_passive_construction_rows"] = scorer_rows

    frame_hash_checks = 0
    for number in range(14, 18):
        folder = results / f"construction-clock-{number:02d}"
        for row in runs[number]:
            repetition = row["repetition"]
            for ms, sample in zip((250, 500, 1000, 2000), row.get("samples", [])):
                frame = folder / f"frame-r{repetition}-{ms}ms.xwd.gz"
                compressed = frame.read_bytes()
                raw = gzip.decompress(compressed)
                if hashlib.sha256(raw).hexdigest() != sample["x11_frame_sha256"] or len(raw) != sample["x11_frame_bytes"]:
                    errors.append(f"run{number}:xwd_hash_or_size_mismatch:{frame.name}")
                frame_hash_checks += 1
            refresh = row.get("post_interval_refresh") or {}
            frame = folder / f"frame-r{repetition}-post-refresh.xwd.gz"
            if "x11_frame_sha256" in refresh:
                if hashlib.sha256(gzip.decompress(frame.read_bytes())).hexdigest() != refresh["x11_frame_sha256"]:
                    errors.append(f"run{number}:post_refresh_xwd_hash_mismatch:{frame.name}")
                frame_hash_checks += 1
    summary["retained_xwd_hash_checks"] = frame_hash_checks

    first = runs[14][0]
    folder = results / "construction-clock-14"
    ordered = sorted(first["samples"], key=lambda sample: sample["elapsed_ns"])
    diffs = []
    decoded = []
    for ms, sample in zip((250, 500, 1000, 2000), ordered):
        decoded.append(xwd_pixels(folder / f"frame-r0-{ms}ms.xwd.gz"))
    for left, right in zip(decoded, decoded[1:]):
        width, height, stride, pixels = left
        if right[:3] != left[:3]:
            errors.append("run14:xwd_dimensions_changed")
        diffs.append(differing_pixels(pixels, right[3], width, height, stride))
    summary["run14_adjacent_frame_pixel_differences"] = diffs

    summary["decision"] = "PASS_AUDIT_ONLY" if not errors else "FAIL_AUDIT"
    summary["errors"] = errors
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="directory containing results/construction-clock-XX")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"], "rows": 30, "xwd_checks": result.get("retained_xwd_hash_checks")}, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
