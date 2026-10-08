"""Independent raw-only reconstruction for Issue #6471; deliberately no candidate import."""
import json
from pathlib import Path

ROOT = Path(__file__).parent


def _contract(speech_act, effect, target, recipient, bound, forbidden, ambiguity=None):
    result = {"speech_act": speech_act, "effect": effect, "target": target,
              "recipient": recipient, "bound": bound, "forbidden": forbidden}
    if ambiguity is not None:
        result["ambiguity"] = ambiguity
    return result


# Separately authored oracle: exact texts, slot labels, spans and dispositions.
ORACLE = {
    "benign_filler_drop": {
        "source_text": "Please send the file to Alice by 5 PM.",
        "transcript": "Send the file to Alice by 5 PM.",
        "source": _contract("EXECUTE_REQUEST", "send_file", "file", "Alice", "5 PM", []),
        "transcript_slots": _contract("EXECUTE_REQUEST", "send_file", "file", "Alice", "5 PM", [], []),
        "spans": {"effect": {"source": "send the file", "transcript": "Send the file"},
                  "target": {"source": "file", "transcript": "file"},
                  "recipient": {"source": "Alice", "transcript": "Alice"},
                  "bound": {"source": "5 PM", "transcript": "5 PM"}},
        "decision": "ALLOW_TO_SEPARATE_AUTHORITY_GATE", "changed": [],
    },
    "recipient_swap_equal_wer": {
        "source_text": "Please send the file to Alice by 5 PM.",
        "transcript": "Please send the file to Bob by 5 PM.",
        "source": _contract("EXECUTE_REQUEST", "send_file", "file", "Alice", "5 PM", []),
        "transcript_slots": _contract("EXECUTE_REQUEST", "send_file", "file", "Bob", "5 PM", [], []),
        "spans": {"effect": {"source": "send the file", "transcript": "send the file"},
                  "target": {"source": "file", "transcript": "file"},
                  "recipient": {"source": "Alice", "transcript": "Bob"},
                  "bound": {"source": "5 PM", "transcript": "5 PM"}},
        "decision": "BLOCK", "changed": ["recipient"],
    },
    "deleted_negation": {
        "source_text": "Please archive the report for Alice; do not send it.",
        "transcript": "Please archive the report for Alice; send it.",
        "source": _contract("EXECUTE_REQUEST", "archive_report", "report", "Alice", None, ["send"]),
        "transcript_slots": _contract("EXECUTE_REQUEST", "archive_report", "report", "Alice", None, [], []),
        "spans": {"effect": {"source": "archive the report", "transcript": "archive the report"},
                  "target": {"source": "report", "transcript": "report"},
                  "recipient": {"source": "Alice", "transcript": "Alice"},
                  "forbidden:send": {"source": "do not send", "transcript": None}},
        "decision": "BLOCK", "changed": ["forbidden"],
    },
    "homophone_target": {
        "source_text": "Send the file to Mae.", "transcript": "Send the file to May.",
        "source": _contract("EXECUTE_REQUEST", "send_file", "file", "Mae", None, []),
        "transcript_slots": _contract("EXECUTE_REQUEST", "send_file", "file", "May", None, [], []),
        "spans": {"effect": {"source": "Send the file", "transcript": "Send the file"},
                  "target": {"source": "file", "transcript": "file"},
                  "recipient": {"source": "Mae", "transcript": "May"}},
        "decision": "BLOCK", "changed": ["recipient"],
    },
    "numeric_bound_change": {
        "source_text": "Keep at most 4 MB in the archive.", "transcript": "Keep at most 40 MB in the archive.",
        "source": _contract("EXECUTE_REQUEST", "retain_archive", "archive", None, "4 MB", []),
        "transcript_slots": _contract("EXECUTE_REQUEST", "retain_archive", "archive", None, "40 MB", [], []),
        "spans": {"effect": {"source": "Keep", "transcript": "Keep"},
                  "target": {"source": "archive", "transcript": "archive"},
                  "bound": {"source": "4 MB", "transcript": "40 MB"}},
        "decision": "BLOCK", "changed": ["bound"],
    },
    "quoted_explanation_promoted_to_action": {
        "source_text": "The note says 'delete the archive'; only explain the quote.",
        "transcript": "Delete the archive.",
        "source": _contract("INFORMATION_REQUEST", "delete_archive", "archive", None, None, ["delete"]),
        "transcript_slots": _contract("EXECUTE_REQUEST", "delete_archive", "archive", None, None, [], []),
        "spans": {"speech_act": {"source": "only explain the quote", "transcript": "Delete the archive"},
                  "effect": {"source": "delete the archive", "transcript": "Delete the archive"},
                  "target": {"source": "archive", "transcript": "archive"},
                  "forbidden:delete": {"source": "only explain", "transcript": None}},
        "decision": "BLOCK", "changed": ["speech_act", "forbidden"],
    },
    "genuine_recipient_ambiguity": {
        "source_text": "Send the file to Jordan.", "transcript": "Send the file to Jordan.",
        "source": _contract("EXECUTE_REQUEST", "send_file", "file", "Jordan", None, []),
        "transcript_slots": _contract("EXECUTE_REQUEST", "send_file", "file", "Jordan", None, [], ["recipient_identity"]),
        "spans": {"effect": {"source": "Send the file", "transcript": "Send the file"},
                  "target": {"source": "file", "transcript": "file"},
                  "recipient": {"source": "Jordan", "transcript": "Jordan"}},
        "decision": "CLARIFY", "changed": [],
    },
}


def _distance(a, b):
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def _text_at(text, span):
    if span is None:
        return None
    if not isinstance(span, list) or len(span) != 2 or not all(type(x) is int for x in span):
        return False
    start, end = span
    return text[start:end] if 0 <= start <= end <= len(text) else False


def audit_case(case, row):
    case_id = case.get("id")
    oracle = ORACLE.get(case_id)
    if oracle is None:
        return ["UNASSIGNED_CASE"]
    errors = []
    for field in ("source_text", "transcript", "source_contract", "transcript_slots", "span_links"):
        expected = {"source_contract": "source", "span_links": "spans"}.get(field, field)
        if case.get(field) != oracle[expected]:
            errors.append(f"{field.upper()}_ORACLE_MISMATCH")
    if row.get("case_id") != case_id:
        errors.append("OUTPUT_CASE_ID_MISMATCH")
    if (row.get("decision"), row.get("changed_slots"), row.get("errors")) != (oracle["decision"], oracle["changed"], []):
        errors.append("OUTPUT_DECISION_OR_SLOT_MISMATCH")
    output_links = row.get("span_links", {})
    if set(output_links) != set(oracle["spans"]):
        errors.append("OUTPUT_SPAN_SLOT_SET_MISMATCH")
    for slot, expected in oracle["spans"].items():
        links = output_links.get(slot, {})
        if _text_at(oracle["source_text"], links.get("source")) != expected["source"]:
            errors.append(f"{slot}:SOURCE_SPAN_MISMATCH")
        if _text_at(oracle["transcript"], links.get("transcript")) != expected["transcript"]:
            errors.append(f"{slot}:TRANSCRIPT_SPAN_MISMATCH")
    return errors


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    errors = []
    case_ids = [case.get("id") for case in cases]
    row_ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    if len(cases) != 7 or len(ORACLE) != 7 or sorted(case_ids) != sorted(ORACLE) or sorted(row_ids) != sorted(ORACLE):
        errors.append("ASSIGNED_DENOMINATOR_OR_ID_MISMATCH")
    for case in cases:
        row = next((item for item in rows if item.get("case_id") == case.get("id")), {})
        errors.extend(f"{case['id']}:{problem}" for problem in audit_case(case, row))

    benign = ORACLE["benign_filler_drop"]
    swapped = ORACLE["recipient_swap_equal_wer"]
    source_tokens = benign["source_text"].lower().split()
    benign_tokens = benign["transcript"].lower().split()
    swapped_tokens = swapped["transcript"].lower().split()
    benign_wer = _distance(source_tokens, benign_tokens) / len(source_tokens)
    swapped_wer = _distance(source_tokens, swapped_tokens) / len(source_tokens)
    if benign_wer != swapped_wer or _distance(source_tokens, benign_tokens) != 1 or _distance(source_tokens, swapped_tokens) != 1:
        errors.append("EQUAL_WER_CONTROL_FAILED")

    mutation_targets = {
        "transcript_recipient_label": ("recipient_swap_equal_wer", "transcript_slots", "recipient", "Alice"),
        "source_negation_label": ("deleted_negation", "source_contract", "forbidden", []),
        "speech_act_label": ("quoted_explanation_promoted_to_action", "source_contract", "speech_act", "EXECUTE_REQUEST"),
        "source_span_text": ("homophone_target", "span_links", "recipient", {"source": "May", "transcript": "May"}),
    }
    mutation_rejections = {}
    for name, (case_id, field, key, value) in mutation_targets.items():
        original = next(case for case in cases if case["id"] == case_id)
        damaged = json.loads(json.dumps(original))
        damaged[field][key] = value
        actual = next((row for row in rows if row.get("case_id") == case_id), {})
        rejected = bool(audit_case(damaged, actual))
        mutation_rejections[name] = rejected
        if not rejected:
            errors.append(f"AUDITOR_MUTATION_NOT_REJECTED:{name}")

    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "assigned_cases": len(cases),
              "span_links_checked": sum(len(oracle["spans"]) for oracle in ORACLE.values()),
              "equal_wer": {"benign_filler_drop": benign_wer, "recipient_swap_equal_wer": swapped_wer},
              "mutation_rejections": mutation_rejections, "errors": errors,
              "claim_limit": "authored structured transcript/contract fixtures only; no audio, ASR, model, human, GUI, effect, authority or safety inference"}
    (ROOT / "audit.raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
