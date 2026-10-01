#!/usr/bin/env python3
"""Raw-only auditor; intentionally does not import study.py."""
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


def digest(data):
    return hashlib.sha256(data).hexdigest()


def oracle(active):
    interpretations = []
    for bits in itertools.product((False, True), repeat=len(CLAIMS)):
        candidate = {c for c, bit in zip(CLAIMS, bits) if bit}
        known = ROOTS | candidate
        if all(head in known for _, head, body in active if set(body) <= known):
            interpretations.append(candidate)
    return set.intersection(*interpretations) if interpretations else set()


def expected_cone(deleted, active):
    cone = {deleted[1]}
    while True:
        expanded = cone | {
            head for _, head, body in active if set(body) & cone
        }
        if expanded == cone:
            return cone
        cone = expanded


def expected_rows():
    for mask in range(64):
        before_active = tuple(r for i, r in enumerate(RULES) if mask & (1 << i))
        before = oracle(before_active)
        yield mask, None, before_active, before, set(), before_active, before
        for i, deleted in enumerate(RULES):
            if not mask & (1 << i):
                continue
            after = tuple(r for r in before_active if r[0] != deleted[0])
            yield mask, deleted[0], before_active, before, expected_cone(deleted, after), after, oracle(after)


def expected_row_tuple(spec):
    mask, deleted_id, before_active, before, cone, active, truth = spec
    if deleted_id is None:
        local = blind = set(before)
    else:
        local = set(before) | ROOTS
        while True:
            remove = {
                claim for claim in CLAIMS
                if claim in local and not any(
                    head == claim and set(body) <= local for _, head, body in active
                )
            }
            if not remove:
                break
            local -= remove
        local &= set(CLAIMS)
        blind = set(before) - set(cone)
    return {
        "mask": mask,
        "deleted_rule": deleted_id,
        "active_rules_before": [r[0] for r in before_active],
        "active_rules_after": [r[0] for r in active],
        "before": sorted(before),
        "affected_cone": sorted(cone),
        "clear_and_rederive": sorted(truth),
        "full_rebuild": sorted(truth),
        "local_support": sorted(local),
        "blind_invalidate": sorted(blind),
    }


def verify(raw_rows, phase="formal"):
    errors = []
    specs = list(expected_rows())
    if phase == "construction":
        specs = [s for s in specs if s[0] in {1, 11, 19}]
    expected_count = 256 if phase == "formal" else 10
    if len(raw_rows) != expected_count:
        errors.append(f"row_count:{len(raw_rows)}")
    if len(specs) != len(raw_rows):
        return [*errors, "oracle_denominator_mismatch"]
    local_false_retain = 0
    blind_false_remove = 0
    for index, (row, spec) in enumerate(zip(raw_rows, specs)):
        expected = expected_row_tuple(spec)
        for key, value in expected.items():
            if row.get(key) != value:
                errors.append(f"row{index}:{key}")
        mask, deleted_id, before_active, before, cone, active, truth = spec
        local = set(row.get("local_support", []))
        blind = set(row.get("blind_invalidate", []))
        if deleted_id is None:
            if set(row.get("local_support", [])) != before or set(row.get("blind_invalidate", [])) != before:
                errors.append(f"row{index}:no_change")
        else:
            if not set(truth) <= set(before):
                errors.append(f"row{index}:adds_grounded_claim")
            if any((claim in before) != (claim in truth) for claim in set(CLAIMS) - set(cone)):
                errors.append(f"row{index}:outside_cone_changed")
            if local != set(truth):
                local_false_retain += len(local - set(truth))
            if blind != set(truth):
                blind_false_remove += len(set(truth) - blind)
    if phase == "formal" and local_false_retain == 0:
        errors.append("local_support_counterexample_missing")
    if phase == "formal" and blind_false_remove == 0:
        errors.append("blind_invalidation_counterexample_missing")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--phase", choices=("construction", "formal"), required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    root = Path(args.run)
    raw_path = root / "rows.jsonl"
    raw = raw_path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    errors = verify(rows, args.phase)
    provenance_errors = []
    study_root = Path(__file__).resolve().parent
    freeze_path = study_root / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
    if args.phase == "formal":
        for relpath, expected_hash in freeze["source_sha256"].items():
            if digest((study_root / relpath).read_bytes()) != expected_hash:
                provenance_errors.append(f"source_hash:{relpath}")
    process = json.loads((root / "process.json").read_text())
    input_bytes = (root / "input.json").read_bytes()
    conditions_bytes = (root / "conditions.jsonl").read_bytes()
    expected_count = 256 if args.phase == "formal" else 10
    expected_input = {
        "roots": sorted(ROOTS),
        "claims": list(CLAIMS),
        "rules": [{"id": rid, "head": head, "body": list(body)} for rid, head, body in RULES],
        "expected_conditions": expected_count,
    }
    canonical_input = (json.dumps(expected_input, sort_keys=True, indent=2) + "\n").encode()
    if input_bytes != canonical_input:
        provenance_errors.append("input_content")
    if process.get("phase") != args.phase or process.get("exit_code") != 0 or process.get("rows") != expected_count:
        provenance_errors.append("process_identity")
    if args.phase == "formal" and process.get("python", "").split()[0] != freeze["container"]["python"]:
        provenance_errors.append("python_identity")
    if args.phase == "formal" and process.get("machine") != "aarch64":
        provenance_errors.append("machine_identity")
    if process.get("rows_sha256") != digest(raw):
        provenance_errors.append("rows_digest")
    if process.get("input_sha256") != digest(input_bytes):
        provenance_errors.append("input_digest")
    if process.get("conditions_sha256") != digest(conditions_bytes):
        provenance_errors.append("conditions_digest")
    condition_specs = list(expected_rows())
    if args.phase == "construction":
        condition_specs = [s for s in condition_specs if s[0] in {1, 11, 19}]
    expected_conditions = "".join(
        json.dumps({"mask": spec[0], "deleted_rule": spec[1]}, sort_keys=True, separators=(",", ":")) + "\n"
        for spec in condition_specs
    ).encode()
    if conditions_bytes != expected_conditions:
        provenance_errors.append("conditions_content")
    if args.phase == "formal" and process.get("study_sha256") != freeze["source_sha256"].get("study.py"):
        provenance_errors.append("executed_study_hash")
    if args.phase == "formal" and freeze.get("formal_conditions_sha256") != digest(expected_conditions):
        provenance_errors.append("frozen_conditions_hash")
    if args.phase == "construction" and conditions_bytes != expected_conditions:
        provenance_errors.append("construction_conditions_content")
    controls = []
    mutations = [
        lambda r: r[0].__setitem__("mask", 63),
        lambda r: r[0].__setitem__("deleted_rule", "r5"),
        lambda r: r[0].__setitem__("active_rules_before", []),
        lambda r: r[0].__setitem__("active_rules_after", []),
        lambda r: r[0].__setitem__("before", []),
        lambda r: r[3].__setitem__("affected_cone", []),
        lambda r: r[0].__setitem__("clear_and_rederive", []),
        lambda r: r[0].__setitem__("full_rebuild", []),
        lambda r: r[0].__setitem__("local_support", []),
        lambda r: r[0].__setitem__("blind_invalidate", []),
    ]
    for index, mutate in enumerate(mutations, 1):
        copied = json.loads(json.dumps(rows))
        mutate(copied)
        rejected = bool(verify(copied, args.phase))
        controls.append({"control": index, "rejected": rejected})
    report = {
        "schema": "cyclic-rule-retraction-audit-v1",
        "rows": len(rows),
        "rows_sha256": digest(raw),
        "errors": errors,
        "provenance_errors": provenance_errors,
        "corruption_controls": controls,
        "controls_rejected": sum(c["rejected"] for c in controls),
        "decision": ("PASS_CONSTRUCTION" if args.phase == "construction" else "PASS_CYCLIC_RULE_RETRACTION_SCOPED") if not errors and not provenance_errors and all(c["rejected"] for c in controls) else "STOP_AUDIT",
    }
    report_path = Path(args.report) if args.report else root / "audit.json"
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["decision"].startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
