#!/usr/bin/env python3
"""Audit the retained base/candidate unittest output without rerunning tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
RESULT = HERE / "RESULT.json"
EXPECTED_FILES = {
    "README.md",
    "audit-attempt-v1-failure.txt",
    "audit_recheck.py",
    "frozen_test.py",
    "raw/base.txt",
    "raw/candidate.txt",
    "RESULT.json",
    "run_independent_recheck.py",
    "write_manifest.py",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    import hashlib

    return hashlib.sha1(header + data).hexdigest()


def fail(message: str) -> int:
    print(f"AUDIT_FAIL {message}")
    return 1


def main() -> int:
    try:
        result = json.loads(RESULT.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail(f"result_read:{type(exc).__name__}")
    if result.get("format") != "appserver-eof-reap-independent-recheck-v1":
        return fail("result_format")
    if result.get("base") != "9fb2dd6782d1d1477a00d14be870487fd4c54fa2":
        return fail("base_identity")
    if result.get("candidate") != "c6f5a122afee85e44bec5c39b80f02e6b939d56a":
        return fail("candidate_identity")
    frozen_test = HERE / "frozen_test.py"
    try:
        test_data = frozen_test.read_bytes()
    except Exception as exc:
        return fail(f"frozen_test_read:{type(exc).__name__}")
    if git_blob_sha1(test_data) != "6f1c5c19fa219b1fac46c65fd7d857b7a02cc548":
        return fail("frozen_test_blob")
    if sha256(test_data) != "f3c405499d6e9a4b6debace1632666a3d15c44e85fdee23b7ef62536ba4095f8":
        return fail("frozen_test_sha256")
    if len(result.get("runs", [])) != 2:
        return fail("run_count")
    rows = {row.get("label"): row for row in result["runs"]}
    if set(rows) != {"base", "candidate"}:
        return fail("run_labels")
    for label, row in rows.items():
        expected_blob = {
            "base": "338b5fbdf436e14768274b9de6a3d3bb13fd274c",
            "candidate": "02193be85d0d5e29a155ec7151d1c44c5c6d6ff2",
        }[label]
        if row.get("source_git_blob") != expected_blob:
            return fail(f"{label}_source_blob")
        if row.get("test_git_blob") != "6f1c5c19fa219b1fac46c65fd7d857b7a02cc548":
            return fail(f"{label}_test_blob")
        if row.get("test_sha256") != sha256(test_data):
            return fail(f"{label}_test_sha256")
        path = HERE / row["raw_log"]
        try:
            raw = path.read_bytes()
        except Exception as exc:
            return fail(f"{label}_log_read:{type(exc).__name__}")
        if sha256(raw) != row.get("raw_log_sha256"):
            return fail(f"{label}_log_hash")
        text = raw.decode("utf-8")
        match = re.search(r"Ran (\d+) tests? in [^\n]+\n\n(OK|FAILED \(.*\))", text)
        if not match or int(match.group(1)) != 8:
            return fail(f"{label}_unittest_summary")
        row["audited_summary"] = match.group(2)
    base_text = (HERE / rows["base"]["raw_log"]).read_text(encoding="utf-8")
    candidate_text = (HERE / rows["candidate"]["raw_log"]).read_text(encoding="utf-8")
    if rows["base"]["exit_code"] == 0:
        return fail("base_expected_nonzero")
    if not re.search(r"Ran 8 tests in [^\n]+\n\nFAILED \(failures=2, errors=2\)", base_text):
        return fail("base_expected_2_fail_2_error")
    if not re.search(
        r"test_close_reaps_eof_leader_without_prior_poll \([^\n]+\) \.\.\. ERROR",
        base_text,
    ):
        return fail("base_missing_eof_regression")
    if "PermissionError: [Errno 1] Operation not permitted" not in base_text:
        return fail("base_missing_darwin_reproduction")
    if rows["candidate"]["exit_code"] != 0 or not re.search(
        r"Ran 8 tests in [^\n]+\n\nOK", candidate_text
    ):
        return fail("candidate_expected_8_pass")
    if not re.search(
        r"test_close_reaps_eof_leader_without_prior_poll \([^\n]+\) \.\.\. ok",
        candidate_text,
    ):
        return fail("candidate_missing_eof_pass")
    if result.get("disposition") != "PASS_REPAIR_RECHECK":
        return fail("disposition")
    try:
        manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return fail(f"manifest_read:{type(exc).__name__}")
    if manifest.get("format") != "appserver-eof-reap-independent-recheck-manifest-v1":
        return fail("manifest_format")
    entries = {entry.get("path"): entry for entry in manifest.get("files", [])}
    if set(entries) != EXPECTED_FILES:
        return fail("manifest_inventory")
    for relative, entry in entries.items():
        data = (HERE / relative).read_bytes()
        if len(data) != entry.get("bytes") or sha256(data) != entry.get("sha256"):
            return fail(f"manifest_hash:{relative}")
    print("PASS_INDEPENDENT_RAW_RECHECK base=2fail+2error candidate=8pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
