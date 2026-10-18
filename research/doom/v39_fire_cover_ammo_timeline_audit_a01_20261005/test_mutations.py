#!/usr/bin/env python3
"""Reproduce v1 false passes and require both v2 reconstructions to reject them."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import audit_v2
import independent_audit_v2

ROOT = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip())
FREEZE = audit_v2.FREEZE
MUTATIONS = FREEZE["reported_false_pass_mutations"]
RECORD = ROOT / "MUTATION_TEST_FINAL.json"


def apply_mutation(document, mutation):
    value = copy.deepcopy(mutation["value"])
    node = document
    for component in mutation["path"][:-1]:
        node = node[component]
    node[mutation["path"][-1]] = value


def legacy_result(mutation, original):
    with tempfile.TemporaryDirectory(prefix="issue59-v39-audit-v1-") as directory:
        case = Path(directory)
        freeze_bytes = audit_v2.read_pin(FREEZE["parent_package_files"]["freeze"])
        script_bytes = audit_v2.read_pin(FREEZE["parent_package_files"]["auditor"])
        (case / "FREEZE.json").write_bytes(freeze_bytes)
        (case / "audit.py").write_bytes(script_bytes)
        changed = copy.deepcopy(original)
        apply_mutation(changed, mutation)
        (case / "RESULT.json").write_text(
            json.dumps(changed, sort_keys=True), encoding="utf-8"
        )
        completed = subprocess.run(
            [sys.executable, "-B", str(case / "audit.py")],
            cwd=REPO, capture_output=True, text=True
        )
        audit_path = case / "AUDIT.json"
        if completed.returncode != 0 or not audit_path.is_file():
            raise AssertionError("legacy auditor did not complete: " + mutation["id"])
        return json.loads(audit_path.read_text(encoding="utf-8"))


def run(record=False):
    report, events, original = audit_v2.load_inputs()
    expected = audit_v2.build_expected(report, events)
    if audit_v2.mismatches(expected, original):
        raise AssertionError("unmodified v1 RESULT did not match the raw reconstruction")
    independent_expected, independent_original = (
        independent_audit_v2.independently_reconstruct()
    )
    if independent_audit_v2.differences(independent_expected, independent_original):
        raise AssertionError("independent baseline reconstruction did not pass")

    outcomes = []
    for mutation in MUTATIONS:
        legacy = legacy_result(mutation, original)
        v2_failures = audit_v2.mismatches(
            expected, _mutated(original, mutation)
        )
        independent_failures = independent_audit_v2.differences(
            independent_expected, _mutated(original, mutation)
        )
        if legacy.get("disposition") != "PASS" or legacy.get("passed") != 5:
            raise AssertionError("reported v1 false pass did not reproduce: "
                                 + mutation["id"])
        if not v2_failures or not independent_failures:
            raise AssertionError("v2 missed a corruption: " + mutation["id"])
        outcomes.append({
            "mutation": mutation["id"],
            "legacy_v1": legacy["disposition"],
            "legacy_checks": "{}/{}".format(legacy["passed"], legacy["total"]),
            "candidate_rejected": True,
            "candidate_mismatch_fields": v2_failures,
            "independent_rejected": True,
            "independent_mismatch_fields": independent_failures,
        })
    result = {
        "format": "issue59-v39-fire-cover-ammo-audit-a01-mutation-test-v1",
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "unmodified_candidate_passed": True,
        "unmodified_independent_audit_passed": True,
        "legacy_false_passes_reproduced": len(outcomes),
        "v2_mutations_rejected": sum(row["candidate_rejected"] for row in outcomes),
        "independent_mutations_rejected":
            sum(row["independent_rejected"] for row in outcomes),
        "cases": outcomes,
        "disposition": "PASS_MUTATION_REJECTION_SCOPED",
    }
    if record:
        if RECORD.exists():
            raise SystemExit("STOP_OUTPUT_EXISTS")
        RECORD.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"))
                          + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


def _mutated(original, mutation):
    result = copy.deepcopy(original)
    apply_mutation(result, mutation)
    return result


if __name__ == "__main__":
    run(record="--record" in sys.argv[1:])
