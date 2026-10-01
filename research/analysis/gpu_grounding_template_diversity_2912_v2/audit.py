#!/usr/bin/env python3
"""Independent structural and decision audit for Issue #4561."""
from __future__ import annotations

import copy
import argparse
import hashlib
import json
from pathlib import Path

from render import FAMILIES, source_family_sha256


SEEDS = [456101, 456102, 456103]
ARMS = ["narrow_2_families", "broad_8_families"]
FROZEN_UPDATES = 400
ACCEPT_MIN = 0.75
EXPECTED_CASES = 16 * len(SEEDS) * len(ARMS)


def _is_cell(value):
    return (isinstance(value, list) and len(value) == 2 and
            all(type(x) is int for x in value) and 0 <= value[0] < 8 and 0 <= value[1] < 10)


def audit_data(raw):
    errors = []
    if raw.get("schema") != "issue4561-template-diversity-formal-v1":
        errors.append("schema mismatch")
    split = raw.get("split", {})
    train, heldout, narrow = split.get("train_families"), split.get("heldout_families"), split.get("narrow_families")
    expected_ids = [f["id"] for f in FAMILIES]
    if train != expected_ids[:8] or heldout != expected_ids[8:] or narrow != expected_ids[:2]:
        errors.append("frozen whole-family split mismatch")
    if set(train or []) & set(heldout or []):
        errors.append("family leakage across split")
    declared_families = raw.get("renderer", {}).get("families", [])
    expected_family_hashes = {f["id"]: source_family_sha256(f) for f in FAMILIES}
    if {f.get("family_id"): f.get("family_sha256") for f in declared_families} != expected_family_hashes:
        errors.append("source family manifest/hash mismatch")

    matrix = raw.get("matrix", {})
    if (matrix.get("seed") != SEEDS or matrix.get("arms") != ARMS or
            matrix.get("updates_per_arm") != FROZEN_UPDATES or matrix.get("batch") != 16 or
            matrix.get("accept_min") != ACCEPT_MIN):
        errors.append("frozen training matrix mismatch")
    metadata = raw.get("metadata", [])
    expected_pairs = {(seed, arm) for seed in SEEDS for arm in ARMS}
    actual_pairs = {(m.get("seed"), m.get("arm")) for m in metadata}
    if actual_pairs != expected_pairs or len(metadata) != 6:
        errors.append("metadata seed/arm cardinality mismatch")
    if any(m.get("steps") != FROZEN_UPDATES or m.get("train_family_ids") !=
           (narrow if m.get("arm") == ARMS[0] else train) for m in metadata):
        errors.append("optimizer step or training-family accounting mismatch")

    cases = raw.get("cases", [])
    if len(cases) != EXPECTED_CASES:
        errors.append("held-out case count mismatch")
    case_keys = set()
    per_family = {}
    accepted_wrong = 0
    for row in cases:
        key = (row.get("seed"), row.get("arm"), row.get("image_id"))
        if key in case_keys:
            errors.append("duplicate evaluation case")
        case_keys.add(key)
        if row.get("seed") not in SEEDS or row.get("arm") not in ARMS or row.get("family_id") not in heldout:
            errors.append("case outside frozen evaluation population")
        pred, target = row.get("predicted_cells"), row.get("target_cells")
        if (not isinstance(pred, list) or len(pred) != 2 or not all(_is_cell(x) for x in pred) or
                not isinstance(target, list) or len(target) != 2 or not all(_is_cell(x) for x in target)):
            errors.append("invalid target/prediction cell")
            continue
        correct = pred == target
        if row.get("exact_pair_correct") is not correct:
            errors.append("exact coordinate correctness field inconsistent")
        confidence = row.get("confidence")
        if (not isinstance(confidence, list) or len(confidence) != 2 or
                any(type(x) not in (float, int) or not 0 <= x <= 1 for x in confidence)):
            errors.append("confidence vector malformed")
            continue
        accepted = min(confidence) >= ACCEPT_MIN
        if row.get("accepted") is not accepted:
            errors.append("accept/YIELD route inconsistent with frozen threshold")
        if accepted and (row.get("candidate_valid") is not True or not isinstance(row.get("parsed_candidate"), dict)):
            errors.append("accepted candidate missing strict-validator evidence")
        if not accepted and (row.get("candidate_valid") is not False or row.get("parsed_candidate") is not None):
            errors.append("yielded case improperly emitted candidate")
        wrong = accepted and not correct
        if row.get("accepted_wrong") is not wrong:
            errors.append("accepted-wrong-coordinate field inconsistent")
        accepted_wrong += int(wrong)
        if row.get("family_id") in heldout:
            per_family.setdefault((row.get("arm"), row.get("family_id")), []).append(correct)

    broad_family = {}
    for family in heldout or []:
        vals = per_family.get((ARMS[1], family), [])
        broad_family[family] = (sum(vals) / len(vals)) if vals else 0.0
        if len(vals) != len(SEEDS) * 4:
            errors.append(f"held-out family case cardinality mismatch: {family}")
    narrow_values = [r.get("exact_pair_correct") is True for r in cases if r.get("arm") == ARMS[0]]
    broad_values = [r.get("exact_pair_correct") is True for r in cases if r.get("arm") == ARMS[1]]
    narrow_acc = sum(narrow_values) / len(narrow_values) if narrow_values else 0.0
    broad_acc = sum(broad_values) / len(broad_values) if broad_values else 0.0
    if accepted_wrong:
        errors.append("one or more accepted wrong coordinates")
    pass_gate = (not errors and all(v >= 0.90 for v in broad_family.values()) and
                 broad_acc - narrow_acc >= 0.10 and accepted_wrong == 0)
    if not errors:
        status = "PASS_TEMPLATE_DIVERSITY_SCOPED" if pass_gate else "HOLD_OR_FAIL_FROZEN_GATES_NOT_MET"
    else:
        status = "FAIL_AUDIT_INTEGRITY"
    return {"status": status, "errors": errors, "broad_accuracy_by_heldout_family": broad_family,
            "narrow_aggregate_accuracy": narrow_acc, "broad_aggregate_accuracy": broad_acc,
            "absolute_delta": broad_acc - narrow_acc, "accepted_wrong_coordinates": accepted_wrong,
            "cases_checked": len(cases)}


def audit_file(path):
    return audit_data(json.loads(Path(path).read_text(encoding="utf-8")))


def mutation_controls(raw):
    mutations = {
        "family_leak": lambda x: x["split"]["heldout_families"].__setitem__(0, x["split"]["train_families"][0]),
        "alter_step_count": lambda x: x["metadata"][0].__setitem__("steps", 399),
        "accept_wrong": lambda x: x["cases"][0].__setitem__("accepted_wrong", True),
        "duplicate_case": lambda x: x["cases"].append(copy.deepcopy(x["cases"][0])),
        "extra_family": lambda x: x["renderer"]["families"].append({"family_id": "extra", "family_sha256": "0" * 64}),
        "wrong_threshold": lambda x: x["matrix"].__setitem__("accept_min", 0.5),
        "out_of_grid": lambda x: x["cases"][0]["predicted_cells"].__setitem__(0, [8, 10]),
    }
    outcomes = {}
    for name, mutate in mutations.items():
        altered = copy.deepcopy(raw)
        mutate(altered)
        outcomes[name] = bool(audit_data(altered)["errors"])
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="formal results.json")
    parser.add_argument("--output", type=Path, help="optional audit JSON destination")
    args = parser.parse_args()
    result = audit_file(args.results)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "PASS_TEMPLATE_DIVERSITY_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
