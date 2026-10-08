"""Independent exhaustive invariant and key auditor; does not import candidate."""

from __future__ import annotations

EXPECTED = {
    "F01": ("save draft", "document D-17", "not started", "no changes made"),
    "F02": ("submit form", "form F-22", "pending", "no submission recorded"),
    "F03": ("move file", "file X-03", "partial", "one copy may exist"),
    "F04": ("book appointment", "slot S-09", "not started", "no booking recorded"),
    "F05": ("send message", "message M-12", "pending", "delivery not confirmed"),
    "F06": ("update record", "record R-08", "partial", "field A changed; field B pending"),
    "F07": ("export report", "report Q-31", "completed", "export exists; no email sent"),
    "F08": ("close ticket", "ticket T-44", "unknown", "closure state unverified"),
}
EXPECTED_OPTIONS = {"C2": ("stop", "inspect"), "C3": ("stop", "inspect", "wait"), "C4": ("stop", "inspect", "wait", "takeover")}
AUTHORITY = "Choosing a disposition in this inert vignette is not authorization to execute an action."
EVIDENCE_SCOPE = "This card reports only the facts stated here; no external state was checked."
OPTION_SCOPES = {
    "stop": ("Stop safely", "No further operation is authorized."),
    "inspect": ("Inspect evidence", "Read-only inspection only; no task effect is authorized."),
    "wait": ("Wait for specified evidence", "No task effect is authorized while waiting."),
    "takeover": ("Take over manually", "The agent dispatches no action; control remains with the user."),
}


def audit(cards):
    errors = []
    seen = set()
    if not isinstance(cards, list) or len(cards) != 24:
        return ["card_denominator"]
    for i, card in enumerate(cards):
        where = f"card[{i}]"
        if not isinstance(card, dict):
            errors.append(f"{where}:not_object")
            continue
        family = card.get("family_id")
        condition = card.get("condition")
        key = (family, condition)
        if family not in EXPECTED or condition not in EXPECTED_OPTIONS or key in seen:
            errors.append(f"{where}:identity")
            continue
        seen.add(key)
        operation, target, status, evidence = EXPECTED[family]
        fixed = {
            "operation": operation,
            "target": target,
            "operation_status": status,
            "evidence_statement": evidence,
            "evidence_scope": EVIDENCE_SCOPE,
            "authority_boundary": AUTHORITY,
        }
        for field, expected in fixed.items():
            if card.get(field) != expected:
                errors.append(f"{where}:{field}")
        options = card.get("options")
        if not isinstance(options, list) or tuple(o.get("id") for o in options if isinstance(o, dict)) != EXPECTED_OPTIONS[condition]:
            errors.append(f"{where}:option_set")
            options = []
        for option in options:
            if not isinstance(option, dict) or OPTION_SCOPES.get(option.get("id")) != (option.get("label"), option.get("scope")):
                errors.append(f"{where}:option_semantics")
        keys = card.get("comprehension_key")
        expected_keys = [
            ("Q1", target, "fact"),
            ("Q2", status, "fact"),
            ("Q3", evidence, "fact"),
            ("Q4", "No", "authority_fact"),
            ("Q5", "No", "evidence_scope_fact"),
        ]
        actual_keys = [(x.get("question_id"), x.get("answer"), x.get("kind")) for x in keys if isinstance(x, dict)] if isinstance(keys, list) else []
        if actual_keys != expected_keys or len(keys) != 5:
            errors.append(f"{where}:comprehension_key")
        if any(x.get("kind") not in {"fact", "authority_fact", "evidence_scope_fact"} for x in keys if isinstance(x, dict)) if isinstance(keys, list) else True:
            errors.append(f"{where}:preference_or_unknown_key")
    if len(seen) != 24:
        errors.append("family_condition_coverage")
    return errors


if __name__ == "__main__":
    import json
    from pathlib import Path
    data = json.loads(Path(__file__).with_name("cards.json").read_text(encoding="utf-8"))
    errs = audit(data)
    print(json.dumps({"audit_integrity": "PASS" if not errs else "FAIL", "errors": errs, "cards": len(data)}, sort_keys=True))
    raise SystemExit(0 if not errs else 1)
