#!/usr/bin/env python3
"""Read-only verifier for the retained #4814 raw bundle and published manifest."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE = Path("/raw.zip")
MANIFEST = Path("/manifest.json")
OUT = Path("/out")
EXPECTED_ALLOCATION = "tiny-visual-equivariant-cnn-2564-20260927-01"
EXPECTED_MANIFEST_SHA256 = "abc669ee525d45d616775c706c61b1aacdd21072daa37014b4d6e3853c49fab5"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    raw_manifest = MANIFEST.read_bytes()
    manifest_sha = digest(raw_manifest)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        errors.append("manifest_sha256_mismatch")
    manifest = json.loads(raw_manifest)
    if manifest.get("allocation") != EXPECTED_ALLOCATION:
        errors.append("allocation_mismatch")
    meta = manifest.get("archive")
    rows = manifest.get("files")
    if not isinstance(meta, dict) or not isinstance(rows, list):
        raise ValueError("manifest archive/files malformed")

    expected: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            errors.append("malformed_file_row")
            continue
        name = row["path"]
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or name in expected:
            errors.append("unsafe_or_duplicate_manifest_path")
            continue
        if not isinstance(row["bytes"], int) or row["bytes"] < 0:
            errors.append("invalid_file_length:" + name)
            continue
        if not isinstance(row["sha256"], str) or len(row["sha256"]) != 64:
            errors.append("invalid_file_sha256:" + name)
            continue
        expected[name] = row

    archive_bytes = ARCHIVE.read_bytes()
    archive_sha = digest(archive_bytes)
    if len(archive_bytes) != meta.get("bytes"):
        errors.append("archive_length_mismatch")
    if archive_sha != meta.get("sha256"):
        errors.append("archive_sha256_mismatch")

    checks = []
    with zipfile.ZipFile(ARCHIVE, "r") as zf:
        bad_member = zf.testzip()
        if bad_member is not None:
            errors.append("zip_crc_failure:" + bad_member)
        infos = [i for i in zf.infolist() if not i.is_dir()]
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or set(names) != set(expected):
            errors.append("zip_member_set_mismatch")
        if len(infos) != meta.get("expanded_file_count"):
            errors.append("zip_member_count_mismatch")
        total = 0
        for info in infos:
            data = zf.read(info)
            total += len(data)
            row = expected.get(info.filename)
            actual_sha = digest(data)
            if row is None:
                checks.append({"path": info.filename, "bytes": len(data), "sha256": actual_sha,
                               "match": False})
                continue
            ok = len(data) == row["bytes"] and actual_sha == row["sha256"]
            if not ok:
                errors.append("member_bytes_mismatch:" + info.filename)
            checks.append({"path": info.filename, "bytes": len(data), "sha256": actual_sha,
                           "match": ok})
        if total != meta.get("expanded_total_bytes"):
            errors.append("expanded_total_bytes_mismatch")
        predictions = next((r for r in checks if r["path"] == "predictions.jsonl"), None)
        if predictions is None or predictions["sha256"] != meta.get("validated_predictions_sha256"):
            errors.append("predictions_digest_mismatch")

    result = {
        "schema": "tiny-visual-equivariant-raw-delivery-audit-v1",
        "allocation": EXPECTED_ALLOCATION,
        "decision": "PASS_RAW_BUNDLE_RECONCILES_MANIFEST" if not errors else "STOP_RAW_BUNDLE_AUDIT",
        "manifest_sha256": manifest_sha,
        "archive_bytes": len(archive_bytes),
        "archive_sha256": archive_sha,
        "expanded_file_count": len(checks),
        "expanded_total_bytes": sum(row["bytes"] for row in checks),
        "predictions_sha256": next((r["sha256"] for r in checks if r["path"] == "predictions.jsonl"), None),
        "errors": errors,
        "files": checks,
        "scope": "Existing #4814 raw evidence delivery/integrity only; no formal rerun, refit, or efficacy reinterpretation.",
    }
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (OUT / "AUDIT.json").write_bytes(encoded)
    print(json.dumps({k: result[k] for k in (
        "decision", "archive_bytes", "archive_sha256", "expanded_file_count",
        "expanded_total_bytes", "predictions_sha256", "errors")}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"decision": "STOP_RAW_BUNDLE_AUDIT",
                          "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2)
