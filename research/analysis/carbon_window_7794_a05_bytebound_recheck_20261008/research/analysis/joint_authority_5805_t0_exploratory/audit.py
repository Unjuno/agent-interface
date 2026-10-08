import json
import sys
from pathlib import Path


MODES = ("requester_only", "all_owner_conjunction", "scoped_delegation", "deny_all")
EXPECTED = {
    "private_a_read": (1, 1, 1, 0),
    "shared_read_a_only": (1, 0, 0, 0),
    "shared_read_both": (1, 1, 1, 0),
    "private_a_write": (1, 1, 1, 0),
    "shared_a_only": (1, 0, 0, 0),
    "shared_both_grant": (1, 1, 1, 0),
    "shared_conflict": (1, 0, 0, 0),
    "shared_revoked": (1, 0, 0, 0),
    "shared_forged": (1, 0, 0, 0),
    "unknown_owners": (0, 0, 0, 0),
    "shared_delegated_write": (1, 0, 1, 0),
    "delegation_wrong_recipient": (1, 0, 0, 0),
    "delegation_revoked": (1, 0, 0, 0),
    "disclose_wrong_recipient": (1, 0, 0, 0),
    "shared_layout_both": (1, 1, 1, 0),
    "emergency_release": (1, 1, 1, 1),
    "cancel": (1, 1, 1, 1),
}


def check(rows):
    errors = []
    if len(rows) != len(EXPECTED) * len(MODES):
        return ["row count mismatch"]
    index = 0
    for trace_id, expected_modes in EXPECTED.items():
        for mode, expected_admitted in zip(MODES, expected_modes):
            row = rows[index]
            index += 1
            if not isinstance(row, dict):
                errors.append("malformed row")
                continue
            if row.get("trace_id") != trace_id or row.get("mode") != mode:
                errors.append("trace or mode order mismatch")
                continue
            if row.get("admitted") is not bool(expected_admitted):
                errors.append(f"admission mismatch: {trace_id}/{mode}")
            if row.get("attempted") is not bool(expected_admitted):
                errors.append(f"attempt mismatch: {trace_id}/{mode}")
            if row.get("effect_applied") is not False:
                errors.append(f"unexpected synthetic effect: {trace_id}/{mode}")
            if row.get("effect_verified") is not False:
                errors.append(f"permission conflated with effect verification: {trace_id}/{mode}")
            if not isinstance(row.get("reason"), str) or not row["reason"]:
                errors.append(f"missing decision reason: {trace_id}/{mode}")
    if errors:
        return sorted(set(errors))
    for trace_id in ("private_a_read", "private_a_write", "shared_read_both", "shared_both_grant", "shared_layout_both"):
        for mode in ("all_owner_conjunction", "scoped_delegation"):
            row = next((r for r in rows if r.get("trace_id") == trace_id and r.get("mode") == mode), {})
            if row.get("admitted") is not True:
                errors.append(f"valid scoped grant denied: {trace_id}/{mode}")
    if next(r for r in rows if r["trace_id"] == "shared_delegated_write" and r["mode"] == "scoped_delegation")["admitted"] is not True:
        errors.append("narrow delegation did not preserve progress")
    if next(r for r in rows if r["trace_id"] == "shared_delegated_write" and r["mode"] == "deny_all")["admitted"] is not False:
        errors.append("deny-all control unexpectedly admitted a content effect")
    for trace_id in ("shared_conflict", "shared_revoked", "shared_forged", "unknown_owners", "delegation_wrong_recipient", "delegation_revoked", "disclose_wrong_recipient"):
        for mode in ("all_owner_conjunction", "scoped_delegation"):
            row = next(r for r in rows if r["trace_id"] == trace_id and r["mode"] == mode)
            if row["admitted"] or row["attempted"]:
                errors.append(f"fail-closed control admitted: {trace_id}/{mode}")
    return sorted(set(errors))


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.jsonl AUDIT.json")
    raw_path, audit_path = map(Path, sys.argv[1:])
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    errors = check(rows)
    result = {
        "schema": "joint-authority-fixture-audit-v1",
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "rows": len(rows),
        "traces": len(EXPECTED),
        "policies": len(MODES),
        "unauthorized_admissions_joint": sum(
            bool(next(r for r in rows if r["trace_id"] == trace_id and r["mode"] == "all_owner_conjunction")["admitted"])
            for trace_id in ("shared_a_only", "shared_conflict", "shared_revoked", "shared_forged", "unknown_owners", "delegation_wrong_recipient", "disclose_wrong_recipient")
        ),
        "narrow_delegation_progress": next(
            r for r in rows if r["trace_id"] == "shared_delegated_write" and r["mode"] == "scoped_delegation"
        )["admitted"],
        "effect_receipts": sum(r["effect_applied"] for r in rows),
        "errors": errors,
        "scope": "fixture-authored finite authorization contract only; no real owner consent, resource ownership, GUI effect, or product policy",
    }
    with audit_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "errors": len(errors), "rows": len(rows)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
