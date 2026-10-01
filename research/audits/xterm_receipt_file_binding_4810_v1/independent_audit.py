"""Independent stdlib-only check of Issue #4810 mutation receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_AUDIT_SHA256 = "3ad71af1ccd3edaf694dc45e19af394f33b5bf64e630084ffb8fd17e74b16381"
EXPECTED_RAW_SHA256 = "2cd5199a67fa50965ef89c2463b363fa677f2c0b03c5884ffa7f141db4436e3a"
EXPECTED = {
    "baseline": None,
    "delete_ephemeral_ready": "scratch/pair-00/EPHEMERAL_XTERM/effects-0.ready.json",
    "delete_resident_done": "scratch/pair-00/RESIDENT_XTERM/effects.done.json",
    "delete_ephemeral_effect": "scratch/pair-00/EPHEMERAL_XTERM/effects-0.jsonl",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest(root: Path) -> dict[str, dict[str, object]]:
    result = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        result[rel] = {"bytes": len(data), "sha256": digest(data)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve(strict=True)
    probe = json.loads(args.probe.read_bytes())
    errors = []
    frozen_audit = evidence.parent / "audit.py"
    raw = evidence / "raw.json"
    actual_manifest = manifest(evidence)
    if digest(frozen_audit.read_bytes()) != EXPECTED_AUDIT_SHA256:
        errors.append("frozen_audit_hash")
    if digest(raw.read_bytes()) != EXPECTED_RAW_SHA256:
        errors.append("frozen_raw_hash")
    if probe.get("audit_sha256") != EXPECTED_AUDIT_SHA256:
        errors.append("probe_audit_identity")
    if probe.get("raw_sha256") != EXPECTED_RAW_SHA256:
        errors.append("probe_raw_identity")
    if not probe.get("source_evidence_unchanged"):
        errors.append("source_evidence_changed")
    if actual_manifest != probe.get("source_evidence_manifest"):
        errors.append("source_manifest_mismatch")
    by_name = {case.get("case"): case for case in probe.get("cases", [])}
    if set(by_name) != set(EXPECTED):
        errors.append("case_set")
    baseline = by_name.get("baseline", {})
    base_result = baseline.get("audit_result") or {}
    if baseline.get("returncode") != 0 or base_result.get("decision") != "CONSTRUCTION_AUDIT_ACCEPT":
        errors.append("baseline_not_accepted")
    missed = []
    for case_name, target in EXPECTED.items():
        if target is None:
            continue
        case = by_name.get(case_name, {})
        case_manifest = case.get("copy_manifest", {})
        expected_manifest = dict(actual_manifest)
        if target not in expected_manifest:
            errors.append("required_target_absent:" + target)
            continue
        expected_manifest.pop(target)
        if case_manifest != expected_manifest:
            errors.append("copy_not_exact_single_deletion:" + case_name)
        if (case.get("missing_path") != target or case.get("returncode") != 0
                or (case.get("audit_result") or {}).get("decision") != "CONSTRUCTION_AUDIT_ACCEPT"):
            errors.append("frozen_auditor_did_not_accept_missing_file:" + case_name)
        else:
            missed.append(case_name)
    if not errors and len(missed) == len(EXPECTED) - 1:
        decision = "PASS_RECEIPT_FILE_INTEGRITY_GAP_REPRODUCED"
    elif not errors and missed:
        decision = "HOLD_PARTIAL_GAP"
    elif not errors:
        decision = "FAIL_NO_REPRODUCTION"
    else:
        decision = "STOP_AUDIT_OR_PROVENANCE"
    report = {
        "schema": "issue4810-independent-audit-v1",
        "decision": decision,
        "errors": errors,
        "baseline_decision": base_result.get("decision"),
        "deletion_cases_accepted": missed,
        "deletion_cases_expected": len(EXPECTED) - 1,
        "original_evidence_manifest_sha256": probe.get("source_evidence_manifest_sha256"),
        "original_evidence_unchanged": probe.get("source_evidence_unchanged"),
    }
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if decision != "STOP_AUDIT_OR_PROVENANCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
