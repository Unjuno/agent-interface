"""Independent raw-only audit; intentionally imports no candidate code."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


FIELDS = ("principal", "target", "recipient", "effect", "scope", "expiry",
          "consequence")
DELTA_FIELDS = ("target", "recipient", "effect", "scope")
CONTROLS = ("approve", "deny", "cancel")


def request_digest(request):
    raw = json.dumps(request, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _card_errors(item, request, expected_highlights):
    errors = []
    expected_fields = {field: request.get(field) for field in FIELDS}
    if item.get("fields") != expected_fields:
        errors.append("effect_fields_do_not_match_truth")
    if item.get("visible_fields") != list(FIELDS):
        errors.append("required_field_not_visible")
    if item.get("highlighted_fields") != list(expected_highlights):
        errors.append("changed_field_highlight_mismatch")
    if item.get("request_digest") != request_digest(request):
        errors.append("request_digest_mismatch")
    if item.get("decision_controls") != list(CONTROLS):
        errors.append("deny_or_cancel_control_missing")
    if item.get("scope") != request.get("scope") or item.get("expiry") != request.get("expiry"):
        errors.append("scope_or_expiry_not_bound_per_effect")
    if item.get("consequence") != request.get("consequence"):
        errors.append("consequence_class_not_visible_or_bound")
    return errors


def discrepancies(fixture, rendered):
    errors = []
    requests = fixture["requests"]
    by_id = {item["request_id"]: item for item in requests}
    if rendered.get("schema") != "approval-sequence-assay-render-v1":
        errors.append("render_schema_mismatch")
    if rendered.get("sequence_id") != fixture.get("sequence_id"):
        errors.append("sequence_identity_mismatch")
    if rendered.get("requests") != requests:
        errors.append("request_truth_changed_or_omitted")

    arms = rendered.get("arms", {})
    for name in ("static", "changed_fields"):
        rows = arms.get(name, {}).get("items", [])
        if [row.get("request_id") for row in rows] != [r["request_id"] for r in requests]:
            errors.append(name + "_request_coverage_mismatch")
        prior = None
        for row in rows:
            req = by_id.get(row.get("request_id"))
            if req is None:
                errors.append(name + "_unknown_request")
                continue
            delta = [] if prior is None else [field for field in DELTA_FIELDS
                                               if req[field] != prior[field]]
            expected = delta if name == "changed_fields" else []
            errors.extend(name + ":" + e for e in _card_errors(row, req, expected))
            prior = req

    batches = arms.get("bounded_batch", {}).get("batches", [])
    flattened = [item for batch in batches for item in batch.get("items", [])]
    if [row.get("request_id") for row in flattened] != [r["request_id"] for r in requests]:
        errors.append("batch_request_coverage_or_order_mismatch")
    for batch in batches:
        ids = [item.get("request_id") for item in batch.get("items", [])]
        truth = [by_id.get(request_id) for request_id in ids]
        if any(req is None for req in truth):
            errors.append("batch_unknown_request")
            continue
        eligible = all(req["consequence"] == "nonconsequential" for req in truth)
        if batch.get("eligible") is not eligible:
            errors.append("batch_eligibility_mismatch")
        if not eligible and len(truth) != 1:
            errors.append("consequential_effects_grouped")
        if batch.get("decision_controls") != list(CONTROLS):
            errors.append("batch_deny_or_cancel_missing")
        for item, req in zip(batch.get("items", []), truth, strict=True):
            if item.get("consequence") != req["consequence"]:
                errors.append("batch_consequence_mismatch")
            errors.extend("batch:" + e for e in _card_errors(item, req, []))

    receipt = fixture["receipt"]
    old = by_id.get(receipt.get("request_id"))
    attempted = by_id.get(fixture.get("receipt_attempt_request_id"))
    expected_decision = "AUTHORIZED_ONCE" if request_digest(old) == request_digest(attempted) else "REFUSE_DIGEST_MISMATCH"
    checks = rendered.get("authority_checks", [])
    if len(checks) != 1:
        errors.append("authority_check_cardinality_mismatch")
    else:
        check = checks[0]
        if (check.get("receipt_request_id") != receipt.get("request_id") or
                check.get("attempt_request_id") != fixture.get("receipt_attempt_request_id") or
                check.get("receipt_digest") != request_digest(old) or
                check.get("attempt_digest") != request_digest(attempted) or
                check.get("decision") != expected_decision):
            errors.append("receipt_not_bound_to_exact_request_digest")
    if rendered.get("responses") != fixture.get("responses"):
        errors.append("deny_cancel_response_record_changed")
    return sorted(errors)


def corruption_cases(rendered):
    cases = {}
    row = copy.deepcopy(rendered)
    row["arms"]["static"]["items"][2]["fields"].pop("recipient")
    row["arms"]["static"]["items"][2]["visible_fields"].remove("recipient")
    cases["omitted_recipient"] = row

    row = copy.deepcopy(rendered)
    row["arms"]["static"]["items"][2]["fields"]["recipient"] = "self"
    cases["swapped_recipient"] = row

    row = copy.deepcopy(rendered)
    row["arms"]["changed_fields"]["items"][2]["highlighted_fields"] = []
    cases["stale_changed_field_highlight"] = row

    row = copy.deepcopy(rendered)
    batches = row["arms"]["bounded_batch"]["batches"]
    batches[0]["items"].append(batches[1]["items"][0])
    batches[0]["eligible"] = False
    del batches[1]
    cases["overbroad_consequential_batch"] = row

    row = copy.deepcopy(rendered)
    row["authority_checks"][0]["decision"] = "AUTHORIZED_ONCE"
    cases["stale_receipt_reuse"] = row

    row = copy.deepcopy(rendered)
    row["responses"] = [{"request_id": "r3", "choice": "approve"}]
    cases["deny_cancel_choice_erased"] = row
    return cases


def audit(fixture, rendered):
    errors = discrepancies(fixture, rendered)
    mutations = {name: discrepancies(fixture, changed)
                 for name, changed in corruption_cases(rendered).items()}
    rejected = {name: bool(case_errors) for name, case_errors in mutations.items()}
    if not all(rejected.values()):
        errors.append("mutation_control_false_accept")
    status = "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_CONSTRUCTION"
    return {
        "schema": "approval-sequence-assay-audit-v1",
        "status": status,
        "request_rows": len(fixture["requests"]),
        "display_arms": 3,
        "baseline_errors": errors,
        "mutation_controls": {
            "total": len(rejected), "rejected": sum(rejected.values()),
            "cases": rejected,
            "case_errors": mutations,
        },
        "participant_observations": 0,
        "scope": "finite authored fixture contract only; no human discrimination, attention, burden, or security-behavior result",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.input.read_text(encoding="utf-8"))
    rendered = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = audit(fixture, rendered)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)
    print(encoded, end="")
    if result["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
