#!/usr/bin/env python3
"""Read-only integrity audit for the retained partial construction artifacts."""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote
from io import BytesIO


RAW = Path("/raw")
EVIDENCE = Path("/evidence")
OUT = Path("/out")
EXPECTED_COUNT = 62
EXPECTED_CASES = 31
EXPECTED_ARCHIVE_SHA256 = "3c57aa270e8bd3309e3b8c5aaff005b3160b501fd1391c428bace7bccee5123e"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (EVIDENCE / "PARTIAL_RAW_MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("allocation") != "effect-receipt-wal-vs-delete-3991-20260928-01":
        fail("allocation identity mismatch")
    if manifest.get("classification") != "partial construction raw; no formal result":
        fail("manifest classification mismatch")
    rows = manifest.get("files")
    if type(rows) is not list or len(rows) != EXPECTED_COUNT:
        fail("manifest file denominator mismatch")
    if manifest.get("file_count") != EXPECTED_COUNT or manifest.get("case_directories") != EXPECTED_CASES:
        fail("manifest declared counts mismatch")

    expected = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"path", "bytes", "sha256"}:
            fail("malformed manifest row")
        rel = Path(row["path"])
        if rel.is_absolute() or ".." in rel.parts or rel.as_posix() in expected:
            fail("unsafe or duplicate manifest path")
        if type(row["bytes"]) is not int or row["bytes"] < 0:
            fail("invalid manifest byte length")
        digest = row["sha256"]
        if type(digest) is not str or len(digest) != 64:
            fail("invalid manifest digest")
        expected[rel.as_posix()] = row

    raw_root = RAW / "cases"
    actual_files = sorted(p for p in raw_root.rglob("*") if p.is_file())
    actual_rel = {p.relative_to(raw_root).as_posix(): p for p in actual_files}
    if set(actual_rel) != set(expected):
        fail("raw filesystem membership differs from manifest")

    file_checks = []
    sqlite_checks = []
    for rel in sorted(expected):
        path = actual_rel[rel]
        data = path.read_bytes()
        row = expected[rel]
        digest = sha256(data)
        if len(data) != row["bytes"] or digest != row["sha256"]:
            fail("raw bytes differ from manifest: " + rel)
        file_checks.append({"path": rel, "bytes": len(data), "sha256": digest})
        uri = "file:" + quote(str(path), safe="/:\\") + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as con:
            integrity = [r[0] for r in con.execute("PRAGMA integrity_check")]
            if integrity != ["ok"]:
                fail("SQLite integrity_check failed: " + rel)
            tables = sorted(r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
            sqlite_checks.append({"path": rel, "integrity_check": integrity,
                                  "tables": tables})

    archive_b64 = (EVIDENCE / "partial-raw.zip.b64").read_bytes()
    archive = base64.b64decode(archive_b64.strip(), validate=True)
    archive_sha = sha256(archive)
    archive_meta = manifest.get("archive")
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        fail("decoded archive digest differs from preregistered digest")
    if type(archive_meta) is not dict or archive_meta.get("sha256") != archive_sha:
        fail("archive digest differs from manifest")
    if archive_meta.get("bytes") != len(archive):
        fail("archive length differs from manifest")

    with zipfile.ZipFile(BytesIO(archive)) as zf:
        names = [i.filename for i in zf.infolist() if not i.is_dir()]
        expected_names = ["cases/" + rel for rel in sorted(expected)]
        if sorted(names) != expected_names or len(names) != len(set(names)):
            fail("ZIP member inventory differs from manifest")
        for rel in sorted(expected):
            archived = zf.read("cases/" + rel)
            row = expected[rel]
            if len(archived) != row["bytes"] or sha256(archived) != row["sha256"]:
                fail("ZIP member bytes differ from manifest: " + rel)

    cases = sorted({Path(rel).parts[0] for rel in expected})
    if len(cases) != EXPECTED_CASES:
        fail("case directory denominator mismatch")
    missing_receipts = [x["path"] for x in sqlite_checks
                        if x["path"].endswith("/effect.db") and "receipts" not in x["tables"]]
    report = {
        "schema": "effect-receipt-wal-partial-raw-audit-v1",
        "allocation": manifest["allocation"],
        "classification": "PASS_PARTIAL_RAW_BYTE_AND_SQLITE_INTEGRITY_ONLY",
        "scientific_result": None,
        "manifest_sha256": sha256(manifest_bytes),
        "archive_sha256": archive_sha,
        "archive_bytes": len(archive),
        "file_count": len(file_checks),
        "case_directories": len(cases),
        "sqlite_integrity_checks": len(sqlite_checks),
        "effect_databases_without_receipts_table": missing_receipts,
        "errors": [],
        "scope": "Retained partial construction evidence only; no WAL-vs-DELETE inference.",
        "files": file_checks,
        "sqlite": sqlite_checks,
    }
    encoded = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (OUT / "AUDIT.json").write_bytes(encoded)
    (OUT / "REPORT.md").write_text(
        "# Partial raw integrity audit\n\n"
        "Result: `PASS_PARTIAL_RAW_BYTE_AND_SQLITE_INTEGRITY_ONLY`.\n\n"
        f"- Files checked: {len(file_checks)} / {EXPECTED_COUNT}\n"
        f"- Case directories: {len(cases)} / {EXPECTED_CASES}\n"
        f"- SQLite integrity checks: {len(sqlite_checks)}\n"
        f"- Decoded ZIP SHA-256: `{archive_sha}`\n"
        f"- Effect DBs missing a `receipts` table: {len(missing_receipts)}\n\n"
        "This audit covers retained partial construction bytes only. It is not a formal experiment result and makes no WAL-vs-DELETE inference.\n",
        encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "classification", "file_count", "case_directories", "sqlite_integrity_checks",
        "archive_sha256", "effect_databases_without_receipts_table")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"classification": "STOP_PARTIAL_RAW_AUDIT",
                          "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2)

