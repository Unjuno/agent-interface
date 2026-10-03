"""Offline exact-source/Git-blob classification for the 11 T7 PR artifacts."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    pass


T7_COMMIT = "684831240f9848e850736781edb98322949e8d8a"
ROOT = "research/analysis/wslc_retained_audit_5309_t7_20261003/"
EXPECTED = {
    "FREEZE.json": ("FREEZE.json", 2577, "3a92930cbfdd77e54fd760fdd214701c67959625f951cf86c4d4eb5ca034fa48"),
    "MANIFEST.json": ("stage-output/MANIFEST.json", 2569, "8963fcba33a141fce235812b16ff6de0baea0b1da0520c96df5693c7eee24178"),
    "README.md": ("README.md", 4287, "0c2e0da124bbde80ed1193147f018ac0bdfcee3c5069f9090537a9fd66eeb70f"),
    "RESULT.md": ("stage-output/RESULT.md", 1326, "1820853498306535262b74d709677c63202e8e1e7099d4d35d5bb0702fdf249e"),
    "RUN.json": ("stage-output/RUN.json", 3627, "7ad429667ccc1765ec090c5a783a9012c3e47bc08c1a2bce6a0e6dcb64bb87b8"),
    "STOP.json": ("stage-output/STOP.json", 1746, "1de6e2ab65e8972e8207c6ab28ac2ad51d5e1d744873ff496cb87d3606e09a1d"),
    "audit.stdout.json": ("stage-output/audit.stdout.json", 306, "604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f"),
    "host_verification.stderr.txt": ("stage-output/host_verification.stderr.public.txt", 523, "725911a7aa3869e758f872bd9c253779eba2832400f13af5c017a811c294d758"),
    "host_verification_failure.json": ("stage-output/host_verification_failure.json", 301, "5c8aaff65903a6e60f92c2087c765b9f8bc4d3275b4a589af0dce0bbd643fed1"),
    "test_verify_receipt.py": ("test_verify_receipt.py", 2268, "3be51148ea26dad6fcf1fb2d573bf715e6408b1deb144e48883a8b7ce35187c0"),
    "verify_receipt.py": ("verify_receipt.py", 1771, "9b3bfd65028a8bc5a5de7a82d3b90e0daa2298cd33e599640767b1d424c970dd"),
}
MANIFEST_RECORDS = {
    "audit.stdout.json": "audit.stdout.json",
    "host_verification_failure.json": "host_verification_failure.json",
    "host_verification.stderr.txt": "host_verification.stderr.txt",
    "RESULT.md": "RESULT.md",
    "RUN.json": "RUN.json",
    "STOP.json": "STOP.json",
}


def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def validate_source(data: bytes, expected_bytes: int, expected_sha256: str) -> None:
    if len(data) != expected_bytes:
        raise AuditError("frozen local source byte count mismatch")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise AuditError("frozen local source SHA-256 mismatch")


def classify_remote_blob(data: bytes, remote_sha1: str, remote_bytes: int) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", remote_sha1):
        raise AuditError("invalid remote Git blob id")
    if remote_bytes == len(data) and remote_sha1 == git_blob_sha1(data):
        return "EXACT_SOURCE"
    if (
        data.endswith(b"\n")
        and remote_bytes == len(data) + 2
        and remote_sha1 == git_blob_sha1(data + b"\r\n")
    ):
        return "SOURCE_PLUS_CRLF"
    raise AuditError("remote file differs beyond allowed exact/CRLF classifications")


def audit(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("schema") != "t7-publication-byte-audit-v1":
        raise AuditError("unexpected snapshot schema")
    if document.get("t7_head_commit") != T7_COMMIT:
        raise AuditError("unexpected T7 commit")
    rows = document.get("files")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise AuditError("expected exactly 11 frozen T7 files")
    by_name: dict[str, dict[str, Any]] = {}
    output = []
    for row in rows:
        if not isinstance(row, dict):
            raise AuditError("invalid file entry")
        name = row.get("name")
        if name not in EXPECTED or name in by_name:
            raise AuditError("unknown or duplicate T7 file")
        local_path, expected_bytes, expected_sha = EXPECTED[name]
        if row.get("local_path") != local_path:
            raise AuditError(f"{name}: frozen source path mismatch")
        if row.get("repository_path") != ROOT + name:
            raise AuditError(f"{name}: repository path mismatch")
        try:
            data = base64.b64decode(row.get("source_base64", ""), validate=True)
        except (binascii.Error, ValueError, TypeError) as exc:
            raise AuditError(f"{name}: invalid frozen source base64") from exc
        validate_source(data, expected_bytes, expected_sha)
        classification = classify_remote_blob(
            data,
            row.get("remote_git_blob_sha1", ""),
            row.get("remote_bytes", -1),
        )
        row["source_bytes"] = len(data)
        row["source_sha256"] = expected_sha
        row["classification"] = classification
        by_name[name] = row
        output.append({
            "name": name,
            "source_bytes": len(data),
            "source_sha256": expected_sha,
            "remote_bytes": row["remote_bytes"],
            "remote_git_blob_sha1": row["remote_git_blob_sha1"],
            "classification": classification,
        })
    if set(by_name) != set(EXPECTED):
        raise AuditError("T7 file set incomplete")

    manifest_row = by_name["MANIFEST.json"]
    manifest_bytes = base64.b64decode(manifest_row["source_base64"], validate=True)
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("frozen source manifest is not valid JSON") from exc
    recorded = manifest.get("records", {})
    for manifest_name, audit_name in MANIFEST_RECORDS.items():
        row = by_name[audit_name]
        claim = recorded.get(manifest_name)
        if not isinstance(claim, dict):
            raise AuditError(f"manifest record missing: {manifest_name}")
        if claim.get("bytes") != row["source_bytes"] or claim.get("sha256") != row["source_sha256"]:
            raise AuditError(f"manifest source claim mismatch: {manifest_name}")
        row["manifest_source_claim_verified"] = True
        row["manifest_matches_remote_blob"] = row["classification"] == "EXACT_SOURCE"

    exact_count = sum(x["classification"] == "EXACT_SOURCE" for x in output)
    crlf_count = sum(x["classification"] == "SOURCE_PLUS_CRLF" for x in output)
    return {
        "status": "PASS_T7_PUBLICATION_BYTES_CLASSIFIED",
        "t7_formal_stop_changed": False,
        "file_count": len(output),
        "exact_source_count": exact_count,
        "source_plus_crlf_count": crlf_count,
        "manifest_record_count": len(MANIFEST_RECORDS),
        "manifest_claims_checked": True,
        "files": sorted(output, key=lambda x: x["name"]),
        "scope": {
            "publication_step_identified": False,
            "connector_wide_behavior_claimed": False,
            "wslc_rerun": False,
            "docker_run": False,
            "performance_or_memory_claim": False,
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
        print(json.dumps({"status": "STOP_T7_PUBLICATION_BYTES_MISMATCH", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
