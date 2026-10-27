#!/usr/bin/env python3
"""Fixed non-agent scorer for the A02 common-check analogy-memory fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def _base_checks(mapping: dict, target: dict, version: str) -> tuple[dict, str]:
    relation_match = (mapping["proposed_relation"] == target["required_relation"] and
                      mapping["mechanism_edge_present"] is True)
    evidence_current = mapping["evidence_current"] is True
    checks = {"relation_graph_match": relation_match,
              "evidence_current": evidence_current,
              "target_version_bound": bool(version)}
    if not evidence_current:
        return checks, "UNKNOWN"
    if not relation_match:
        return checks, "REJECT"
    return checks, "PASS"


def _retrieve_memory(mapping: dict, memory: list[dict]) -> dict | None:
    return next((entry for entry in memory if entry["family"] == mapping["family"]), None)


def _context_words(mapping: dict, target: dict, version: str,
                   condition: str, item: dict | None) -> list[str]:
    words = ["target", target["target_id"], "version", version, "relation",
             target["required_relation"], "candidate", mapping["candidate_id"],
             "proposal", mapping["proposed_relation"]]
    if item is not None and condition == "prose_memory":
        words.extend(item["prose_note"].split())
    elif item is not None and condition == "structured_memory":
        words.extend([item["record_id"], item["boundary_field"],
                      item["source_value"], item["rejected_target_value"]])
    if len(words) > 64:
        raise ValueError("frozen context exceeds 64 word-units")
    words.extend(f"neutral{i:02d}" for i in range(64 - len(words)))
    return words


def _score(mapping: dict, card: dict, version: str, condition: str,
           fixture: dict, schedule_id: str, condition_order: int,
           candidate_order: int) -> dict:
    target = {"target_id": card["target_id"], "required_relation": card["required_relation"],
              "boundary_field": card["versions"][version]["boundary_field"],
              "boundary_value": card["versions"][version]["value"]}
    checks, base_status = _base_checks(mapping, target, version)
    memory = fixture["rejection_memory"]
    item = None
    if condition in ("prose_memory", "structured_memory"):
        item = _retrieve_memory(mapping, memory)

    query = {"kind": "generic_recheck", "boundary_field": None,
             "current_value": None, "blocked_value": None, "source_value": None}
    if condition == "prose_memory" and item is not None:
        query["kind"] = "untyped_note_recheck"
    elif condition == "structured_memory" and item is not None:
        query = {"kind": "typed_boundary_question", "boundary_field": item["boundary_field"],
                 "current_value": target["boundary_value"],
                 "blocked_value": item["rejected_target_value"],
                 "source_value": item["source_value"]}

    if base_status == "UNKNOWN":
        decision, reason = "UNKNOWN", "COMMON_EVIDENCE_NOT_CURRENT"
    elif base_status == "REJECT":
        decision, reason = "REJECT", "COMMON_RELATION_CHECK_FAILED"
    elif condition == "structured_memory" and item is not None:
        if target["boundary_field"] != item["boundary_field"]:
            decision, reason = "UNKNOWN", "BOUNDARY_FIELD_UNAVAILABLE"
        elif target["boundary_value"] == item["rejected_target_value"]:
            decision, reason = "REJECT", "MEMORY_BOUNDARY_STILL_APPLIES"
        elif target["boundary_value"] == item["source_value"]:
            decision, reason = "PROPOSE", "MEMORY_BOUNDARY_RECHECK_PASSES"
        else:
            decision, reason = "UNKNOWN", "BOUNDARY_VALUE_UNRESOLVED"
    elif condition == "prose_memory" and item is not None:
        decision, reason = "PROPOSE", "UNTYPED_NOTE_HAS_NO_CONSUMABLE_BOUNDARY_QUERY"
    else:
        decision, reason = "PROPOSE", "COMMON_CHECKS_PASS"

    return {
        "row_id": f"{schedule_id}:{condition}:{mapping['candidate_id']}",
        "schedule_id": schedule_id,
        "target_id": card["target_id"],
        "target_version": version,
        "condition": condition,
        "condition_order": condition_order,
        "candidate_order": candidate_order,
        "candidate_id": mapping["candidate_id"],
        "candidate_exposed": True,
        "common_checks": checks,
        "common_status": base_status,
        "lookup_count": 1,
        "lookup_budget": fixture["lookup_budget"],
        "review_slot_count": 1,
        "review_slot_budget": fixture["review_slot_budget"],
        "context_word_count": 64,
        "context_word_budget": fixture["context_word_budget"],
        "scorer_context_words": _context_words(mapping, target, version, condition, item),
        "memory_record_id": item["record_id"] if item else None,
        "lookup_match": item is not None,
        "query": query,
        "decision": decision,
        "reason": reason,
        "automatic_exclusion": False
    }


def run(fixture: dict) -> dict:
    cards = {card["target_id"]: card for card in fixture["target_cards"]}
    mappings = {row["candidate_id"]: row for row in fixture["mappings"]}
    by_target: dict[str, list[dict]] = {}
    for row in fixture["mappings"]:
        by_target.setdefault(row["target_id"], []).append(row)
    schedules, changed_schedules, rows = [], [], []
    for index, card in enumerate(fixture["target_cards"]):
        order = list(fixture["conditions"])
        random.Random(fixture["seed"] + index).shuffle(order)
        schedule_id = f"{card['target_id']}:v1"
        schedules.append({"schedule_id": schedule_id, "condition_order": order,
                          "candidate_order": fixture["candidate_order"]})
        ordered = sorted(by_target[card["target_id"]],
                         key=lambda item: fixture["candidate_order"].index(item["candidate_id"][0]))
        for condition_order, condition in enumerate(order):
            for candidate_order, mapping in enumerate(ordered):
                rows.append(_score(mapping, card, "v1", condition, fixture, schedule_id,
                                   condition_order, candidate_order))
    for index, candidate_id in enumerate(fixture["changed_envelope_controls"]):
        mapping = mappings[candidate_id]
        card = cards[mapping["target_id"]]
        order = list(fixture["conditions"])
        random.Random(fixture["seed"] + 100 + index).shuffle(order)
        schedule_id = f"{card['target_id']}:v2:{candidate_id}"
        changed_schedules.append({"schedule_id": schedule_id, "condition_order": order,
                                  "candidate_order": [candidate_id]})
        for condition_order, condition in enumerate(order):
            rows.append(_score(mapping, card, "v2", condition, fixture, schedule_id,
                               condition_order, 0))
    return {"schema": "analogy-rejection-8500-a02-raw-v1", "seed": fixture["seed"],
            "schedules": schedules, "changed_schedules": changed_schedules, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir)
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    result = run(fixture)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = root / "raw" / "first-outcome" / "candidate.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(result["rows"]),
                      "schedules": len(result["schedules"]),
                      "changed_schedules": len(result["changed_schedules"]),
                      "sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
