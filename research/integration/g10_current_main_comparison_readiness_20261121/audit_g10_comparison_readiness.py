"""Read-only G10 custody and comparison-contract admission audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


MAIN_SHA = "ce6449f38a56e1731f01d1024837fb34c9c759a3"
G10_SOURCE_SHA = "9823419dc71eb6f7fd745bfe8249cf7f7584a3a9"
ADAPTER_SHA256 = "9680761627e72a1986304eb8985b89280fe74d74f93aef9a2375ec02065aeac1"
G10_REL = Path("research/integration/calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74")
ADAPTER_REL = Path("research/integration/standard_mcp_task_ledger_57_v1/recorded_comparison_adapter_v1.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[3]
    result_path = Path(args.output).resolve()
    packet = Path(__file__).resolve().parent
    if result_path.parent != packet.resolve():
        fail("output must stay inside the new audit packet")
    if result_path.exists():
        fail("refusing to overwrite an existing audit result")

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
        capture_output=True, text=True).stdout.strip()
    if head != MAIN_SHA:
        fail(f"checkout head changed: {head}")

    g10 = repo / G10_REL
    plan = json.loads((g10 / "PLAN.json").read_text(encoding="utf-8"))
    raw_path = g10 / "runs/compiled_ocrlive10/raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    historical_audit = json.loads((g10 / "AUDIT.json").read_text(encoding="utf-8"))
    adapter_path = repo / ADAPTER_REL
    adapter_digest = digest(adapter_path)
    if adapter_digest != ADAPTER_SHA256:
        fail(f"comparison adapter source changed: {adapter_digest}")
    if plan.get("source_main") != G10_SOURCE_SHA:
        fail("G10 source revision does not match the frozen allocation")

    declared_sources = plan.get("source_hashes")
    raw_sources = raw.get("source_hashes")
    if not isinstance(declared_sources, dict) or declared_sources != raw_sources:
        fail("PLAN and raw source-hash maps differ")
    source_mismatches = []
    for relative, expected in sorted(declared_sources.items()):
        target = (g10 / relative).resolve(strict=True)
        if not target.is_relative_to(g10.resolve()):
            fail(f"source path escapes packet: {relative}")
        actual = digest(target)
        if actual != expected:
            source_mismatches.append({"path": relative, "expected": expected,
                                      "actual": actual})

    run_root = g10 / "runs/compiled_ocrlive10"
    run_manifest = []
    for path in sorted(run_root.rglob("*")):
        if path.is_symlink():
            fail(f"unexpected symlink in retained run: {path.relative_to(run_root)}")
        if path.is_file():
            run_manifest.append({"path": path.relative_to(run_root).as_posix(),
                                 "sha256": digest(path), "bytes": path.stat().st_size})
    if not run_manifest:
        fail("retained G10 run is empty")
    manifest_bytes = (json.dumps(run_manifest, sort_keys=True, separators=(",", ":"))
                      + "\n").encode("utf-8")
    manifest_path = packet / "G10_RUN_SHA256.json"
    if manifest_path.exists():
        if manifest_path.read_bytes() != manifest_bytes:
            fail("retained G10 run differs from the existing frozen manifest")
    else:
        manifest_path.write_bytes(manifest_bytes)

    ledger_dir = repo / ADAPTER_REL.parent
    sys.path.insert(0, os.fspath(ledger_dir))
    try:
        from ledger import LedgerValidationError
        from recorded_comparison_adapter_v1 import (
            _MEASUREMENT_KEYS,
            _METADATA_KEYS,
            build_measured_run,
        )

        try:
            build_measured_run(
                raw, recorder_root=run_root, ledger_metadata={}, measurement={})
        except LedgerValidationError as error:
            adapter_rejection = str(error)
        else:
            fail("adapter unexpectedly accepted unmodified G10 raw.json")
    finally:
        sys.path.remove(os.fspath(ledger_dir))

    required_receipt = {
        "complete", "events", "raw_refs", "unresolved_attempt_ids",
        "unresolved_tool_call_ids",
    }
    missing_receipt = sorted(required_receipt - set(raw))
    events = raw.get("events")
    if events != []:
        fail("G10 raw.events differs from the preregistered empty-event condition")
    if historical_audit.get("primary_usage") != "UNKNOWN":
        fail("historical G10 primary usage disposition changed")
    if source_mismatches:
        fail("one or more G10 pinned source hashes do not match")
    expected_missing_receipt = sorted(required_receipt - {"events"})
    if missing_receipt != expected_missing_receipt:
        fail("unexpected reconciled caller receipt fields appeared in G10 raw")

    report = {
        "audit_id": "G10-COMPARISON-READINESS-20261121-R01",
        "status": "PASS_CUSTODY_AND_EXPECTED_ADAPTER_HOLD",
        "main_sha": head,
        "g10_source_sha": plan["source_main"],
        "g10_allocation": plan["allocation"],
        "comparison_adapter_sha256": adapter_digest,
        "g10_declared_source_count": len(declared_sources),
        "g10_source_hash_mismatches": source_mismatches,
        "retained_run_file_count": len(run_manifest),
        "retained_run_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "historical_audit": {
            "disposition": historical_audit.get("disposition"),
            "errors": historical_audit.get("errors"),
            "ocr_calls": historical_audit.get("ocr_calls"),
            "ocr_local_elapsed_ns": historical_audit.get("ocr_local_elapsed_ns"),
            "primary_usage": historical_audit.get("primary_usage"),
            "native_programs": historical_audit.get("native_programs"),
        },
        "g10_raw_inventory": {
            "top_level_events": len(events),
            "graph_events": len(raw.get("graph_events", [])),
            "native_attempts": len(raw.get("native_attempts", [])),
            "images": len(raw.get("images", [])),
            "verifier_calls": len(raw.get("verifier_calls", [])),
            "ocr_attempts": sum(1 for _ in (run_root / "OCR_ATTEMPTS.jsonl")
                                .read_text(encoding="utf-8").splitlines() if _.strip()),
        },
        "adapter_contract": {
            "required_receipt_fields": sorted(required_receipt),
            "missing_receipt_fields_in_g10_raw": missing_receipt,
            "required_metadata_fields": sorted(_METADATA_KEYS),
            "required_measurement_fields": sorted(_MEASUREMENT_KEYS),
            "rejection_for_unmodified_g10_raw": adapter_rejection,
        },
        "decision": {
            "eligible_as_matched_efficiency_arm": False,
            "retained_narrow_use": "live positive-control for fixed Calc OCR/guarded-save/effect path",
            "reason": [
                "the current comparison adapter rejects the unmodified G10 raw record",
                "there is no matched comparison block in this one-allocation packet",
                "primary provider usage is UNKNOWN and cannot be treated as zero",
                "G10 native/graph/OCR events do not supply the recorder's complete model/tool/score event ledger",
            ],
            "live_or_provider_action_performed": False,
        },
    }
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
