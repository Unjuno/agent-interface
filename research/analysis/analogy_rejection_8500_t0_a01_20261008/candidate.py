"""Deterministic, non-agent scorer for Issue #8500's finite T0 fixture."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


BASELINE_THRESHOLD = 0.80
PROSE_OVERLAP_THRESHOLD = 0.34
ARMS = ("no_memory", "prose", "structured")


def _jaccard(left: list[str], right: list[str]) -> float:
    a, b = set(left), set(right)
    return len(a & b) / len(a | b) if a | b else 0.0


def _retrieve_prose(candidate: dict, memory: list[dict]) -> tuple[dict | None, float]:
    ranked = [(_jaccard(candidate["query_terms"], item["prose_terms"]), item)
              for item in memory]
    if not ranked:
        return None, 0.0
    score, item = max(ranked, key=lambda pair: (pair[0], pair[1]["counterexample_id"]))
    return (item, score) if score >= PROSE_OVERLAP_THRESHOLD else (None, score)


def score_candidate(candidate: dict, target: dict, condition: str,
                    memory: list[dict]) -> dict:
    """Score one candidate; memory can prompt a fresh check, never auto-exclude."""
    if condition not in ARMS:
        raise ValueError(f"unknown condition: {condition}")

    memory_item = None
    retrieval_score = 0.0
    if condition == "prose":
        memory_item, retrieval_score = _retrieve_prose(candidate, memory)
    elif condition == "structured":
        memory_item = next((item for item in memory
                            if ((candidate.get("counterexample_id") is not None and
                                 item.get("counterexample_id") == candidate["counterexample_id"]) or
                                (candidate.get("counterexample_id") is None and
                                 item.get("relation_family") == candidate.get("relation_family")))), None)

    relation_valid = candidate.get("relation_valid")
    boundary_matches = candidate.get("boundary_matches")
    fresh_check = False
    if condition == "structured" and memory_item is not None:
        fresh_check = True
        if relation_valid is None:
            decision, reason = "UNKNOWN", "FRESH_CHECK_EVIDENCE_MISSING"
        elif relation_valid is False:
            decision, reason = "REJECT", "APPLICABLE_COUNTEREXAMPLE_FRESH_CHECK_FAILED"
        elif boundary_matches is False:
            decision, reason = "PROPOSE", "BOUNDARY_NO_LONGER_APPLIES_FRESH_CHECK_PASSED"
        else:
            decision, reason = "PROPOSE", "BOUNDARY_RECHECK_FRESH_CHECK_PASSED"
    elif condition == "prose" and memory_item is not None:
        decision, reason = "UNKNOWN", "PROSE_NOTE_PROMPTS_RECHECK"
    elif candidate["lexical_similarity"] >= BASELINE_THRESHOLD:
        decision, reason = "PROPOSE", "LEXICAL_BASELINE_ABOVE_THRESHOLD"
    else:
        decision, reason = "UNKNOWN", "LEXICAL_BASELINE_BELOW_THRESHOLD"

    return {
        "decision": decision,
        "reason": reason,
        "retrieved_counterexample_id": memory_item["counterexample_id"] if memory_item else None,
        "retrieval_score": round(retrieval_score, 8),
        "fresh_check_performed": fresh_check,
        "automatic_exclusion": False,
        "boundary_matches": boundary_matches if fresh_check else None,
    }


def _context_words(candidate: dict, target: dict, condition: str,
                   memory_item: dict | None) -> list[str]:
    words = ["target", target["target_id"], "candidate", candidate["candidate_id"],
             "relation", candidate["relation_family"]]
    words.extend(candidate["query_terms"])
    if memory_item is not None:
        if condition == "prose":
            words.extend(memory_item["prose_terms"])
        elif condition == "structured":
            words.extend([memory_item["counterexample_id"], memory_item["boundary_field"],
                          memory_item["source_value"], memory_item["rejected_target_value"]])
    if len(words) > 64:
        raise ValueError("fixture exceeds frozen 64-word-unit context budget")
    words.extend(f"neutral{i:02d}" for i in range(64 - len(words)))
    return words


def _score_one(mapping: dict, target: dict, version: str, condition: str,
               fixture: dict, block_id: str, condition_order: int,
               candidate_order: int) -> dict:
    target_value = target["requirements"][mapping["boundary_field"]]
    relation_valid = (mapping["source_value"] == target_value and
                      mapping["mechanism_edge_present"] is True)
    memory = fixture["rejection_memory"]
    memory_item = None
    retrieval_score = 0.0
    if condition == "structured":
        memory_item = next((m for m in memory
                            if m["relation_family"] == mapping["relation_family"]), None)
    elif condition == "prose":
        memory_item, retrieval_score = _retrieve_prose(mapping, memory)
    boundary_matches = bool(
        memory_item is not None and
        target_value == memory_item["rejected_target_value"] and
        mapping["source_value"] == memory_item["source_value"]
    )
    scorer_candidate = dict(mapping)
    scorer_candidate["relation_valid"] = relation_valid
    scorer_candidate["boundary_matches"] = boundary_matches
    scored = score_candidate(scorer_candidate, target, condition, memory)
    if condition == "prose":
        # The prose arm sees only the selected note; ranking is performed once.
        scored["retrieved_counterexample_id"] = memory_item["counterexample_id"] if memory_item else None
        scored["retrieval_score"] = round(retrieval_score, 8)
    context_memory = memory_item if condition != "no_memory" else None
    return {
        "row_id": f"{block_id}:{condition}:{mapping['candidate_id']}",
        "block_id": block_id,
        "target_id": target["target_id"],
        "target_version": version,
        "condition": condition,
        "condition_order": condition_order,
        "candidate_order": candidate_order,
        "candidate_id": mapping["candidate_id"],
        "candidate_exposed": True,
        "lookup_count": 1,
        "lookup_budget": fixture["lookup_budget"],
        "context_word_count": 64,
        "context_word_budget": fixture["context_word_budget"],
        "scorer_context_words": _context_words(mapping, target, condition, context_memory),
        **scored,
    }


def run(fixture: dict) -> dict:
    target_by_id = {t["target_id"]: t for t in fixture["target_cards"]}
    mappings_by_target: dict[str, list[dict]] = {}
    mapping_by_id = {m["candidate_id"]: m for m in fixture["mappings"]}
    for mapping in fixture["mappings"]:
        mappings_by_target.setdefault(mapping["target_id"], []).append(mapping)

    rows = []
    schedules = []
    for index, card in enumerate(fixture["target_cards"]):
        target_id = card["target_id"]
        arm_order = list(fixture["conditions"])
        random.Random(fixture["seed"] + index).shuffle(arm_order)
        schedules.append({"block_id": f"{target_id}:v1", "condition_order": arm_order})
        target = {"target_id": target_id, "version": "v1",
                  "requirements": card["versions"]["v1"]}
        candidates = mappings_by_target[target_id]
        for condition_order, condition in enumerate(arm_order):
            for candidate_order, mapping in enumerate(candidates):
                rows.append(_score_one(mapping, target, "v1", condition, fixture,
                                       f"{target_id}:v1", condition_order, candidate_order))

    change_schedules = []
    for index, candidate_id in enumerate(fixture["change_controls"]):
        mapping = mapping_by_id[candidate_id]
        card = target_by_id[mapping["target_id"]]
        target = {"target_id": mapping["target_id"], "version": "v2",
                  "requirements": card["versions"]["v2"]}
        arm_order = list(fixture["conditions"])
        random.Random(fixture["seed"] + 100 + index).shuffle(arm_order)
        block_id = f"{target['target_id']}:v2"
        change_schedules.append({"block_id": block_id, "condition_order": arm_order,
                                 "candidate_id": candidate_id})
        for condition_order, condition in enumerate(arm_order):
            rows.append(_score_one(mapping, target, "v2", condition, fixture, block_id,
                                   condition_order, 0))
    return {"schema": "analogy-rejection-t0-a01-raw-v1", "seed": fixture["seed"],
            "schedules": schedules, "change_schedules": change_schedules, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir)
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    result = run(fixture)
    (root / "candidate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")
    print(f"CANDIDATE_COMPLETE rows={len(result['rows'])} blocks="
          f"{len(result['schedules']) + len(result['change_schedules'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
