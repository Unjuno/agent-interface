#!/usr/bin/env python3
"""Reproduce control-schema gaps in the frozen Issue #3188 audit-v2.

This is an audit-characterization probe only. It never writes or changes formal
raw evidence; every challenge is applied to an in-memory JSON copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path("research/integration/issue_3188_source_bound_entry_gate_v1")
RUN = pathlib.Path("research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py")
CANDIDATE_AUDIT = pathlib.Path("research/analysis/map01_matched_recovery_entry_gate_3008_v2/audit.py")
AUDITOR_V2 = BASE / "independent_audit_v2.py"
RAW = BASE / "results/formal-02/raw.json"

EXPECTED = {
    RUN.as_posix(): "e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822",
    CANDIDATE_AUDIT.as_posix(): "72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d",
    AUDITOR_V2.as_posix(): "b0785c9008f4873502be7fc90ba259b939fa1662fbd0efb89aff65c38b799d3e",
    RAW.as_posix(): "8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    paths = {name: args.repo_root / name for name in EXPECTED}
    payloads = {name: path.read_bytes() for name, path in paths.items()}
    actual = {name: sha256(payloads[name]) for name in EXPECTED}
    mismatches = [name for name, expected in EXPECTED.items() if actual[name] != expected]
    if mismatches:
        print(json.dumps({"status": "STOP_SOURCE_OR_RAW_HASH_MISMATCH",
                          "mismatches": mismatches, "actual_sha256": actual},
                         indent=2, sort_keys=True))
        return 2

    namespace = {"__name__": "frozen_independent_audit_v2"}
    exec(compile(payloads[AUDITOR_V2.as_posix()], str(paths[AUDITOR_V2.as_posix()]), "exec"),
         namespace)
    audit = namespace["audit"]
    raw = payloads[RAW.as_posix()]
    source_dir = paths[RUN.as_posix()].parent
    baseline = audit(raw, source_dir)

    original = json.loads(raw)
    challenges: dict[str, dict] = {}

    # The named missing_receipt control should remain bound to terminal_integrity=False.
    swapped = json.loads(raw)
    swapped["controls"][0]["terminal_integrity"] = True
    swapped["controls"][0]["arm_bound_audit"] = False
    challenges["missing_receipt_guard_swapped"] = swapped

    # JSON true/false are schema booleans; integer 0 is not the same type.
    typed = json.loads(raw)
    typed["controls"][0]["terminal_integrity"] = 0
    challenges["boolean_false_replaced_with_integer_zero"] = typed

    results = {}
    for name, challenged in challenges.items():
        result = audit(json.dumps(challenged, sort_keys=True).encode("utf-8"), source_dir)
        results[name] = {"status": result["status"], "errors": result["errors"]}

    raw_after = sha256(paths[RAW.as_posix()].read_bytes())
    reproduced = baseline["status"] == "PASS_INDEPENDENT_AUDIT" and all(
        row["status"] == "PASS_INDEPENDENT_AUDIT" and row["errors"] == []
        for row in results.values()
    ) and raw_after == EXPECTED[RAW.as_posix()]

    output = {
        "schema": "issue-3188-audit-v2-control-schema-probe-v1",
        "status": "GAP_REPRODUCED" if reproduced else "PROBE_INTEGRITY_OR_EXPECTATION_FAILURE",
        "base_commit": "eca4bcc1ee839b80442397e27f238c97d6dd6bb4",
        "formal_allocation_disposition_unchanged": "HOLD_FROZEN_AUDITOR_DEFECT",
        "formal_raw_sha256_before_and_after": [actual[RAW.as_posix()], raw_after],
        "source_sha256": actual,
        "baseline_audit": {"status": baseline["status"], "errors": baseline["errors"]},
        "mutation_challenges": results,
        "limitations": [
            "finite mutation characterization of this exact frozen raw and audit-v2 only",
            "host-process execution; not a Docker/OrbStack run",
            "does not alter or replace the formal-02 HOLD",
            "does not establish arbitrary independent-auditor soundness",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
