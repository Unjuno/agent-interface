#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #8500 T0 A02."""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import random
from pathlib import Path


def _checks(mapping: dict, card: dict, version: str) -> tuple[dict, str]:
    # Rebuild the common verifier from source facts, independently of candidate output.
    check_a = mapping["proposed_relation"] == card["required_relation"]
    check_b = mapping["mechanism_edge_present"] is True
    check_c = mapping["evidence_current"] is True
    values = {"relation_graph_match": check_a and check_b,
              "evidence_current": check_c,
              "target_version_bound": version in card["versions"]}
    if check_c is False:
        state = "UNKNOWN"
    elif not (check_a and check_b):
        state = "REJECT"
    else:
        state = "PASS"
    return values, state


def _expected_context(mapping: dict, card: dict, version: str,
                      condition: str, memory_item: dict | None) -> list[str]:
    base = ["target", card["target_id"], "version", version, "relation",
            card["required_relation"], "candidate", mapping["candidate_id"],
            "proposal", mapping["proposed_relation"]]
    if memory_item is not None and condition == "prose_memory":
        base.extend(memory_item["prose_note"].split())
    elif memory_item is not None and condition == "structured_memory":
        base.extend([memory_item["record_id"], memory_item["boundary_field"],
                     memory_item["source_value"], memory_item["rejected_target_value"]])
    base.extend(f"neutral{i:02d}" for i in range(64 - len(base)))
    return base


def _memory_for(mapping: dict, condition: str, records: list[dict]) -> tuple[dict | None, bool]:
    if condition == "no_memory":
        return None, 0.0
    selected = next((x for x in records if x["family"] == mapping["family"]), None)
    return selected, selected is not None


def _expected_row(mapping: dict, card: dict, version: str, condition: str,
                  fixture: dict, schedule_id: str, condition_order: int,
                  candidate_order: int) -> dict:
    checks, common_status = _checks(mapping, card, version)
    item, lookup_match = _memory_for(mapping, condition, fixture["rejection_memory"])
    boundary = card["versions"][version]
    query = {"kind": "generic_recheck", "boundary_field": None,
             "current_value": None, "blocked_value": None, "source_value": None}
    if condition == "prose_memory" and item is not None:
        query["kind"] = "untyped_note_recheck"
    elif condition == "structured_memory" and item is not None:
        query = {"kind": "typed_boundary_question", "boundary_field": item["boundary_field"],
                 "current_value": boundary["value"],
                 "blocked_value": item["rejected_target_value"],
                 "source_value": item["source_value"]}
    if common_status == "UNKNOWN":
        decision, reason = "UNKNOWN", "COMMON_EVIDENCE_NOT_CURRENT"
    elif common_status == "REJECT":
        decision, reason = "REJECT", "COMMON_RELATION_CHECK_FAILED"
    elif condition == "structured_memory" and item is not None:
        if boundary["boundary_field"] != item["boundary_field"]:
            decision, reason = "UNKNOWN", "BOUNDARY_FIELD_UNAVAILABLE"
        elif boundary["value"] == item["rejected_target_value"]:
            decision, reason = "REJECT", "MEMORY_BOUNDARY_STILL_APPLIES"
        elif boundary["value"] == item["source_value"]:
            decision, reason = "PROPOSE", "MEMORY_BOUNDARY_RECHECK_PASSES"
        else:
            decision, reason = "UNKNOWN", "BOUNDARY_VALUE_UNRESOLVED"
    elif condition == "prose_memory" and item is not None:
        decision, reason = "PROPOSE", "UNTYPED_NOTE_HAS_NO_CONSUMABLE_BOUNDARY_QUERY"
    else:
        decision, reason = "PROPOSE", "COMMON_CHECKS_PASS"
    return {
        "row_id": f"{schedule_id}:{condition}:{mapping['candidate_id']}",
        "schedule_id": schedule_id, "target_id": card["target_id"],
        "target_version": version, "condition": condition,
        "condition_order": condition_order, "candidate_order": candidate_order,
        "candidate_id": mapping["candidate_id"], "candidate_exposed": True,
        "common_checks": checks, "common_status": common_status,
        "lookup_count": 1, "lookup_budget": fixture["lookup_budget"],
        "review_slot_count": 1, "review_slot_budget": fixture["review_slot_budget"],
        "context_word_count": 64, "context_word_budget": fixture["context_word_budget"],
        "scorer_context_words": _expected_context(mapping, card, version, condition, item),
        "memory_record_id": item["record_id"] if item else None,
        "lookup_match": lookup_match, "query": query,
        "decision": decision, "reason": reason, "automatic_exclusion": False
    }


def reconstruct(fixture: dict) -> dict:
    by_id = {x["candidate_id"]: x for x in fixture["mappings"]}
    by_target: dict[str, list[dict]] = {}
    cards = {x["target_id"]: x for x in fixture["target_cards"]}
    for mapping in fixture["mappings"]:
        by_target.setdefault(mapping["target_id"], []).append(mapping)
    schedules, changed, rows = [], [], []
    for index, card in enumerate(fixture["target_cards"]):
        order = list(fixture["conditions"])
        random.Random(fixture["seed"] + index).shuffle(order)
        schedule_id = f"{card['target_id']}:v1"
        schedules.append({"schedule_id": schedule_id, "condition_order": order,
                          "candidate_order": fixture["candidate_order"]})
        ordered = sorted(by_target[card["target_id"]],
                         key=lambda item: fixture["candidate_order"].index(item["candidate_id"][0]))
        for condition_order, condition in enumerate(order):
            for position, mapping in enumerate(ordered):
                rows.append(_expected_row(mapping, card, "v1", condition, fixture,
                                          schedule_id, condition_order, position))
    for index, candidate_id in enumerate(fixture["changed_envelope_controls"]):
        mapping = by_id[candidate_id]
        card = cards[mapping["target_id"]]
        order = list(fixture["conditions"])
        random.Random(fixture["seed"] + 100 + index).shuffle(order)
        schedule_id = f"{card['target_id']}:v2:{candidate_id}"
        changed.append({"schedule_id": schedule_id, "condition_order": order,
                        "candidate_order": [candidate_id]})
        for condition_order, condition in enumerate(order):
            rows.append(_expected_row(mapping, card, "v2", condition, fixture,
                                      schedule_id, condition_order, 0))
    return {"schema": "analogy-rejection-8500-a02-raw-v1", "seed": fixture["seed"],
            "schedules": schedules, "changed_schedules": changed, "rows": rows}


def inspect(raw: dict, fixture: dict, truth: dict) -> list[str]:
    errors: list[str] = []
    expected = reconstruct(fixture)
    for key in ("schema", "seed", "schedules", "changed_schedules"):
        if raw.get(key) != expected[key]:
            errors.append("raw_" + key)
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected["rows"]):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []
    expected_by_id = {row["row_id"]: row for row in expected["rows"]}
    observed_by_id: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("row_id"), str):
            errors.append("malformed_row")
            continue
        row_id = row["row_id"]
        if row_id in observed_by_id:
            errors.append("duplicate_row")
        observed_by_id[row_id] = row
        want = expected_by_id.get(row_id)
        if want is None:
            errors.append("unexpected_row")
            continue
        if row != want:
            errors.append("row_mismatch_" + row_id)
    if set(observed_by_id) != set(expected_by_id):
        errors.append("row_set")

    # The same fresh target-specific checks must be consumed in all arms.
    grouping: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        if isinstance(row, dict):
            key = (row.get("schedule_id"), row.get("target_version"), row.get("candidate_id"))
            grouping.setdefault(key, []).append(row)
    for group in grouping.values():
        common = {(json.dumps(row.get("common_checks"), sort_keys=True), row.get("common_status"))
                  for row in group}
        if len(common) != 1:
            errors.append("common_check_arm_parity")

    for row in rows:
        if not isinstance(row, dict):
            continue
        context = row.get("scorer_context_words")
        if not isinstance(context, list) or len(context) != 64:
            errors.append("context_word_budget")
            continue
        if row.get("condition") in context:
            errors.append("condition_label_leak")
        if row.get("lookup_count") != 1 or row.get("review_slot_count") != 1:
            errors.append("query_budget")
        if row.get("candidate_exposed") is not True or row.get("automatic_exclusion") is not False:
            errors.append("exposure_or_exclusion")

    # Check the immutable truth key is complete and unique; decisions are summarized separately.
    truth_keys = [(x["candidate_id"], x["target_id"]) for x in truth.get("rows", [])]
    expected_truth_keys = [(m["candidate_id"], m["target_id"]) for m in fixture["mappings"]]
    if len(truth_keys) != len(set(truth_keys)) or set(truth_keys) != set(expected_truth_keys):
        errors.append("truth_key_coverage")
    return errors


def _metrics(raw: dict, fixture: dict, truth: dict) -> dict:
    truths = {(x["candidate_id"], x["target_id"]): x for x in truth["rows"]}
    by_condition = {condition: [r for r in raw["rows"] if r["condition"] == condition]
                    for condition in fixture["conditions"]}
    invalid = {}
    recall = {}
    for condition, rows in by_condition.items():
        invalid[condition] = sum(
            1 for row in rows if row["target_version"] == "v1" and
            not truths[(row["candidate_id"], row["target_id"])]["valid_v1"] and
            row["decision"] == "PROPOSE")
        positives = [row for row in rows if
                     (row["target_version"] == "v1" and
                      truths[(row["candidate_id"], row["target_id"])]["valid_v1"]) or
                     (row["target_version"] == "v2" and
                      truths[(row["candidate_id"], row["target_id"])]["valid_v2"])]
        recall[condition] = {
            "proposed": sum(1 for row in positives if row["decision"] == "PROPOSE"),
            "eligible": len(positives)
        }
    changed_ids = set(fixture["changed_envelope_controls"])
    changed_structured = [r for r in by_condition["structured_memory"]
                          if r["target_version"] == "v2" and r["candidate_id"] in changed_ids]
    changed = {"proposed": sum(1 for r in changed_structured if r["decision"] == "PROPOSE"),
               "eligible": len(changed_ids)}
    return {"invalid_proposals_unchanged_envelope": invalid,
            "valid_candidate_recall": recall,
            "structured_changed_controls": changed}


def _mutations_rejected(raw: dict, fixture: dict, truth: dict) -> tuple[list[dict], list[str]]:
    controls = []

    def trial(name: str, edit) -> None:
        changed = copy.deepcopy(raw)
        edit(changed)
        rejected = bool(inspect(changed, fixture, truth))
        controls.append({"mutation": name, "rejected": rejected})

    trial("drop_row", lambda value: value["rows"].pop())

    def unique_verifier(value):
        row = next(r for r in value["rows"] if r["condition"] == "structured_memory")
        row["common_checks"]["relation_graph_match"] = False
    trial("arm_specific_verifier_access", unique_verifier)

    def suppress_changed_target(value):
        row = next(r for r in value["rows"] if r["target_version"] == "v2" and
                   r["condition"] == "structured_memory")
        row["decision"] = "REJECT"
    trial("changed_envelope_false_reject", suppress_changed_target)

    trial("duplicate_row", lambda value: value["rows"].append(copy.deepcopy(value["rows"][0])))

    def leak_arm_label(value):
        row = next(r for r in value["rows"] if r["condition"] == "prose_memory")
        row["scorer_context_words"][0] = "prose_memory"
    trial("arm_label_leak", leak_arm_label)
    return controls, [x["mutation"] for x in controls if not x["rejected"]]


def audit(raw: dict, fixture: dict, truth: dict) -> dict:
    errors = inspect(raw, fixture, truth)
    metrics = _metrics(raw, fixture, truth)
    mutations, missed = _mutations_rejected(raw, fixture, truth)
    invalid = metrics["invalid_proposals_unchanged_envelope"]
    recall = metrics["valid_candidate_recall"]
    common_parity = "common_check_arm_parity" not in errors
    changed = metrics["structured_changed_controls"]
    if changed["proposed"] != changed["eligible"]:
        disposition = "FAIL_NEGATIVE_SUPPRESSION"
    elif not common_parity:
        disposition = "HOLD_VERIFIER_ACCESS_MISMATCH"
    elif missed:
        disposition = "FAIL_METHOD"
    elif (invalid["structured_memory"] < invalid["no_memory"] and
          invalid["structured_memory"] < invalid["prose_memory"] and
          all(recall["structured_memory"]["proposed"] * recall[condition]["eligible"] >=
              recall[condition]["proposed"] * recall["structured_memory"]["eligible"]
              for condition in fixture["conditions"] if condition != "structured_memory") and
          not errors):
        disposition = "PASS_METHOD_SCOPED"
    elif not errors:
        disposition = "NO_INCREMENTAL_VALUE"
    else:
        disposition = "FAIL_METHOD"
    return {"status": disposition, "errors": errors, "metrics": metrics,
            "reconstructed_rows": len(raw.get("rows", [])),
            "mutation_controls": mutations,
            "mutations_rejected": len(mutations) - len(missed),
            "candidate_raw_sha256": hashlib.sha256(
                json.dumps(raw, sort_keys=True, indent=2).encode() + b"\n").hexdigest(),
            "scope": "finite authored scorer; no human or open-literature inference"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir)
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    truth = json.loads((root / "truth.json").read_text(encoding="utf-8"))
    raw_path = root / "raw" / "first-outcome" / "candidate.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    result = audit(raw, fixture, truth)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = root / "raw" / "first-outcome" / "audit.json"
    output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": len(result["errors"]),
                      "mutations_rejected": result["mutations_rejected"],
                      "audit_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))
    return 0 if result["status"] in ("PASS_METHOD_SCOPED", "NO_INCREMENTAL_VALUE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
