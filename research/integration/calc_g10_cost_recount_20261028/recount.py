"""Recount recorded G10 timing/cost coverage without rerunning its actor/auditor.

Run from any directory with Python 3.13+: ``python recount.py``.
Only the derived sibling ``recount.json`` is written. Historical inputs remain
read-only and are verified against the archive FILES.json manifest.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = (ROOT / "research/integration/calc_current_shared_3311_4d74_20261004")
PACKAGE = ARCHIVE / "calc-compiled-ocrlive-4d74"
RUN = PACKAGE / "runs/compiled_ocrlive10"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed_ns(start: int, end: int, label: str) -> int:
    if type(start) is not int or type(end) is not int or end < start:
        raise ValueError(f"invalid recorded monotonic interval: {label}")
    return end - start


def main() -> None:
    manifest = json.loads((ARCHIVE / "FILES.json").read_text(encoding="utf-8"))
    expected = {row["path"]: row["sha256"] for row in manifest["files"]}
    source_paths = {
        "raw": (RUN / "raw.json", "calc-compiled-ocrlive-4d74/runs/compiled_ocrlive10/raw.json"),
        "ocr_attempts": (RUN / "OCR_ATTEMPTS.jsonl", "calc-compiled-ocrlive-4d74/runs/compiled_ocrlive10/OCR_ATTEMPTS.jsonl"),
        "host_receipt": (RUN / "HOST_RECEIPT.json", "calc-compiled-ocrlive-4d74/runs/compiled_ocrlive10/HOST_RECEIPT.json"),
        "original_audit": (PACKAGE / "AUDIT.json", "calc-compiled-ocrlive-4d74/AUDIT.json"),
        "original_report": (PACKAGE / "REPORT.md", "calc-compiled-ocrlive-4d74/REPORT.md"),
    }
    source_hashes = {}
    for label, (path, manifest_path) in source_paths.items():
        actual = sha256(path)
        if actual != expected.get(manifest_path):
            raise ValueError(f"archive hash mismatch: {label}")
        source_hashes[label] = actual

    raw = json.loads(source_paths["raw"][0].read_text(encoding="utf-8"))
    host = json.loads(source_paths["host_receipt"][0].read_text(encoding="utf-8"))
    audit = json.loads(source_paths["original_audit"][0].read_text(encoding="utf-8"))
    report = source_paths["original_report"][0].read_text(encoding="utf-8").lower()
    ocr_rows = [json.loads(line) for line in
                source_paths["ocr_attempts"][0].read_text(encoding="utf-8").splitlines()
                if line.strip()]
    if not ocr_rows or len(ocr_rows) != audit["ocr_calls"]:
        raise ValueError("OCR attempt count differs from retained audit")
    if audit["disposition"] != "PASS_SCOPED_LIVE_OCR_GRAPH" or audit["errors"]:
        raise ValueError("unexpected historical audit disposition")

    ocr_durations = [elapsed_ns(row["start_ns"], row["end_ns"], "OCR")
                     for row in ocr_rows]
    ocr_sum = sum(ocr_durations)
    if ocr_sum != audit["ocr_local_elapsed_ns"]:
        raise ValueError("recounted OCR duration differs from retained audit")
    if "no additional benchmark model calls" not in report:
        raise ValueError("original report wording for additional calls changed")

    native = []
    for index, attempt in enumerate(raw["native_attempts"], start=1):
        execution = attempt["execution"]
        releases = execution.get("releases", [])
        native.append({
            "attempt": index,
            "elapsed_ns": elapsed_ns(execution["started_ns"], execution["ended_ns"], "native"),
            "program_emissions": execution.get("program_emissions"),
            "release_records": len(releases),
            "all_recorded_releases_verified_empty": bool(releases) and all(
                row.get("verified") is True and row.get("keys_down") == [] and
                row.get("buttons_down") == [] for row in releases),
        })

    host_start = datetime.fromisoformat(host["started_utc"])
    host_end = datetime.fromisoformat(host["ended_utc"])
    host_elapsed_ns = int((host_end - host_start).total_seconds() * 1_000_000_000)
    raw_container_ns = elapsed_ns(raw["started_ns"], raw["ended_ns"], "container")
    graph_ns = elapsed_ns(raw["graph_started_ns"], raw["graph_ended_ns"], "compiled graph")
    outputs = [row.get("stdout", "").strip() for row in ocr_rows]

    result = {
        "format": "calc-g10-read-only-cost-recount-v1",
        "recount_script_sha256": sha256(Path(__file__)),
        "historical_sources_sha256": source_hashes,
        "historical_scope": {
            "allocation": "CALC-COMPILED-OCR-3311-4D74-CONSTRUCTION-G10-20261004",
            "source_main": "9823419dc71eb6f7fd745bfe8249cf7f7584a3a9",
            "runs": 1,
            "original_audit_disposition": audit["disposition"],
            "saved_effects_reported_by_original_audit": len(audit["saved_effects"]),
            "all_saved_effects_passed_in_original_audit": all(row["pass_effect"] for row in audit["saved_effects"]),
        },
        "recounted_measurements": {
            "host_launcher_elapsed_ns": host_elapsed_ns,
            "container_process_elapsed_ns": raw_container_ns,
            "compiled_graph_elapsed_ns": graph_ns,
            "compiled_graph_observations": len(raw["compiled_result"]["observations"]),
            "native_program_attempts": native,
            "native_program_elapsed_ns_sum": sum(row["elapsed_ns"] for row in native),
            "ocr_subprocess_attempt_count": len(ocr_rows),
            "ocr_subprocess_outputs_in_order": outputs,
            "ocr_subprocess_elapsed_ns_each": ocr_durations,
            "ocr_subprocess_elapsed_ns_sum": ocr_sum,
            "ocr_first_start_to_last_end_ns": elapsed_ns(ocr_rows[0]["start_ns"], ocr_rows[-1]["end_ns"], "OCR span"),
        },
        "not_reconstructed": {
            "primary_model_usage_and_attempts": "UNKNOWN per original report/audit",
            "additional_benchmark_model_calls": 0,
            "model_visible_tokens_images_and_wait": "not measured",
            "wall_time_to_independently_scored_task_effect": "not measured; original scoring is not timestamp-joined to host run",
            "cold_warm_invalidation_repair_phases": "not compared",
            "matched_baseline_or_speedup": "not available",
            "cumulative_reuse_break_even": "not available",
        },
        "limitations": [
            "Derived read-only recount; original G10 actor and auditor were not rerun.",
            "Timing intervals are historical single-run host/container/monotonic measurements with distinct endpoints.",
            "A correct OCR transcript and two independently saved effects are the original scoped report, not general OCR or application reliability.",
            "Requested WSLc CPU/memory settings are not evidence of enforcement.",
            "This record contains no baseline and cannot support a comparative speed or token-efficiency claim.",
        ],
    }
    destination = HERE / "recount.json"
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
