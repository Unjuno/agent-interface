#!/usr/bin/env python3
"""Independent raw/source audit for terminal-release composition A01."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_PATH = (
    "research/integration/mindustry_three_arm_economics_20260928/"
    "target_socket_submit_v1.py"
)
STATUS_HEAD = "bd0ba260acf885d7b859d665571b2c3260666642"
RELEASE_HEAD = "1d7bb20bcde67333f58e41a24f8dce68f8561ffd"
ANCHOR = "        terminal = terminals[0]\n        release = terminal.get(\"release\")"
COMPOSED = (
    "        terminal = terminals[0]\n"
    "        if terminal.get(\"status\") != \"completed\":\n"
    "            raise SocketSubmitStop(\"matching terminal must report completed action\")\n"
    "        release = terminal.get(\"release\")"
)
STATUSES = {
    "completed": True,
    "failed": False,
    "cancelled": False,
    "needs_decision": False,
    "explicit_null": False,
    "missing": False,
    "boolean_true": False,
    "uppercase": False,
}
RELEASES = {
    "minimal_empty": True,
    "source_owner_release": True,
    "held_key": False,
    "held_button": False,
    "missing_keys": False,
    "missing_buttons": False,
    "unverified": False,
    "missing_release": False,
    "unknown_field": False,
    "malformed_metadata": False,
}


def blob(revision: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{SOURCE_PATH}"], cwd=HERE, stderr=subprocess.PIPE
    )


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "RAW.json"
    audit_path = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "AUDIT.json"
    plan = (HERE / "PLAN.md").read_text(encoding="utf-8")
    if STATUS_HEAD not in plan or RELEASE_HEAD not in plan:
        fail("plan does not pin both candidate heads")
    status_source = blob(STATUS_HEAD).decode("utf-8")
    release_source = blob(RELEASE_HEAD).decode("utf-8")
    if COMPOSED not in status_source:
        fail("status candidate does not contain the exact completed-status guard")
    if release_source.count(ANCHOR) != 1:
        fail("release candidate source anchor is absent or ambiguous")
    rebuilt = release_source.replace(ANCHOR, COMPOSED, 1).encode("utf-8")
    candidate = (HERE / "candidate_adapter.py").read_bytes()
    if rebuilt != candidate:
        fail("candidate bytes do not equal the composition of pinned PR blobs")

    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    if raw.get("schema") != "mindustry_terminal_release_composition_raw_v1":
        fail("raw schema mismatch")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate).hexdigest():
        fail("candidate hash mismatch")
    if raw.get("status_source_blob") != subprocess.check_output(
            ["git", "rev-parse", f"{STATUS_HEAD}:{SOURCE_PATH}"], cwd=HERE, text=True).strip():
        fail("status source blob mismatch")
    if raw.get("release_source_blob") != subprocess.check_output(
            ["git", "rev-parse", f"{RELEASE_HEAD}:{SOURCE_PATH}"], cwd=HERE, text=True).strip():
        fail("release source blob mismatch")
    if raw.get("case_count") != len(STATUSES) * len(RELEASES):
        fail("wrong matrix size")
    rows = raw.get("rows")
    if type(rows) is not list or len(rows) != raw["case_count"]:
        fail("row count mismatch")
    seen = set()
    mismatches = []
    for row in rows:
        if type(row) is not dict:
            fail("row must be an object")
        key = (row.get("status_case"), row.get("release_case"))
        if key in seen or key[0] not in STATUSES or key[1] not in RELEASES:
            fail(f"duplicate or unknown matrix key: {key!r}")
        seen.add(key)
        expected = "accepted" if STATUSES[key[0]] and RELEASES[key[1]] else "rejected"
        if row.get("observed") != expected:
            mismatches.append({"case": key, "expected": expected, "observed": row.get("observed")})
        if expected == "accepted" and row.get("receipt") != {
                "request_id": "composition-a01-action", "terminal": True, "released": True}:
            mismatches.append({"case": key, "expected_receipt": True, "receipt": row.get("receipt")})
        if expected == "rejected" and row.get("receipt") is not None:
            mismatches.append({"case": key, "expected_receipt": None, "receipt": row.get("receipt")})
    if len(seen) != len(STATUSES) * len(RELEASES):
        fail("matrix is incomplete")
    disposition = "PASS_COMPOSED_GATES_SCOPED" if not mismatches else "FAIL_COMPOSITION_MATRIX"
    audit = {
        "schema": "mindustry_terminal_release_composition_audit_v1",
        "disposition": disposition,
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "matrix_cases": len(seen),
        "accepted_expected_and_observed": sum(
            1 for row in rows if row["observed"] == "accepted"),
        "rejected_expected_and_observed": sum(
            1 for row in rows if row["observed"] == "rejected"),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "source_scope": "exact open-PR Git blobs; derived composition candidate is not current main",
        "live_authority_or_effect_verified": False,
    }
    output = json.dumps(audit, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    audit_path.write_bytes(output)
    print(json.dumps(audit, sort_keys=True))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
