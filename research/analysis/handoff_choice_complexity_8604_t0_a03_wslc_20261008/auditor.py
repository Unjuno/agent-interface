"""Independent fixed-contract card and factual-key auditor; does not import candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CONDITIONS = {"C2": ("stop", "inspect"), "C3": ("stop", "inspect", "wait"), "C4": ("stop", "inspect", "wait", "takeover")}
OPTIONS = {
    "stop": ("Stop safely", "No further operation is authorized."),
    "inspect": ("Inspect evidence", "Read-only inspection only; no task effect is authorized."),
    "wait": ("Wait for specified evidence", "No task effect is authorized while waiting."),
    "takeover": ("Take over manually", "The agent dispatches no action; control remains with the user."),
}
SCOPE = "This card reports only the facts stated here; no external state was checked."
AUTHORITY = "Choosing a disposition in this inert vignette is not authorization to execute an action."


def audit(spec, cards):
    errors = []
    families = spec.get("families") if isinstance(spec, dict) else None
    if not isinstance(families, list) or not isinstance(cards, list) or len(cards) != 3 * len(families):
        return ["card_denominator"]
    expected = {f.get("id"): f for f in families if isinstance(f, dict)}
    if len(expected) != len(families):
        return ["spec_family_identity"]
    seen = set()
    for i, card in enumerate(cards):
        prefix = f"card[{i}]"
        if not isinstance(card, dict):
            errors.append(prefix + ":not_object")
            continue
        fid, condition = card.get("family_id"), card.get("condition")
        family = expected.get(fid)
        if family is None or condition not in CONDITIONS or (fid, condition) in seen:
            errors.append(prefix + ":identity")
            continue
        seen.add((fid, condition))
        expected_fields = {
            "operation": family.get("operation"),
            "target": family.get("target"),
            "operation_status": family.get("status"),
            "evidence_statement": family.get("evidence"),
            "evidence_scope": SCOPE,
            "authority_boundary": AUTHORITY,
        }
        for field, value in expected_fields.items():
            if card.get(field) != value:
                errors.append(prefix + ":" + field)
        options = card.get("options")
        if not isinstance(options, list) or [o.get("id") for o in options if isinstance(o, dict)] != list(CONDITIONS[condition]):
            errors.append(prefix + ":option_set")
            options = []
        for option in options:
            if not isinstance(option, dict) or OPTIONS.get(option.get("id")) != (option.get("label"), option.get("scope")):
                errors.append(prefix + ":option_semantics")
        expected_key = [
            ("Q1", family.get("target"), "fact"),
            ("Q2", family.get("status"), "fact"),
            ("Q3", family.get("evidence"), "fact"),
            ("Q4", "No", "authority_fact"),
            ("Q5", "No", "evidence_scope_fact"),
        ]
        key = card.get("comprehension_key")
        actual_key = [(q.get("question_id"), q.get("answer"), q.get("kind")) for q in key if isinstance(q, dict)] if isinstance(key, list) else []
        if actual_key != expected_key or not isinstance(key, list) or len(key) != 5:
            errors.append(prefix + ":comprehension_key")
        if isinstance(key, list) and any(q.get("kind") not in {"fact", "authority_fact", "evidence_scope_fact"} for q in key if isinstance(q, dict)):
            errors.append(prefix + ":non_factual_key")
    wanted = {(fid, condition) for fid in expected for condition in CONDITIONS}
    if seen != wanted:
        errors.append("family_condition_coverage")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    cards = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    errors = audit(spec, cards)
    result = {"schema": "8604-audit-v1", "audit_integrity": "PASS" if not errors else "FAIL", "errors": errors, "cards_reconstructed": len(cards) if isinstance(cards, list) else 0, "families": len(spec.get("families", [])) if isinstance(spec, dict) else 0, "comprehension_keys": sum(len(c.get("comprehension_key", [])) for c in cards if isinstance(c, dict)) if isinstance(cards, list) else 0}
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print("AUDIT_COMPLETE " + result["audit_integrity"] + f" errors={len(errors)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
