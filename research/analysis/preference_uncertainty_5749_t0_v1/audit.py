import copy
import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "explicit": ("ACT", "A", 0),
    "ambiguous-answer-ab": ("ASK_THEN_ACT", "A", 2),
    "ambiguous-answer-ba": ("ASK_THEN_ACT", "B", 2),
    "robust-c": ("ACT", "C", 1),
    "no-default-deadline": ("YIELD", None, 2),
    "no-response": ("YIELD", None, 2),
    "stale-answer": ("YIELD", None, 2),
    "hard-forbidden": ("ACT", "B", 0),
    "constructing": ("SCOPED_SELECTION", "B", None),
    "framing-sensitive": ("HOLD_FRAMING_SENSITIVE", None, None),
}


def audit(doc):
    errors = []
    if len(doc.get("rows", [])) != len(EXPECTED):
        errors.append("row_count_mismatch")
    for row in doc.get("rows", []):
        expected = EXPECTED.get(row.get("case_id"))
        if expected is None:
            errors.append("unknown_case")
            continue
        if (row.get("outcome"), row.get("action"), row.get("minimax_regret")) != expected:
            errors.append("oracle_mismatch:" + row["case_id"])
        if row.get("unsafe_or_forbidden"):
            errors.append("forbidden_effect_admitted")
    by_id = {row.get("case_id"): row for row in doc.get("rows", [])}
    if by_id.get("no-response", {}).get("action") is not None:
        errors.append("silence_treated_as_consent")
    if by_id.get("stale-answer", {}).get("action") is not None:
        errors.append("stale_choice_answer_accepted")
    if by_id.get("framing-sensitive", {}).get("action") is not None:
        errors.append("framing_sensitive_answer_forced")
    if by_id.get("constructing", {}).get("action") != "B":
        errors.append("choice_specific_constructed_preference_lost")
    if by_id.get("explicit", {}).get("counts_as_query"):
        errors.append("unnecessary_query_on_explicit_case")
    return {"errors": errors, "rows": len(doc.get("rows", [])),
            "query_count": sum(bool(r.get("counts_as_query")) for r in doc.get("rows", [])),
            "forbidden_effects": sum(bool(r.get("unsafe_or_forbidden")) for r in doc.get("rows", [])),
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def corruption_suite(doc):
    mutations = [
        ("force_forbidden", lambda d: d["rows"][7].update(action="A", unsafe_or_forbidden=True)),
        ("silence_as_consent", lambda d: d["rows"][5].update(action="A")),
        ("accept_stale", lambda d: d["rows"][6].update(action="B")),
        ("force_framing_choice", lambda d: d["rows"][9].update(action="A")),
        ("ask_explicit", lambda d: d["rows"][0].update(counts_as_query=True)),
        ("break_robust_regret", lambda d: d["rows"][3].update(minimax_regret=2)),
        ("drop_case", lambda d: d["rows"].pop()),
    ]
    results = []
    for name, mutate in mutations:
        mutant = copy.deepcopy(doc)
        mutate(mutant)
        results.append({"name": name, "rejected": bool(audit(mutant)["errors"])})
    return results


def main():
    raw = Path(sys.argv[1]).read_bytes()
    doc = json.loads(raw)
    result = audit(doc)
    controls = corruption_suite(doc)
    if not all(item["rejected"] for item in controls):
        result["errors"].append("corruption_control_escaped")
    result["corruptions"] = controls
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    result["disposition"] = "PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
