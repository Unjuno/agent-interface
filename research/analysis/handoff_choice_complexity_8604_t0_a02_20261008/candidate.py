"""Candidate CLI for the inert handoff-card fixture; writes output exclusively."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

OPTIONS = {
    "stop": ("Stop safely", "No further operation is authorized."),
    "inspect": ("Inspect evidence", "Read-only inspection only; no task effect is authorized."),
    "wait": ("Wait for specified evidence", "No task effect is authorized while waiting."),
    "takeover": ("Take over manually", "The agent dispatches no action; control remains with the user."),
}
CONDITIONS = (("C2", ("stop", "inspect")), ("C3", ("stop", "inspect", "wait")), ("C4", ("stop", "inspect", "wait", "takeover")))


def build_cards(spec):
    if not isinstance(spec, dict) or not isinstance(spec.get("families"), list) or not spec["families"]:
        raise ValueError("spec requires a non-empty families list")
    cards = []
    seen = set()
    for family in spec["families"]:
        required = ("id", "operation", "target", "status", "evidence")
        if not isinstance(family, dict) or any(not isinstance(family.get(k), str) or not family[k] for k in required):
            raise ValueError("each family requires non-empty id/operation/target/status/evidence strings")
        if family["id"] in seen:
            raise ValueError("duplicate family id")
        seen.add(family["id"])
        for condition, option_ids in CONDITIONS:
            cards.append({
                "family_id": family["id"],
                "condition": condition,
                "operation": family["operation"],
                "target": family["target"],
                "operation_status": family["status"],
                "evidence_statement": family["evidence"],
                "evidence_scope": "This card reports only the facts stated here; no external state was checked.",
                "authority_boundary": "Choosing a disposition in this inert vignette is not authorization to execute an action.",
                "options": [{"id": oid, "label": OPTIONS[oid][0], "scope": OPTIONS[oid][1]} for oid in option_ids],
                "comprehension_key": [
                    {"question_id": "Q1", "question": "Which target is named?", "answer": family["target"], "kind": "fact"},
                    {"question_id": "Q2", "question": "What is the operation status?", "answer": family["status"], "kind": "fact"},
                    {"question_id": "Q3", "question": "What does the evidence say?", "answer": family["evidence"], "kind": "fact"},
                    {"question_id": "Q4", "question": "Does choosing authorize dispatch?", "answer": "No", "kind": "authority_fact"},
                    {"question_id": "Q5", "question": "Was external state independently checked?", "answer": "No", "kind": "evidence_scope_fact"},
                ],
            })
    return cards


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    cards = build_cards(spec)
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(cards, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(f"CANDIDATE_COMPLETE cards={len(cards)}")


if __name__ == "__main__":
    main()
