"""Deterministic inert handoff-card fixture candidate for Issue #8604."""

from __future__ import annotations

FAMILIES = (
    ("F01", "save draft", "document D-17", "not started", "no changes made"),
    ("F02", "submit form", "form F-22", "pending", "no submission recorded"),
    ("F03", "move file", "file X-03", "partial", "one copy may exist"),
    ("F04", "book appointment", "slot S-09", "not started", "no booking recorded"),
    ("F05", "send message", "message M-12", "pending", "delivery not confirmed"),
    ("F06", "update record", "record R-08", "partial", "field A changed; field B pending"),
    ("F07", "export report", "report Q-31", "completed", "export exists; no email sent"),
    ("F08", "close ticket", "ticket T-44", "unknown", "closure state unverified"),
)

BASE_OPTIONS = {
    "stop": ("Stop safely", "No further operation is authorized."),
    "inspect": ("Inspect evidence", "Read-only inspection only; no task effect is authorized."),
    "wait": ("Wait for specified evidence", "No task effect is authorized while waiting."),
    "takeover": ("Take over manually", "The agent dispatches no action; control remains with the user."),
}

CONDITIONS = (("C2", ("stop", "inspect")), ("C3", ("stop", "inspect", "wait")), ("C4", ("stop", "inspect", "wait", "takeover")))


def build_cards():
    cards = []
    for family_id, operation, target, status, evidence in FAMILIES:
        for condition, option_ids in CONDITIONS:
            options = [
                {"id": oid, "label": BASE_OPTIONS[oid][0], "scope": BASE_OPTIONS[oid][1]}
                for oid in option_ids
            ]
            card = {
                "family_id": family_id,
                "condition": condition,
                "operation": operation,
                "target": target,
                "operation_status": status,
                "evidence_statement": evidence,
                "evidence_scope": "This card reports only the facts stated here; no external state was checked.",
                "authority_boundary": "Choosing a disposition in this inert vignette is not authorization to execute an action.",
                "options": options,
            }
            card["comprehension_key"] = [
                {"question_id": "Q1", "question": "Which target is named?", "answer": target, "kind": "fact"},
                {"question_id": "Q2", "question": "What is the operation status?", "answer": status, "kind": "fact"},
                {"question_id": "Q3", "question": "What does the evidence say?", "answer": evidence, "kind": "fact"},
                {"question_id": "Q4", "question": "Does choosing authorize dispatch?", "answer": "No", "kind": "authority_fact"},
                {"question_id": "Q5", "question": "Was external state independently checked?", "answer": "No", "kind": "evidence_scope_fact"},
            ]
            cards.append(card)
    return cards


if __name__ == "__main__":
    import json
    print(json.dumps(build_cards(), ensure_ascii=False, sort_keys=True, indent=2))
