#!/usr/bin/env python3
"""Independently audit retained A02 raw JSON without running the candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[3]
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKAGE / "RAW.json").read_text(encoding="utf-8"))
checks = []


def check(name, condition, detail=None):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


def duplicates(rows, event):
    counts = {}
    for row in rows:
        if type(row) is dict and row.get("event") == event and type(row.get("id")) is str:
            counts[row["id"]] = counts.get(row["id"], 0) + 1
    return sorted(identifier for identifier, count in counts.items() if count > 1)


source_path = ROOT / "research/doom/doom_controller_failure_cleanup_v1.py"
candidate_path = PACKAGE / "candidate.py"
audit_path = PACKAGE / "audit.py"
source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
audit_sha = hashlib.sha256(audit_path.read_bytes()).hexdigest()
check("raw_schema", RAW.get("schema") == "issue8681-cleanup-identity-a02-raw-v1")
check("allocation_identity", RAW.get("allocation_id") == FREEZE.get("allocation_id"))
check("base_main_identity", RAW.get("base_main_sha") == FREEZE.get("base_main_sha"))
check("source_hash_frozen", source_sha == FREEZE.get("source_sha256") == RAW.get("source_sha256"))
check("candidate_hash_frozen", candidate_sha == FREEZE.get("candidate_sha256"))
check("auditor_hash_frozen", audit_sha == FREEZE.get("audit_sha256"))
check("all_prohibited_claims_false", all(value is False for value in RAW.get("claims", {}).values()))

expected = {
    "valid_single": (True, True),
    "legacy_tokenless": (True, True),
    "mismatched_token": (True, False),
    "distinct_pair": (True, True),
    "duplicate_accept_one_terminal": (False, False),
    "duplicate_terminal_verified_then_failed": (False, False),
    "duplicate_terminal_failed_then_verified": (False, False),
}
rows = RAW.get("cases")
check("case_set_exact", type(rows) is list and len(rows) == len(expected)
      and {row.get("name") for row in rows if type(row) is dict} == set(expected))
if type(rows) is list:
    for row in rows:
        if type(row) is not dict or row.get("name") not in expected:
            continue
        name = row["name"]
        receipt = row.get("receipt") if type(row.get("receipt")) is dict else {}
        terminals_complete, verified_empty = expected[name]
        check(name + "_terminals_complete",
              receipt.get("input_terminals_complete") is terminals_complete)
        check(name + "_verified_empty",
              receipt.get("input_releases_verified_empty") is verified_empty
              and receipt.get("input_release_verified_empty") is verified_empty)
        accepted_dups = duplicates(row.get("events", []), "accepted")
        terminal_dups = duplicates(row.get("events", []), "terminal")
        ambiguous = bool(accepted_dups or terminal_dups)
        check(name + "_ambiguity_metadata",
              receipt.get("event_identity_ambiguous") is ambiguous
              and receipt.get("accepted_duplicate_ids") == accepted_dups
              and receipt.get("terminal_duplicate_ids") == terminal_dups)

passed = all(row["pass"] for row in checks)
result = {
    "schema": "issue8681-cleanup-identity-a02-audit-v1",
    "status": "PASS_CONSTRUCTION_AUDIT" if passed else "FAIL_AUDIT",
    "passed": sum(row["pass"] for row in checks),
    "total": len(checks),
    "checks": checks,
    "source_sha256": source_sha,
    "candidate_sha256": candidate_sha,
    "audit_sha256": audit_sha,
    "scope": "synthetic event reconstruction only; no production occurrence or physical-release claim",
}
(PACKAGE / "AUDIT.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "passed": result["passed"],
                  "total": result["total"]}, sort_keys=True))
if not passed:
    raise SystemExit(1)
