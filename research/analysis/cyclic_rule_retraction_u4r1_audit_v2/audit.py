#!/usr/bin/env python3
"""Independent posthoc audit; imports neither #4449 study nor auditor."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOTS = {"E0", "E1"}
CLAIMS = ("A", "B")
RULES = (
    ("r0", "A", ("E0",)),
    ("r1", "A", ("B",)),
    ("r2", "A", ("E1", "B")),
    ("r3", "B", ("E1",)),
    ("r4", "B", ("A",)),
    ("r5", "B", ("E0", "A")),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def least_model(active):
    closed = []
    for bits in itertools.product((False, True), repeat=len(CLAIMS)):
        interp = {claim for claim, bit in zip(CLAIMS, bits) if bit}
        known = ROOTS | interp
        if all(head in known for _, head, body in active if set(body) <= known):
            closed.append(interp)
    return set.intersection(*closed)


def dependency_cone(deleted, active):
    cone = {deleted[1]}
    while True:
        grown = cone | {head for _, head, body in active if set(body) & cone}
        if grown == cone:
            return cone
        cone = grown


def local_support(before, active):
    known = set(before) | ROOTS
    while True:
        unsupported = {
            claim for claim in CLAIMS
            if claim in known and not any(
                head == claim and set(body) <= known for _, head, body in active
            )
        }
        if not unsupported:
            return known & set(CLAIMS)
        known -= unsupported


def expected_rows(masks=range(64)):
    for mask in masks:
        before_active = tuple(rule for i, rule in enumerate(RULES) if mask & (1 << i))
        before = least_model(before_active)
        yield {
            "mask": mask,
            "deleted_rule": None,
            "active_rules_before": [r[0] for r in before_active],
            "active_rules_after": [r[0] for r in before_active],
            "before": sorted(before),
            "affected_cone": [],
            "clear_and_rederive": sorted(before),
            "full_rebuild": sorted(before),
            "local_support": sorted(before),
            "blind_invalidate": sorted(before),
        }
        for i, deleted in enumerate(RULES):
            if not mask & (1 << i):
                continue
            active = tuple(r for r in before_active if r[0] != deleted[0])
            cone = dependency_cone(deleted, active)
            truth = least_model(active)
            yield {
                "mask": mask,
                "deleted_rule": deleted[0],
                "active_rules_before": [r[0] for r in before_active],
                "active_rules_after": [r[0] for r in active],
                "before": sorted(before),
                "affected_cone": sorted(cone),
                "clear_and_rederive": sorted(truth),
                "full_rebuild": sorted(truth),
                "local_support": sorted(local_support(before, active)),
                "blind_invalidate": sorted(set(before) - cone),
            }


MUTATIONS = (
    (0, "mask", 63),
    (0, "deleted_rule", "r0"),
    (1, "before", []),
    (1, "active_rules_before", []),
    (1, "active_rules_after", ["r1"]),
    (1, "affected_cone", []),
    (1, "clear_and_rederive", ["A"]),
    (1, "full_rebuild", ["A"]),
    (7, "local_support", []),
    (29, "blind_invalidate", []),
)
SELF_TEST_MUTATIONS = MUTATIONS[:9] + ((3, "blind_invalidate", []),)


def verify_rows(rows, masks=range(64)):
    expected = list(expected_rows(masks))
    errors = []
    if len(rows) != len(expected):
        errors.append(f"row_count:{len(rows)}")
        return errors
    for index, (actual, wanted) in enumerate(zip(rows, expected)):
        if actual != wanted:
            errors.append(f"row_mismatch:{index}")
        if actual.get("deleted_rule") is not None:
            if not set(actual.get("full_rebuild", [])) <= set(actual.get("before", [])):
                errors.append(f"adds_claim:{index}")
            outside = set(CLAIMS) - set(actual.get("affected_cone", []))
            if any((claim in actual.get("before", [])) != (claim in actual.get("full_rebuild", [])) for claim in outside):
                errors.append(f"outside_cone_changed:{index}")
    return errors


def self_test():
    rows = list(expected_rows((1, 11, 19)))
    base_errors = verify_rows(rows, (1, 11, 19))
    controls = []
    for number, (index, key, replacement) in enumerate(SELF_TEST_MUTATIONS, 1):
        changed = json.loads(json.dumps(rows))
        if index >= len(changed):
            controls.append({"control": number, "effective": False, "rejected": False})
            continue
        effective = changed[index].get(key) != replacement
        changed[index][key] = replacement
        rejected = bool(verify_rows(changed, (1, 11, 19)))
        controls.append({"control": number, "effective": effective, "rejected": rejected})
    ok = not base_errors and all(x["effective"] and x["rejected"] for x in controls)
    return {"decision": "PASS_SELF_TEST" if ok else "STOP_SELF_TEST", "rows": len(rows), "errors": base_errors, "controls": controls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--study", type=Path)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        report = self_test()
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(0 if report["decision"] == "PASS_SELF_TEST" else 2)
    if not all((args.study, args.run, args.freeze, args.out)):
        parser.error("formal mode requires --study --run --freeze --out")

    study = args.study
    run = args.run
    freeze = json.loads(args.freeze.read_text())
    provenance = []
    for rel, expected in freeze["audit_source_sha256"].items():
        if sha((args.freeze.parent / rel).read_bytes()) != expected:
            provenance.append(f"audit_source_sha256:{rel}")
    for rel, expected in freeze["original_files"].items():
        observed = sha((study / rel).read_bytes())
        if observed != expected["sha256"]:
            provenance.append(f"original_sha256:{rel}")
    rows_bytes = (run / "rows.jsonl").read_bytes()
    conditions_bytes = (run / "conditions.jsonl").read_bytes()
    input_bytes = (run / "input.json").read_bytes()
    process_bytes = (run / "process.json").read_bytes()
    original_audit_bytes = (run / "audit.json").read_bytes()
    for key, data in (("rows", rows_bytes), ("conditions", conditions_bytes), ("input", input_bytes), ("process", process_bytes), ("original_audit", original_audit_bytes)):
        if sha(data) != freeze["formal_files"][key]["sha256"]:
            provenance.append(f"formal_sha256:{key}")
    rows = [json.loads(line) for line in rows_bytes.splitlines()]
    conditions = [json.loads(line) for line in conditions_bytes.splitlines()]
    expected = list(expected_rows())
    expected_conditions = [{"mask": row["mask"], "deleted_rule": row["deleted_rule"]} for row in expected]
    expected_newline = "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in expected_conditions).encode()
    expected_escaped = "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\\n" for x in expected_conditions).encode()
    process = json.loads(process_bytes)
    input_json = json.loads(input_bytes)
    original_freeze = json.loads((study / "FREEZE.json").read_text())
    old_report = json.loads(original_audit_bytes)
    if conditions != expected_conditions or conditions_bytes != expected_newline:
        provenance.append("condition_sequence")
    if sha(expected_newline) != freeze["formal_files"]["conditions"]["sha256"]:
        provenance.append("frozen_expected_newline_hash")
    if sha(expected_escaped) != original_freeze["formal_conditions_sha256"]:
        provenance.append("original_digest_not_escaped_separator")
    if process.get("phase") != "formal" or process.get("exit_code") != 0 or process.get("rows") != 256:
        provenance.append("process_identity")
    if process.get("rows_sha256") != sha(rows_bytes) or process.get("conditions_sha256") != sha(conditions_bytes):
        provenance.append("process_output_hashes")
    if process.get("input_sha256") != sha(input_bytes):
        provenance.append("process_input_hash")
    if process.get("study_sha256") != original_freeze["source_sha256"]["study.py"]:
        provenance.append("executed_study_hash")
    if input_json.get("expected_conditions") != 256 or len(rows) != 256:
        provenance.append("denominator")
    if original_freeze.get("formal_invocations_authorized") != 1 or original_freeze.get("formal_invocations_before_freeze") != 0:
        provenance.append("allocation_freeze")
    semantic_errors = verify_rows(rows)
    controls = []
    for number, (index, key, replacement) in enumerate(MUTATIONS, 1):
        copied = json.loads(json.dumps(rows))
        original_value = copied[index].get(key)
        effective = original_value != replacement
        copied[index][key] = replacement
        rejected = bool(verify_rows(copied))
        controls.append({"control": number, "row": index, "field": key, "effective": effective, "rejected": rejected})
    false_retained = sum(len(set(r["local_support"]) - set(r["full_rebuild"])) for r in rows if r["deleted_rule"] is not None)
    false_removed = sum(len(set(r["full_rebuild"]) - set(r["blind_invalidate"])) for r in rows if r["deleted_rule"] is not None)
    candidate_mismatches = sum(r["clear_and_rederive"] != r["full_rebuild"] for r in rows)
    passed = not provenance and not semantic_errors and all(c["effective"] and c["rejected"] for c in controls) and false_retained > 0 and false_removed > 0 and candidate_mismatches == 0 and old_report.get("decision") == "STOP_AUDIT"
    report = {
        "schema": "cyclic-rule-retraction-posthoc-audit-v2",
        "decision": "PASS_POSTHOC_RAW_AUDIT_ONLY" if passed else "STOP_POSTHOC_AUDIT",
        "original_issue_4449_disposition_unchanged": "STOP_AUDIT",
        "rows": len(rows),
        "rows_sha256": sha(rows_bytes),
        "conditions_sha256": sha(conditions_bytes),
        "newline_conditions_sha256": sha(expected_newline),
        "escaped_separator_sha256": sha(expected_escaped),
        "original_frozen_conditions_sha256": original_freeze["formal_conditions_sha256"],
        "candidate_full_mismatch_rows": candidate_mismatches,
        "local_support_false_retained_claims": false_retained,
        "blind_invalidation_false_removed_claims": false_removed,
        "provenance_errors": provenance,
        "semantic_errors": semantic_errors,
        "corruption_controls": controls,
        "controls_rejected": sum(c["rejected"] for c in controls),
    }
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
