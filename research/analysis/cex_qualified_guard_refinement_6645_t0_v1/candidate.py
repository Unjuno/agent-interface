#!/usr/bin/env python3
"""Finite counterexample-qualified guard refinement candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def signature(features: dict[str, bool], vocabulary: list[str]) -> tuple[bool, ...]:
    return tuple(features[name] for name in vocabulary)


def run(fixture: dict[str, Any]) -> dict[str, Any]:
    states = {state["id"]: state for state in fixture["state_inventory"]}
    controls = [states[state_id] for state_id in fixture["independently_verified_control_ids"]]
    vocabulary = fixture["predicate_vocabulary"]
    guard = fixture["original_guard"]
    events: list[dict[str, Any]] = []
    alternatives: list[dict[str, Any]] = []
    ambiguous_signatures: set[tuple[bool, ...]] = set()
    no_refinement_signatures: set[tuple[bool, ...]] = set()
    unavailable_fallback_signature = signature(fixture["fallback"]["unavailable_signature"], vocabulary)

    for counterexample in fixture["counterexamples"]:
        state = states[counterexample["state_id"]]
        class_name = counterexample["classification"]
        terms: list[str] = []
        result = "NO_REFINEMENT_NONREAL"
        if class_name == "REAL_GUARD_MISS" and counterexample["independent_replay"]:
            state_sig = signature(state["features"], vocabulary)
            matching_controls = [
                control for control in controls
                if signature(control["features"], vocabulary) == state_sig
            ]
            if matching_controls:
                ambiguous_signatures.add(state_sig)
                no_refinement_signatures.add(state_sig)
                result = "UNKNOWN_OBSERVATIONAL_ALIAS"
            else:
                for predicate in vocabulary:
                    if all(control["features"][predicate] is True for control in controls) and state["features"][predicate] is False:
                        terms.append(predicate)
                if terms:
                    alternatives.extend(
                        {"counterexample_id": counterexample["id"], "terms": [predicate]}
                        for predicate in sorted(terms)
                    )
                    result = "REFINEMENT_ALTERNATIVES_RETAINED"
                else:
                    no_refinement_signatures.add(state_sig)
                    result = "UNKNOWN_NO_VALID_CONTROL_PRESERVING_TERM"
        events.append({
            "counterexample_id": counterexample["id"],
            "state_id": state["id"],
            "classification_consumed": class_name,
            "result": result,
            "candidate_terms": sorted(terms),
        })

    changed_predicates = sorted({term for alternative in alternatives for term in alternative["terms"]})
    invalidated = sorted(
        cache["id"] for cache in fixture["cache_instances"]
        if cache["active"] and set(cache["depends_on"]).intersection(changed_predicates)
    )
    retained = sorted(
        cache["id"] for cache in fixture["cache_instances"]
        if cache["active"] and cache["id"] not in invalidated
    )

    decisions: dict[str, str] = {}
    for state_id, state in sorted(states.items()):
        if state_id in fixture["out_of_scope_state_ids"]:
            decisions[state_id] = "OUT_OF_SCOPE"
            continue
        state_sig = signature(state["features"], vocabulary)
        if state_sig in ambiguous_signatures or state_sig in no_refinement_signatures:
            decisions[state_id] = "UNKNOWN"
            continue
        if not all(state["features"][name] is True for name in guard):
            decisions[state_id] = (
                "HOLD_NO_SAFE_FALLBACK"
                if state_sig == unavailable_fallback_signature
                else "DEOPT_GENERIC"
            )
            continue
        applicable = []
        for alternative in alternatives:
            terms = alternative["terms"]
            if terms:
                applicable.append(any(state["features"][term] is True for term in terms))
        if not applicable:
            decisions[state_id] = "UNKNOWN"
        elif all(applicable):
            decisions[state_id] = "ADMIT"
        elif not any(applicable):
            decisions[state_id] = "REFUSE_AND_DEOPT"
        else:
            decisions[state_id] = "UNKNOWN_ALTERNATIVE_DISAGREEMENT"

    return {
        "schema": "cex-guard-refinement-raw-v1",
        "allocation_id": fixture["allocation_id"],
        "counterexample_events": events,
        "refinement_alternatives": alternatives,
        "changed_predicates": changed_predicates,
        "cache_invalidation": {"invalidated": invalidated, "retained": retained},
        "decisions": decisions,
        "fallback": {
            "route": fixture["fallback"]["route"],
            "authority_before": fixture["fallback"]["authority_before"],
            "authority_after": fixture["fallback"]["authority_after"],
            "task_input_replays": 0,
        },
        "arms": fixture["arms"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("output")
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(args.output).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": raw["allocation_id"], "counterexample_events": len(raw["counterexample_events"]), "decisions": len(raw["decisions"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
