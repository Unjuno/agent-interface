#!/usr/bin/env python3
"""Independently recompute event identity and release outcomes from raw rows."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKAGE / "RAW.json").read_text(encoding="utf-8"))
checks = []


def check(name, condition, detail=None):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


def rows_for(events, event_name):
    return [row for row in events if type(row) is dict and row.get("event") == event_name
            and type(row.get("id")) is str]


def duplicate_ids(rows):
    counts = {}
    for row in rows:
        counts[row["id"]] = counts.get(row["id"], 0) + 1
    return sorted(identifier for identifier, count in counts.items() if count > 1)


def derive(events):
    accepted = rows_for(events, "accepted")
    terminals = rows_for(events, "terminal")
    accepted_dups = duplicate_ids(accepted)
    terminal_dups = duplicate_ids(terminals)
    accepted_ids = {row["id"] for row in accepted}
    terminal_ids = {row["id"] for row in terminals}
    ambiguous = bool(accepted_dups or terminal_dups)
    complete = not ambiguous and accepted_ids.issubset(terminal_ids)
    if not complete:
        return complete, False, ambiguous, accepted_dups, terminal_dups
    accepted_by_id = {row["id"]: row for row in accepted}
    terminal_by_id = {row["id"]: row for row in terminals}
    empty = True
    for identifier in accepted_ids:
        accepted_row = accepted_by_id[identifier]
        terminal_row = terminal_by_id[identifier]
        release = terminal_row.get("release")
        if not (type(release) is dict and release.get("verified") is True
                and release.get("keys_down") == []
                and release.get("buttons_down") == []):
            empty = False
            break
        if "intent_token" in release and not (
                type(accepted_row.get("intent_token")) is str
                and bool(accepted_row.get("intent_token"))
                and release.get("intent_token") == accepted_row["intent_token"]):
            empty = False
            break
    return complete, empty, ambiguous, accepted_dups, terminal_dups


ROOT_PATHS = {
    "production_source": ROOT / "research/doom/doom_controller_failure_cleanup_v1.py",
    "regression_tests": ROOT / "research/doom/test_controller_failure_cleanup_v39.py",
    "candidate": PACKAGE / "candidate.py",
    "auditor": PACKAGE / "audit.py",
}
hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
          for name, path in ROOT_PATHS.items()}
check("raw_schema", RAW.get("schema") == "issue8681-cleanup-identity-a05-raw-v1")
check("allocation_identity", RAW.get("allocation_id") == FREEZE.get("allocation_id"))
check("base_main_identity", RAW.get("base_main_sha") == FREEZE.get("base_main_sha"))
check("all_source_and_runner_hashes_frozen", all(
    hashes[name] == FREEZE.get("files", {}).get(name, {}).get("sha256")
    for name in hashes))
check("source_hash_agrees_with_raw", hashes["production_source"] == RAW.get("source_sha256"))
check("promoted_hash_fields_agree", hashes["production_source"] == FREEZE.get("source_sha256")
      and hashes["candidate"] == FREEZE.get("candidate_sha256")
      and hashes["auditor"] == FREEZE.get("audit_sha256")
      and hashes["regression_tests"] == FREEZE.get("regression_sha256"))
check("prohibited_claims_false", type(RAW.get("claims")) is dict
      and all(value is False for value in RAW["claims"].values()))

expected_names = {
    "valid_single", "legacy_tokenless", "mismatched_token", "distinct_pair",
    "duplicate_accept_one_terminal", "duplicate_terminal_verified_then_failed",
    "duplicate_terminal_failed_then_verified",
}
case_rows = RAW.get("cases")
check("case_set_exact", type(case_rows) is list and len(case_rows) == len(expected_names)
      and {row.get("name") for row in case_rows if type(row) is dict} == expected_names)
if type(case_rows) is list:
    by_name = {row.get("name"): row for row in case_rows if type(row) is dict}
    for name in sorted(expected_names & set(by_name)):
        case = by_name[name]
        events = case.get("events") if type(case.get("events")) is list else []
        observed = case.get("receipt") if type(case.get("receipt")) is dict else {}
        complete, empty, ambiguous, accepted_dups, terminal_dups = derive(events)
        accepted_n = 2 if name in ("distinct_pair", "duplicate_accept_one_terminal") else 1
        terminal_n = 2 if name.startswith("duplicate_terminal_") or name == "distinct_pair" else 1
        check(name + "_case_shape", len(rows_for(events, "accepted")) == accepted_n
              and len(rows_for(events, "terminal")) == terminal_n)
        check(name + "_terminals_complete_recomputed",
              observed.get("input_terminals_complete") is complete)
        check(name + "_verified_empty_recomputed",
              observed.get("input_releases_verified_empty") is empty
              and observed.get("input_release_verified_empty") is empty)
        check(name + "_ambiguity_metadata_recomputed",
              observed.get("event_identity_ambiguous") is ambiguous
              and observed.get("accepted_duplicate_ids") == accepted_dups
              and observed.get("terminal_duplicate_ids") == terminal_dups)
        if name == "legacy_tokenless":
            terminal_rows = rows_for(events, "terminal")
            release = terminal_rows[0].get("release") if len(terminal_rows) == 1 else None
            check(name + "_actually_tokenless",
                  type(release) is dict and "intent_token" not in release)
        if name == "mismatched_token":
            accepted_rows = rows_for(events, "accepted")
            terminal_rows = rows_for(events, "terminal")
            release = terminal_rows[0].get("release") if len(terminal_rows) == 1 else None
            check(name + "_actually_mismatched",
                  len(accepted_rows) == len(terminal_rows) == 1
                  and type(release) is dict
                  and release.get("intent_token") != accepted_rows[0].get("intent_token"))
        if name.startswith("duplicate_terminal_"):
            terminal_rows = rows_for(events, "terminal")
            check(name + "_terminals_conflict",
                  len(terminal_rows) == 2
                  and terminal_rows[0].get("release", {}).get("verified")
                  is not terminal_rows[1].get("release", {}).get("verified"))

passed = all(item["pass"] for item in checks)
result = {
    "schema": "issue8681-cleanup-identity-a05-audit-v1",
    "status": "PASS_CONSTRUCTION_AUDIT" if passed else "FAIL_AUDIT",
    "passed": sum(item["pass"] for item in checks),
    "total": len(checks),
    "checks": checks,
    "hashes": hashes,
    "scope": "synthetic event reconstruction only; no production-occurrence or physical-release claim",
}
(PACKAGE / "AUDIT.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "passed": result["passed"],
                  "total": result["total"]}, sort_keys=True))
if not passed:
    raise SystemExit(1)
