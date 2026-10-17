#!/usr/bin/env python3
"""Additive post-run reconstruction of GetSystemTimes regime labels; no rerun."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
from collections import Counter
from decimal import Decimal

from recheck_review import compare_streams, read_json, read_lines, verify_manifest

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "a01"
REVIEW_OUT = ROOT / "results" / "review-correction-03" / "RECHECK.json"
THRESHOLD_PCT = Decimal("50.0")
RECORDED_ROUNDING_UNIT = Decimal("0.000001")
ROUNDING_HALF_UNIT = RECORDED_ROUNDING_UNIT / Decimal(2)


def corrected_busy_bounds(recorded_busy_pct: int | float) -> tuple[Decimal, Decimal]:
    """Invert B=100*S/(I+S), with B rounded to six decimal places.

    GetSystemTimes' kernel counter K includes idle I; S=K+U. True busy is
    100*(S-I)/S = 200-10000/B. Monotonicity lets us propagate the recorded
    half-unit rounding interval through that inverse.
    """
    if type(recorded_busy_pct) not in (int, float) or not math.isfinite(recorded_busy_pct):
        raise ValueError("recorded busy percent must be finite numeric data")
    b = Decimal(str(recorded_busy_pct))
    if b <= ROUNDING_HALF_UNIT:
        raise ValueError("recorded busy percent must be positive")
    low_b = b - ROUNDING_HALF_UNIT
    high_b = b + ROUNDING_HALF_UNIT
    return (Decimal(200) - Decimal(10000) / low_b,
            Decimal(200) - Decimal(10000) / high_b)


def reconstructed_regime(recorded_busy_pct: int | float) -> str:
    low, high = corrected_busy_bounds(recorded_busy_pct)
    if low >= THRESHOLD_PCT:
        return "elevated"
    if high < THRESHOLD_PCT:
        return "ordinary"
    return "threshold_ambiguous"


def classify_intervals(heartbeats, host_rows):
    by_regime = {"ordinary": [], "elevated": [], "threshold_ambiguous": []}
    overall_midpoint = ((heartbeats[0]["observer_received_monotonic_ns"]
                         + heartbeats[-1]["observer_received_monotonic_ns"]) // 2
                        if heartbeats else 0)
    hi = 0
    for index in range(len(heartbeats) - 1):
        left, right = heartbeats[index], heartbeats[index + 1]
        interval_midpoint = (left["observer_received_monotonic_ns"]
                             + right["observer_received_monotonic_ns"]) // 2
        while hi + 1 < len(host_rows) and host_rows[hi + 1]["observer_monotonic_ns"] <= interval_midpoint:
            hi += 1
        if host_rows and host_rows[hi]["observer_monotonic_ns"] <= interval_midpoint:
            regime = reconstructed_regime(host_rows[hi]["busy_pct"])
            by_regime[regime].append({
                "end_ns": right["observer_received_monotonic_ns"],
                "worker_interval_ms": (right["worker_monotonic_ns"]
                                       - left["worker_monotonic_ns"]) / 1e6,
                "observer_interval_ms": (right["observer_received_monotonic_ns"]
                                         - left["observer_received_monotonic_ns"]) / 1e6,
            })
    summary = {}
    for regime, rows in by_regime.items():
        first_half = sum(row["end_ns"] < overall_midpoint for row in rows)
        summary[regime] = {
            "interval_rows": len(rows),
            "first_half_rows": first_half,
            "second_half_rows": len(rows) - first_half,
            "meets_frozen_coverage_floor": (
                len(rows) >= 200 and first_half >= 100 and len(rows) - first_half >= 100
            ),
        }
    return summary


def authenticate_post_manifest(worktree_manifest: bytes, index_manifest: bytes,
                               head_manifest: bytes, worktree_sidecar: bytes,
                               index_sidecar: bytes, head_sidecar: bytes) -> tuple[bool, list[str]]:
    """Authenticate the post-audit manifest before trusting its path list."""
    errors = []
    if not (worktree_manifest == index_manifest == head_manifest):
        errors.append("post-audit manifest differs across worktree, index, and HEAD")
    if not (worktree_sidecar == index_sidecar == head_sidecar):
        errors.append("post-audit manifest sidecar differs across worktree, index, and HEAD")
    try:
        expected = worktree_sidecar.decode("ascii").split()[0]
    except (UnicodeDecodeError, IndexError):
        expected = ""
    if not expected or hashlib.sha256(worktree_manifest).hexdigest() != expected:
        errors.append("post-audit manifest does not match its sidecar")
    return not errors, errors


def main() -> int:
    run = read_json(OUT / "RUN.json")
    original_audit = read_json(OUT / "AUDIT.json")
    raw_rows = read_lines(OUT / "worker-stdout.jsonl")
    observed_rows = read_lines(OUT / "observed-events.jsonl")
    heartbeats = read_lines(OUT / "heartbeats.jsonl")
    progress = read_lines(OUT / "progress.jsonl")
    host_rows = read_lines(OUT / "host_cpu.jsonl")
    errors = verify_manifest(
        OUT, OUT / "OUTPUT_SHA256SUMS.txt",
        {"OUTPUT_SHA256SUMS.txt", "AUDIT.json", "POST_AUDIT_SHA256SUMS.txt",
         "POST_AUDIT_SHA256SUMS.sha256"},
    )
    errors.extend(compare_streams(raw_rows, observed_rows, heartbeats, progress))

    repo = ROOT.parents[2]
    prefix = ROOT.relative_to(repo).as_posix() + "/"
    manifest_rel = f"{prefix}results/a01/POST_AUDIT_SHA256SUMS.txt"
    sidecar_rel = f"{prefix}results/a01/POST_AUDIT_SHA256SUMS.sha256"
    manifest_path = OUT / "POST_AUDIT_SHA256SUMS.txt"
    sidecar_path = OUT / "POST_AUDIT_SHA256SUMS.sha256"
    work_manifest = manifest_path.read_bytes()
    work_sidecar = sidecar_path.read_bytes()
    index_manifest = subprocess.run(["git", "show", f":{manifest_rel}"], cwd=repo,
                                    capture_output=True)
    head_manifest = subprocess.run(["git", "show", f"HEAD:{manifest_rel}"], cwd=repo,
                                   capture_output=True)
    index_sidecar = subprocess.run(["git", "show", f":{sidecar_rel}"], cwd=repo,
                                   capture_output=True)
    head_sidecar = subprocess.run(["git", "show", f"HEAD:{sidecar_rel}"], cwd=repo,
                                  capture_output=True)
    post_manifest_authenticated = all(result.returncode == 0 for result in
                                      (index_manifest, head_manifest, index_sidecar, head_sidecar))
    post_manifest_errors = []
    if post_manifest_authenticated:
        post_manifest_authenticated, post_manifest_errors = authenticate_post_manifest(
            work_manifest, index_manifest.stdout, head_manifest.stdout,
            work_sidecar, index_sidecar.stdout, head_sidecar.stdout,
        )
    else:
        post_manifest_errors = ["post-audit manifest or sidecar Git blob unavailable"]
    errors.extend(post_manifest_errors)
    post_rows = ([line.split("  ", 1) for line in work_manifest.decode("utf-8").splitlines()]
                 if post_manifest_authenticated else [])
    worktree_mismatches = [name for digest, name in post_rows
                           if not (OUT / name).is_file()
                           or hashlib.sha256((OUT / name).read_bytes()).hexdigest() != digest]
    committed_mismatches = []
    for digest, name in post_rows:
        blob = subprocess.run(["git", "show", f"HEAD:{prefix}results/a01/{name}"],
                              cwd=repo, capture_output=True)
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != digest:
            committed_mismatches.append(name)
    sidecar_mismatch = not post_manifest_authenticated
    if worktree_mismatches:
        errors.append("post-audit worktree seal mismatch")
    if committed_mismatches:
        errors.append("post-audit committed blob seal mismatch")
    if sidecar_mismatch:
        errors.append("post-audit manifest sidecar mismatch")

    sample_regimes = Counter(reconstructed_regime(row["busy_pct"]) for row in host_rows)
    corrected_values = [float((Decimal(200) - Decimal(10000) / Decimal(str(row["busy_pct"]))))
                        for row in host_rows]
    threshold_b = Decimal(20000) / Decimal(300)
    threshold_margins = [abs(Decimal(str(row["busy_pct"])) - threshold_b) for row in host_rows]
    minimum_recorded_margin = min(threshold_margins) if threshold_margins else None
    interval_coverage = classify_intervals(heartbeats, host_rows)
    ambiguous = sample_regimes["threshold_ambiguous"]
    comparison_eligible = (
        not errors and ambiguous == 0
        and all(interval_coverage[name]["meets_frozen_coverage_floor"]
                for name in ("ordinary", "elevated"))
    )
    result = {
        "schema": "failure-detector-5531-regime-trace-corrected-review-recheck-v1",
        "allocation": run["allocation"],
        "candidate_or_formal_auditor_rerun": False,
        "original_run_status_preserved": run["capture_status"],
        "original_audit_output_preserved": True,
        "prior_correction_02_disposition": "HOLD_INVALID_UNAUDITABLE_HOST_REGIME_LABELS",
        "prior_correction_02_reconstructability_claim": "superseded: recorded rounded busy_pct is algebraically invertible",
        "raw_worker_event_rows": len(raw_rows),
        "observer_event_rows": len(observed_rows),
        "heartbeat_split_rows": len(heartbeats),
        "progress_split_rows": len(progress),
        "stream_projection_errors": errors,
        "host_counter_samples": len(host_rows),
        "raw_counter_deltas_retained": False,
        "recorded_busy_pct_sample_counts": dict(sorted(Counter(float(row["busy_pct"]) for row in host_rows).items())),
        "reconstructed_host_sample_regime_counts": dict(sorted(sample_regimes.items())),
        "corrected_busy_pct_min": min(corrected_values) if corrected_values else None,
        "corrected_busy_pct_max": max(corrected_values) if corrected_values else None,
        "formula": {
            "recorded_busy_pct": "B = 100*(delta_kernel + delta_user)/(delta_idle + delta_kernel + delta_user); Windows delta_kernel includes delta_idle",
            "reconstruction": "true_busy_pct = 200 - 10000/B",
            "threshold_pct": 50.0,
            "recorded_B_threshold_pct": "200/3",
            "B_rounding_unit_pct": "0.000001",
            "B_rounding_half_unit_pct": "0.0000005",
            "minimum_recorded_distance_from_threshold_B_pct": str(minimum_recorded_margin) if minimum_recorded_margin is not None else None,
            "rounding_boundary_ambiguous_samples": ambiguous,
            "source": "https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes",
        },
        "interval_coverage_by_reconstructed_regime": interval_coverage,
        "previous_audit_disposition": original_audit["trace_capture_disposition"],
        "previous_audit_scope_caveat": "historical audit checked structure/timing but applied the flawed recorded busy formula directly",
        "scientific_disposition": "HOLD_INSUFFICIENT_REGIME_COVERAGE" if not comparison_eligible else "TRACE_CANDIDATE_ONLY",
        "eligible_for_regime_comparison": comparison_eligible,
        "post_audit_manifest_worktree_mismatches": worktree_mismatches,
        "post_audit_manifest_committed_blob_mismatches": committed_mismatches,
        "post_audit_manifest_committed_sidecar_mismatch": sidecar_mismatch,
        "post_audit_manifest_authenticated_before_path_use": post_manifest_authenticated,
    }
    REVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_OUT.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "disposition": result["scientific_disposition"],
        "sample_regimes": result["reconstructed_host_sample_regime_counts"],
        "interval_coverage": result["interval_coverage_by_reconstructed_regime"],
        "manifest_mismatches": len(worktree_mismatches) + len(committed_mismatches) + int(sidecar_mismatch),
        "projection_errors": len(errors),
    }, sort_keys=True))
    return 0 if not errors and ambiguous == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
