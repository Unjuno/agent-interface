#!/usr/bin/env python3
"""Post-submission evidence-integrity recheck; never reruns the candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "a01"
REVIEW_OUT = ROOT / "results" / "review-correction-02" / "RECHECK.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_lines(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_manifest(directory: Path, manifest_path: Path, excluded: set[str]) -> list[str]:
    entries = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        entries[name] = digest
    actual = {p.name for p in directory.iterdir() if p.is_file() and p.name not in excluded}
    errors = []
    if set(entries) != actual:
        errors.append("pre-audit manifest path set mismatch")
    for name, expected in entries.items():
        path = directory / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"pre-audit manifest digest mismatch: {name}")
    return errors


def compare_streams(raw_rows, observed_rows, heartbeat_rows, progress_rows):
    errors = []
    if len(raw_rows) != len(observed_rows):
        errors.append("raw and observer event counts differ")
        return errors
    expected_hb, expected_progress = [], []
    for raw, observed in zip(raw_rows, observed_rows):
        if any(observed.get(key) != value for key, value in raw.items()):
            errors.append("observer event does not preserve the raw worker fields")
            break
        if type(observed.get("observer_received_monotonic_ns")) is not int:
            errors.append("observer receipt timestamp missing")
            break
        projected = dict(raw)
        projected["observer_received_monotonic_ns"] = observed["observer_received_monotonic_ns"]
        if raw.get("event") == "heartbeat":
            expected_hb.append(projected)
        elif raw.get("event") == "progress":
            expected_progress.append(projected)
    if expected_hb != heartbeat_rows:
        errors.append("heartbeat split differs from projected observed raw stream")
    if expected_progress != progress_rows:
        errors.append("progress split differs from projected observed raw stream")
    return errors


def main() -> int:
    run = read_json(OUT / "RUN.json")
    original_audit = read_json(OUT / "AUDIT.json")
    raw_rows = read_lines(OUT / "worker-stdout.jsonl")
    observed_rows = read_lines(OUT / "observed-events.jsonl")
    heartbeat_rows = read_lines(OUT / "heartbeats.jsonl")
    progress_rows = read_lines(OUT / "progress.jsonl")
    host_rows = read_lines(OUT / "host_cpu.jsonl")
    errors = verify_manifest(
        OUT, OUT / "OUTPUT_SHA256SUMS.txt",
        {"OUTPUT_SHA256SUMS.txt", "AUDIT.json", "POST_AUDIT_SHA256SUMS.txt",
         "POST_AUDIT_SHA256SUMS.sha256"},
    )
    errors.extend(compare_streams(raw_rows, observed_rows, heartbeat_rows, progress_rows))
    missing_raw_counter = sum(
        not {"idle_delta_100ns", "kernel_delta_100ns", "user_delta_100ns"}.issubset(row)
        for row in host_rows
    )
    post_manifest = OUT / "POST_AUDIT_SHA256SUMS.txt"
    post_rows = [line.split("  ", 1) for line in post_manifest.read_text(encoding="utf-8").splitlines()]
    worktree_seal_mismatches = [
        name for digest, name in post_rows
        if not (OUT / name).is_file()
        or hashlib.sha256((OUT / name).read_bytes()).hexdigest() != digest
    ]
    repo = ROOT.parents[2]
    prefix = ROOT.relative_to(repo).as_posix() + "/"
    committed_seal_mismatches = []
    for digest, name in post_rows:
        blob = subprocess.run(
            ["git", "show", f"HEAD:{prefix}results/a01/{name}"],
            cwd=repo, capture_output=True,
        )
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != digest:
            committed_seal_mismatches.append(name)
    sidecar_parts = (OUT / "POST_AUDIT_SHA256SUMS.sha256").read_text(encoding="utf-8").split()
    committed_post_manifest = subprocess.run(
        ["git", "show", f"HEAD:{prefix}results/a01/POST_AUDIT_SHA256SUMS.txt"],
        cwd=repo, capture_output=True, check=True,
    ).stdout
    committed_sidecar_mismatch = hashlib.sha256(committed_post_manifest).hexdigest() != sidecar_parts[0]
    result = {
        "schema": "failure-detector-5531-regime-trace-review-recheck-v1",
        "allocation": run["allocation"],
        "candidate_or_formal_auditor_rerun": False,
        "original_run_status_preserved": run["capture_status"],
        "original_audit_output_preserved": True,
        "raw_worker_event_rows": len(raw_rows),
        "observer_event_rows": len(observed_rows),
        "heartbeat_split_rows": len(heartbeat_rows),
        "progress_split_rows": len(progress_rows),
        "split_projection_errors": errors,
        "host_counter_samples": len(host_rows),
        "samples_without_raw_counter_deltas": missing_raw_counter,
        "host_regime_labels_reconstructable": missing_raw_counter == 0,
        "post_audit_manifest_worktree_mismatches": worktree_seal_mismatches,
        "post_audit_manifest_committed_blob_mismatches": committed_seal_mismatches,
        "post_audit_manifest_committed_sidecar_mismatch": committed_sidecar_mismatch,
        "counter_formula_review": {
            "recorded_formula_in_collect_py": "(delta_idle + delta_kernel + delta_user - delta_idle) / (delta_idle + delta_kernel + delta_user)",
            "corrected_formula_if_raw_deltas_are_retained": "(delta_kernel + delta_user - delta_idle) / (delta_kernel + delta_user)",
            "windows_kernel_counter_includes_idle": True,
            "consequence": "idle time is double-counted; the recorded regime labels cannot be accepted as valid busy percentages",
            "raw_counter_deltas_retained": False,
            "source": "https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes",
        },
        "previous_audit_disposition": original_audit["trace_capture_disposition"],
        "previous_audit_scope_caveat": "prior audit checked row structure and timing but did not independently derive or verify GetSystemTimes busy-percent arithmetic",
        "scientific_disposition": "HOLD_INVALID_UNAUDITABLE_HOST_REGIME_LABELS",
        "eligible_for_regime_comparison": False,
        "errors": errors,
    }
    REVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "disposition": result["scientific_disposition"],
        "raw_counter_deltas_retained": not missing_raw_counter,
        "split_projection_errors": len(errors),
        "committed_checksum_mismatches": len(committed_seal_mismatches),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
