#!/usr/bin/env python3
"""Raw-only structural audit for the one-shot #5531 A01 trace."""
from __future__ import annotations

import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "a01"
ALLOCATION = "FAILURE-DETECTOR-5531-REGIME-TRACE-A01-20261005-01"
THRESHOLD = 50.0


def regime_for_busy(busy_pct: float) -> str:
    return "elevated" if busy_pct >= THRESHOLD else "ordinary"


def contiguous_zero_based(values: list[object]) -> bool:
    return all(type(value) is int for value in values) and values == list(range(len(values)))


def strictly_increasing(values: list[object]) -> bool:
    return all(type(value) is int for value in values) and all(
        values[i] < values[i + 1] for i in range(len(values) - 1)
    )


def read_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_lines(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    run = read_json(OUT / "RUN.json")
    hb = read_lines(OUT / "heartbeats.jsonl")
    progress = read_lines(OUT / "progress.jsonl")
    host = read_lines(OUT / "host_cpu.jsonl")
    source_events = read_lines(OUT / "worker-stdout.jsonl")
    observed_events = read_lines(OUT / "observed-events.jsonl")
    freeze = read_json(ROOT / "FREEZE.json")
    errors = []
    if run.get("allocation") != ALLOCATION: errors.append("allocation mismatch")
    if type(run.get("candidate_exit_code")) is not int or run.get("candidate_exit_code") != 0:
        errors.append("candidate did not exit zero")
    if run.get("capture_status") != "CAPTURED": errors.append("capture status is not CAPTURED")
    if run.get("retry_count") != 0: errors.append("unexpected retry count")
    if run.get("freeze_sha256") != sha256(ROOT / "FREEZE.json"):
        errors.append("RUN.json freeze digest mismatch")
    for name, expected in freeze.get("source_sha256", {}).items():
        if not (ROOT / name).is_file() or sha256(ROOT / name) != expected:
            errors.append(f"frozen source digest mismatch: {name}")
    manifest_path = OUT / "OUTPUT_SHA256SUMS.txt"
    manifest = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        manifest[name] = digest
    actual_names = {p.name for p in OUT.iterdir() if p.is_file() and p.name not in {"OUTPUT_SHA256SUMS.txt", "AUDIT.json"}}
    if set(manifest) != actual_names: errors.append("output manifest path set mismatch")
    for name, digest in manifest.items():
        if name not in actual_names or sha256(OUT / name) != digest:
            errors.append(f"output digest mismatch: {name}")
    if len(source_events) != len(observed_events): errors.append("source/observed event row count mismatch")
    for source, observed in zip(source_events, observed_events):
        if any(observed.get(k) != v for k, v in source.items()):
            errors.append("observed event differs from raw worker stdout")
            break
        if type(observed.get("observer_received_monotonic_ns")) is not int:
            errors.append("observer receive timestamp missing or invalid")
            break
    if not strictly_increasing([x.get("observer_received_monotonic_ns") for x in observed_events]):
        errors.append("observed event stream clock is not strictly increasing")
    if len(source_events) != len(hb) + len(progress): errors.append("split event streams do not cover raw worker stdout")
    pid, digest = run.get("worker_pid"), run.get("nonce_sha256")
    if type(pid) is not int: errors.append("worker PID is not an exact integer")
    if not hb: errors.append("no heartbeat rows")
    seqs = [x.get("sequence") for x in hb]
    if not contiguous_zero_based(seqs): errors.append("heartbeat sequence is not contiguous from zero")
    if any(x.get("event") != "heartbeat" or x.get("allocation") != ALLOCATION for x in hb):
        errors.append("heartbeat type/allocation mismatch")
    if any(x.get("pid") != pid for x in hb + progress): errors.append("worker PID mismatch")
    nonce_values = [x.get("nonce") for x in hb + progress]
    import hashlib
    nonce = nonce_values[0] if nonce_values and all(type(x) is str and x == nonce_values[0] for x in nonce_values) else None
    if not isinstance(nonce, str) or hashlib.sha256(nonce.encode()).hexdigest() != digest:
        errors.append("run nonce mismatch")
    if any(x.get("allocation") != ALLOCATION for x in progress): errors.append("progress allocation mismatch")
    if not contiguous_zero_based([x.get("progress_sequence") for x in progress]):
        errors.append("progress sequence is not contiguous from zero")
    if not strictly_increasing([x.get("worker_monotonic_ns") for x in hb]):
        errors.append("worker monotonic clock is not strictly increasing")
    if not strictly_increasing([x.get("observer_received_monotonic_ns") for x in hb]):
        errors.append("observer receipt clock is not strictly increasing")
    if any(type(x.get("observer_received_monotonic_ns")) is not int or
           type(x.get("worker_monotonic_ns")) is not int or
           x["observer_received_monotonic_ns"] < x["worker_monotonic_ns"] for x in hb):
        errors.append("observer receipt precedes worker event")
    if any(type(x.get("busy_pct")) not in (int, float) or not math.isfinite(x["busy_pct"])
           or x["busy_pct"] < 0 or x["busy_pct"] > 100 for x in host):
        errors.append("host CPU percentage is not finite numeric data in [0,100]")
    if any(x.get("threshold_pct") != THRESHOLD for x in host): errors.append("threshold mismatch")
    if not contiguous_zero_based([x.get("sequence") for x in host]): errors.append("host sample sequence is not contiguous")
    if any(x.get("regime") != regime_for_busy(float(x["busy_pct"])) for x in host):
        errors.append("regime label mismatch")
    if not strictly_increasing([x.get("observer_monotonic_ns") for x in host]):
        errors.append("host sample clock is not strictly increasing")
    if host and hb:
        start, end = hb[0]["observer_received_monotonic_ns"], hb[-1]["observer_received_monotonic_ns"]
        span = end - start
        if span < 590_000_000_000: errors.append("heartbeat trace shorter than 590 seconds")
        if host[0]["observer_monotonic_ns"] > start + 2_000_000_000: errors.append("host samples start too late")
        if host[-1]["observer_monotonic_ns"] < end - 2_000_000_000: errors.append("host samples end too early")
    interval_by_regime = {"ordinary": [], "elevated": []}
    midpoint = (hb[0]["observer_received_monotonic_ns"] + hb[-1]["observer_received_monotonic_ns"]) // 2 if hb else 0
    hi = 0
    for i in range(len(hb) - 1):
        left, right = hb[i], hb[i + 1]
        interval_midpoint = (left["observer_received_monotonic_ns"] + right["observer_received_monotonic_ns"]) // 2
        while hi + 1 < len(host) and host[hi + 1]["observer_monotonic_ns"] <= interval_midpoint:
            hi += 1
        if host and host[hi]["observer_monotonic_ns"] <= interval_midpoint:
            interval_by_regime[host[hi]["regime"]].append({
                "end_ns": right["observer_received_monotonic_ns"],
                "observer_interval_ms": (right["observer_received_monotonic_ns"] - left["observer_received_monotonic_ns"]) / 1e6,
                "worker_interval_ms": (right["worker_monotonic_ns"] - left["worker_monotonic_ns"]) / 1e6,
            })
    coverage = {}
    for regime, intervals in interval_by_regime.items():
        first = sum(x["end_ns"] < midpoint for x in intervals)
        second = len(intervals) - first
        observed_ms = [x["observer_interval_ms"] for x in intervals]
        worker_ms = [x["worker_interval_ms"] for x in intervals]
        coverage[regime] = {
            "interval_rows": len(intervals), "first_half_rows": first, "second_half_rows": second,
            "observer_interval_p50_ms": round(statistics.median(observed_ms), 3) if observed_ms else None,
            "observer_interval_max_ms": round(max(observed_ms), 3) if observed_ms else None,
            "worker_interval_p50_ms": round(statistics.median(worker_ms), 3) if worker_ms else None,
            "meets_frozen_coverage_floor": len(intervals) >= 200 and first >= 100 and second >= 100,
        }
    if host and (host[0]["observer_monotonic_ns"] - hb[0]["observer_received_monotonic_ns"] > 2_000_000_000):
        errors.append("host counter stream does not overlap the heartbeat trace")
    result = {
        "schema": "failure-detector-5531-regime-trace-audit-v1",
        "allocation": ALLOCATION,
        "auditor": "independent raw-only structural and timing reconstruction",
        "heartbeat_rows": len(hb), "progress_rows": len(progress), "host_sample_rows": len(host),
        "coverage_by_regime": coverage,
        "trace_capture_disposition": "PASS_TRACE_CAPTURE_SCOPED" if not errors else "FAIL_CAPTURE",
        "regime_comparison_eligibility": "HOLD_INSUFFICIENT_REGIME_COVERAGE" if not all(x["meets_frozen_coverage_floor"] for x in coverage.values()) or set(x for x in coverage if coverage[x]["interval_rows"]) != {"ordinary", "elevated"} else "TRACE_CANDIDATE_ONLY",
        "errors": errors,
        "scope": "One controlled healthy child process; not detector validation or a performance comparison.",
    }
    (OUT / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["trace_capture_disposition"],
                      "eligibility": result["regime_comparison_eligibility"],
                      "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = {
            "schema": "failure-detector-5531-regime-trace-audit-v1",
            "allocation": ALLOCATION,
            "trace_capture_disposition": "FAIL_AUDIT",
            "regime_comparison_eligibility": "HOLD_AUDIT_FAILURE",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "scope": "Audit process failure; no inference or candidate rerun.",
        }
        out = ROOT / "results" / "a01" / "AUDIT.json"
        out.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, sort_keys=True))
        raise SystemExit(1)
