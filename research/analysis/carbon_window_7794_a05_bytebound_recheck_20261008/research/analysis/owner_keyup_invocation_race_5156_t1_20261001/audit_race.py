"""Independent fail-closed auditor for the host-only invocation race record."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def audit_records(raw, actual_hashes):
    errors = []
    if raw.get("schema") != "owner_keyup_invocation_race_5156_t1_v1":
        errors.append("schema mismatch")
    if raw.get("docker_invocations") != 0 or raw.get("x11_input_invocations") != 0:
        errors.append("experiment exceeded host-only scope")
    baseline = raw.get("baseline", {})
    if baseline.get("candidate_invocations") != 2 or baseline.get("audit_invocations") != 2:
        errors.append("baseline race reproduction count mismatch")
    if baseline.get("statuses") != [0, 0]:
        errors.append("baseline dispatcher statuses mismatch")
    fixed = raw.get("atomic_claim", {})
    if fixed.get("candidate_invocations") != 1:
        errors.append("atomic claim admitted an unexpected candidate count")
    if fixed.get("audit_invocations") != 1 or fixed.get("statuses") != [0, 2]:
        errors.append("atomic claim dispatcher outcome mismatch")
    if fixed.get("claim_state") != "RESERVED_NO_RETRY":
        errors.append("atomic claim marker missing or malformed")
    expected_hashes = raw.get("source_hashes", {})
    if not expected_hashes:
        errors.append("source hash inventory missing")
    for path, expected in expected_hashes.items():
        if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
            errors.append(f"invalid expected source hash: {path}")
        elif actual_hashes.get(path) != expected:
            errors.append(f"source hash mismatch: {path}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[3]
    actual_hashes = {}
    for path in raw.get("source_paths", {}):
        target = root / path
        actual_hashes[path] = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    errors = audit_records(raw, actual_hashes)
    report = {
        "decision": "PASS_HOST_ONLY_RACE_BOUNDARY" if not errors else "FAIL_CLOSED",
        "rows": 2,
        "errors": errors,
        "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
    }
    args.audit.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
