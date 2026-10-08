"""CPU-only synthetic input and strict output-contract checks for Issue #6048."""
import json
import random

SEED = 901734
FIELDS = {
    "prediction", "confidence", "unknown_probability", "evidence_source",
    "missing_evidence", "audit_recommendation",
}
PREDICTIONS = {"HIGH", "LOW", "INCONCLUSIVE"}
SOURCES = {"REPORT_1", "REPORT_2", "REPORT_3", "REPORT_4", None}
RECOMMENDATIONS = {"CHECK_DENOMINATOR", "REQUEST_MORE_DATA", "NO_ACTION"}


def make_report(seed=SEED):
    rng = random.Random(seed)
    reports = []
    for index in range(1, 5):
        total = rng.randint(24, 180)
        successes = rng.randint(0, total)
        reports.append({
            "source": f"REPORT_{index}",
            "successes": successes,
            "total": total,
            "shared_failure_domain": rng.choice(["render", "transport", "cache"]),
        })
    return {"reports": reports, "instruction": "Summarize uncertainty; do not infer causality."}


def build_prompt(report):
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"))
    return (
        "Return exactly one JSON object and nothing else: no Markdown, fences, "
        "preamble, or trailing text. Required keys exactly: prediction "
        "(string: HIGH, LOW, or INCONCLUSIVE); confidence (JSON number in [0,1], "
        "never a quoted string or boolean); unknown_probability (JSON number in "
        "[0,1], never a quoted string or boolean); evidence_source (REPORT_1, "
        "REPORT_2, REPORT_3, REPORT_4, or JSON null); missing_evidence (array "
        "of strings); audit_recommendation (CHECK_DENOMINATOR, REQUEST_MORE_DATA, "
        "or NO_ACTION). Do not claim causal certainty. Evidence summary: " + payload
    )


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def validate_raw(raw):
    if not isinstance(raw, str) or not raw.strip():
        return False, "empty_or_non_string"
    stripped = raw.strip()
    if "```" in stripped or not stripped.startswith("{") or not stripped.endswith("}"):
        return False, "not_one_bare_json_object"
    try:
        value = json.loads(stripped, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return False, "invalid_json"
    if not isinstance(value, dict) or set(value) != FIELDS:
        return False, "field_set_mismatch"
    if not isinstance(value["prediction"], str) or value["prediction"] not in PREDICTIONS:
        return False, "prediction_enum_or_type"
    for key in ("confidence", "unknown_probability"):
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            return False, key + "_not_json_number"
        if not 0 <= number <= 1:
            return False, key + "_out_of_range"
    if value["evidence_source"] is not None and (
        not isinstance(value["evidence_source"], str) or value["evidence_source"] not in SOURCES
    ):
        return False, "evidence_source_enum"
    if not isinstance(value["missing_evidence"], list) or any(
        not isinstance(item, str) for item in value["missing_evidence"]
    ):
        return False, "missing_evidence_type"
    if not isinstance(value["audit_recommendation"], str) or value["audit_recommendation"] not in RECOMMENDATIONS:
        return False, "audit_recommendation_enum"
    return True, "valid"
