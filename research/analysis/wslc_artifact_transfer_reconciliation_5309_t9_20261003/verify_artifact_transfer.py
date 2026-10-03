"""Offline byte-level reconciliation of the retained T7/T8 stdout artifacts."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    pass


def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def _read_exact_artifacts(document: dict[str, Any]) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    try:
        artifacts = document["artifacts"]
        capture_meta = artifacts["captured_stdout"]
        t7_meta = artifacts["t7_committed_stdout"]
        capture = base64.b64decode(capture_meta["base64"], validate=True)
        t7 = base64.b64decode(t7_meta["base64"], validate=True)
    except (KeyError, TypeError, binascii.Error) as exc:
        raise AuditError("invalid frozen artifact snapshot") from exc

    for label, meta, data in (
        ("captured_stdout", capture_meta, capture),
        ("t7_committed_stdout", t7_meta, t7),
    ):
        if len(data) != meta.get("bytes"):
            raise AuditError(f"{label}: byte length mismatch")
        if git_blob_sha1(data) != meta.get("git_blob_sha1"):
            raise AuditError(f"{label}: Git blob identity mismatch")
        expected_sha256 = meta.get("sha256")
        if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
            raise AuditError(f"{label}: SHA-256 mismatch")
    return capture, t7, capture_meta, t7_meta


def reconcile_bytes(capture: bytes, t7_committed: bytes) -> dict[str, Any]:
    if not capture.endswith(b"\n"):
        raise AuditError("captured stdout does not end with LF")
    if t7_committed != capture + b"\r\n":
        raise AuditError("T7 committed bytes are not exactly capture plus CRLF")
    try:
        capture_json = json.loads(capture)
        t7_json = json.loads(t7_committed)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("one or both receipts are not valid JSON") from exc
    if capture_json != t7_json:
        raise AuditError("decoded JSON values differ")
    return {
        "byte_prefix_equal": True,
        "appended_suffix_hex": "0d0a",
        "json_values_equal": True,
        "captured_bytes": len(capture),
        "t7_committed_bytes": len(t7_committed),
        "captured_sha256": hashlib.sha256(capture).hexdigest(),
        "t7_committed_sha256": hashlib.sha256(t7_committed).hexdigest(),
        "captured_git_blob_sha1": git_blob_sha1(capture),
        "t7_committed_git_blob_sha1": git_blob_sha1(t7_committed),
    }


def audit(document: dict[str, Any]) -> dict[str, Any]:
    capture, t7, capture_meta, t7_meta = _read_exact_artifacts(document)
    result = reconcile_bytes(capture, t7)
    if capture_meta.get("path") == t7_meta.get("path"):
        raise AuditError("artifact source paths must remain distinct")
    return {
        "status": "PASS_ARTIFACT_TRANSFER_PROVENANCE_RECONCILED",
        "sources": {
            "captured_stdout": {
                "commit": capture_meta["commit"],
                "path": capture_meta["path"],
                "git_blob_sha1": capture_meta["git_blob_sha1"],
            },
            "t7_committed_stdout": {
                "commit": t7_meta["commit"],
                "path": t7_meta["path"],
                "git_blob_sha1": t7_meta["git_blob_sha1"],
            },
        },
        "comparison": result,
        "scope": {
            "t7_formal_stop_changed": False,
            "t8_schema_audit_pass_changed": False,
            "transfer_mechanism_identified": False,
            "runtime_or_performance_claim": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        result = audit(document)
    except (OSError, json.JSONDecodeError, AuditError) as exc:
        print(json.dumps({"status": "STOP_ARTIFACT_PROVENANCE_MISMATCH", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

