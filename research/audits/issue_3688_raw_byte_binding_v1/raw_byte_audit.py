#!/usr/bin/env python3
"""Byte-bound wrapper around the frozen Issue #3676 structural audit."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _load_upstream(source_dir):
    path = Path(source_dir) / "audit.py"
    spec = importlib.util.spec_from_file_location("predecessor_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_bytes(raw_path, predecessor_freeze_path, study_freeze_path,
                source_dir, expected_study_freeze_sha256):
    raw_bytes = Path(raw_path).read_bytes()
    predecessor_freeze_bytes = Path(predecessor_freeze_path).read_bytes()
    study_freeze_bytes = Path(study_freeze_path).read_bytes()
    errors = []

    expected_pin = str(expected_study_freeze_sha256)
    actual_study_freeze_sha = hashlib.sha256(study_freeze_bytes).hexdigest()
    if not HEX_SHA256.fullmatch(expected_pin) or actual_study_freeze_sha != expected_pin:
        return {"status": "FAIL_PROVENANCE", "stage": "study_freeze_binding",
                "errors": ["study freeze bytes do not match the pinned digest"],
                "actual_study_freeze_sha256": actual_study_freeze_sha}

    try:
        study_freeze = json.loads(study_freeze_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"status": "FAIL_PROVENANCE", "stage": "study_freeze_parse",
                "errors": [f"study freeze is invalid JSON: {exc}"]}

    expected_raw_sha = study_freeze.get("predecessor_raw_sha256")
    expected_original_freeze_sha = study_freeze.get("predecessor_freeze_sha256")
    expected_source_hashes = study_freeze.get("source_sha256")
    if not isinstance(expected_raw_sha, str) or not HEX_SHA256.fullmatch(expected_raw_sha):
        errors.append("study freeze raw digest is malformed")
    if not isinstance(expected_original_freeze_sha, str) or not HEX_SHA256.fullmatch(expected_original_freeze_sha):
        errors.append("study freeze predecessor digest is malformed")
    if not isinstance(expected_source_hashes, dict) or not expected_source_hashes:
        errors.append("study freeze source manifest is missing")
    if errors:
        return {"status": "FAIL_PROVENANCE", "stage": "study_freeze_schema", "errors": errors,
                "actual_study_freeze_sha256": actual_study_freeze_sha}

    actual_source_hashes = {}
    for relative, expected in sorted(expected_source_hashes.items()):
        if relative not in {"audit.py", "test_audit.py"} or not isinstance(expected, str) or not HEX_SHA256.fullmatch(expected):
            errors.append(f"invalid source-manifest entry: {relative}")
            continue
        source = Path(source_dir) / relative
        if not source.is_file():
            errors.append(f"source file missing: {relative}")
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        actual_source_hashes[relative] = actual
        if actual != expected:
            errors.append(f"source hash mismatch: {relative}")
    if errors:
        return {"status": "FAIL_PROVENANCE", "stage": "source_manifest_binding", "errors": errors,
                "actual_study_freeze_sha256": actual_study_freeze_sha,
                "actual_source_sha256": actual_source_hashes}

    actual_original_freeze_sha = hashlib.sha256(predecessor_freeze_bytes).hexdigest()
    if actual_original_freeze_sha != expected_original_freeze_sha:
        errors.append("predecessor freeze bytes do not match study freeze")
    actual_raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if actual_raw_sha != expected_raw_sha:
        errors.append("raw bytes do not match study freeze")
    if errors:
        return {"status": "FAIL_PROVENANCE", "stage": "raw_and_predecessor_binding",
                "errors": errors, "actual_raw_sha256": actual_raw_sha,
                "actual_predecessor_freeze_sha256": actual_original_freeze_sha,
                "actual_study_freeze_sha256": actual_study_freeze_sha,
                "actual_source_sha256": actual_source_hashes}

    try:
        raw = json.loads(raw_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"status": "FAIL_PROVENANCE", "stage": "raw_parse",
                "errors": [f"byte-bound raw is invalid JSON: {exc}"],
                "actual_raw_sha256": actual_raw_sha}
    embedded_freeze_sha = hashlib.sha256(predecessor_freeze_bytes).hexdigest()
    if raw.get("freeze_sha256") != embedded_freeze_sha:
        return {"status": "FAIL_PROVENANCE", "stage": "raw_freeze_binding",
                "errors": ["raw embedded predecessor freeze digest mismatch"],
                "actual_raw_sha256": actual_raw_sha}

    upstream = _load_upstream(source_dir)
    structural_errors = upstream.errors_for(raw)
    return {
        "status": "PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT" if not structural_errors else "FAIL_STRUCTURAL_AUDIT",
        "stage": "structural_audit",
        "errors": structural_errors,
        "actual_raw_sha256": actual_raw_sha,
        "expected_raw_sha256": expected_raw_sha,
        "actual_predecessor_freeze_sha256": actual_original_freeze_sha,
        "actual_study_freeze_sha256": actual_study_freeze_sha,
        "actual_source_sha256": actual_source_hashes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--predecessor-freeze", required=True, type=Path)
    parser.add_argument("--study-freeze", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--expected-study-freeze-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = audit_bytes(args.raw, args.predecessor_freeze, args.study_freeze,
                         args.source_dir, args.expected_study_freeze_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
