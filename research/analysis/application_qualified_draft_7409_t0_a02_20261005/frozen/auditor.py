#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #7409 A02."""
import copy
import json
import re
import sys


REVISION = re.compile(r"r(?:0|[1-9][0-9]*)\Z")


def revision_is_valid(token):
    return isinstance(token, str) and REVISION.fullmatch(token) is not None


def advance(token):
    if not revision_is_valid(token):
        return None
    return "r" + str(int(token[1:]) + 1)


def merged(document, values):
    result = copy.deepcopy(document)
    for field, value in values.items():
        result[field] = copy.deepcopy(value)
    return result


def reconstruct(case):
    original = copy.deepcopy(case["base"])
    base_token = case["base_revision"]
    live_token = case["human"]["revision_after_commit"]
    human_state = merged(original, case["human"]["writes"])
    direct = {
        "status": "DIRECT_COMMITTED",
        "final": merged(human_state, case["agent"]["writes"]),
        "revision": advance(live_token),
        "external_effects": copy.deepcopy(case["agent"]["external_effects"]),
    }
    app = case["app"]
    allowed = app["versioned_draft"] and app["draft_backend_isolated"] and app["no_external_effects"] and not case["agent"]["external_effects"]
    if not allowed:
        why = "SHARED_BACKEND" if not app["draft_backend_isolated"] else "EXTERNAL_EFFECT"
        staged = {
            "status": "REFUSED_ELIGIBILITY", "reason": why, "draft_created": False, "draft": None,
            "live_after_draft_write": human_state, "final": human_state, "final_revision": live_token,
            "revision_observation": None, "conflicts": [], "promoted": False, "external_effects": [],
            "events": ["HUMAN_COMMIT", "REFUSED_BEFORE_DRAFT"],
        }
        return {"case_id": case["id"], "direct": direct, "staged": staged}

    private_copy = merged(original, case["agent"]["writes"])
    pre_human = copy.deepcopy(original)
    post_human = merged(pre_human, case["human"]["writes"])
    trace = ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "READ_BASE_REVISION", "READ_LIVE_REVISION", "REVISION_COMPARE"]
    base_ok = revision_is_valid(base_token)
    live_ok = revision_is_valid(live_token)
    equal = (base_token == live_token) if (base_ok and live_ok) else None
    evidence = {
        "base_revision": base_token,
        "live_revision": live_token,
        "base_token_valid": base_ok,
        "live_token_valid": live_ok,
        "tokens_equal": equal,
        "gate": "UNKNOWN" if equal is None else ("MATCH" if equal else "CHANGED"),
        "event_index": trace.index("REVISION_COMPARE"),
    }
    changed_fields = set(case["human"]["writes"])
    dependent_fields = set(case["agent"]["writes"]) | set(case["agent"]["reads"])
    collisions = sorted(changed_fields & dependent_fields)
    trace.append("CHECK_READ_WRITE_CONFLICTS")
    if equal is None:
        final_status, explanation, destination, resulting_token, did_promote = "HOLD_REVISION_UNKNOWN", "INVALID_OR_MISSING_REVISION_TOKEN", post_human, live_token, False
        trace.append("PROMOTION_HELD_UNKNOWN_REVISION")
    elif collisions:
        final_status, explanation, destination, resulting_token, did_promote = "CONFLICT_HOLD", "OVERLAPPING_READ_OR_WRITE", post_human, live_token, False
        trace.append("CONFLICT_SURFACED")
    elif not app["explicit_promotion"]:
        final_status, explanation, destination, resulting_token, did_promote = "HOLD_PROMOTION_NOT_AUTHORIZED", "NO_EXPLICIT_PROMOTION", post_human, live_token, False
        trace.append("PROMOTION_HELD")
    else:
        final_status, explanation = "PROMOTED", "REVISION_GATE_AND_CONFLICT_CHECK_PASSED"
        destination, resulting_token, did_promote = merged(post_human, case["agent"]["writes"]), advance(live_token), True
        trace.append("EXPLICIT_PROMOTION")
    evidence["promotion_event_index"] = trace.index("EXPLICIT_PROMOTION") if did_promote else None
    staged = {
        "status": final_status, "reason": explanation, "draft_created": True, "draft": private_copy,
        "live_after_draft_write": pre_human, "live_after_human_commit": post_human,
        "final": destination, "final_revision": resulting_token, "revision_observation": evidence,
        "conflicts": collisions, "promoted": did_promote, "external_effects": [], "events": trace,
    }
    return {"case_id": case["id"], "direct": direct, "staged": staged}


def compare(cases, candidate):
    issues = []
    if candidate.get("schema") != "issue-7409-t0-a02-candidate-v1":
        issues.append("schema mismatch")
    actual = candidate.get("rows", [])
    if len(actual) != len(cases):
        issues.append("row-count mismatch")
    expected_rows = [reconstruct(case) for case in cases]
    for index, expected_row in enumerate(expected_rows):
        if index < len(actual) and actual[index] != expected_row:
            issues.append(f"row {index} differs from independent reconstruction")
    if [case["id"] for case in cases] != [row.get("case_id") for row in actual]:
        issues.append("row identity/order mismatch")
    return issues


def mutations_rejected(cases, candidate):
    outcomes = {}

    def attempt(name, alter):
        altered = copy.deepcopy(candidate)
        alter(altered)
        outcomes[name] = bool(compare(cases, altered))

    def row(result, case_id):
        return next(item for item in result["rows"] if item["case_id"] == case_id)

    attempt("missing_revision_receipt", lambda x: row(x, "C4-later-disjoint-revision")["staged"].pop("revision_observation"))
    attempt("current_revision_laundered_as_base", lambda x: row(x, "C4-later-disjoint-revision")["staged"]["revision_observation"].update({"live_revision": "r0", "tokens_equal": True, "gate": "MATCH"}))
    attempt("base_revision_laundered", lambda x: row(x, "C4-later-disjoint-revision")["staged"]["revision_observation"].update({"base_revision": "r1"}))
    attempt("changed_revision_flag_forged", lambda x: row(x, "C4-later-disjoint-revision")["staged"]["revision_observation"].update({"tokens_equal": True, "gate": "MATCH"}))
    attempt("check_moved_after_promotion", lambda x: row(x, "C4-later-disjoint-revision")["staged"].update({"events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "CHECK_READ_WRITE_CONFLICTS", "EXPLICIT_PROMOTION", "REVISION_COMPARE"], "revision_observation": dict(row(x, "C4-later-disjoint-revision")["staged"]["revision_observation"], event_index=5, promotion_event_index=4)}))
    attempt("stale_same_field_promoted", lambda x: row(x, "C2-same-field")["staged"].update({"status": "PROMOTED", "promoted": True, "conflicts": []}))
    attempt("hidden_dependency_promoted", lambda x: row(x, "C3-hidden-dependency")["staged"].update({"status": "PROMOTED", "promoted": True, "conflicts": []}))
    attempt("unknown_revision_promoted", lambda x: row(x, "C8-unavailable-live-revision")["staged"].update({"status": "PROMOTED", "promoted": True, "final_revision": "r2"}))
    return outcomes


def main():
    case_path, raw_path, audit_path = sys.argv[1:4]
    with open(case_path, encoding="utf-8") as stream:
        cases = json.load(stream)
    with open(raw_path, encoding="utf-8") as stream:
        output = json.load(stream)
    errors = compare(cases, output)
    controls = mutations_rejected(cases, output)
    if not all(controls.values()):
        errors.append("one or more frozen mutations were accepted")
    result = {
        "schema": "issue-7409-t0-a02-audit-v1",
        "disposition": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "reconstructed_rows": len(cases),
        "errors": errors,
        "mutations_rejected": sum(controls.values()),
        "mutations_total": len(controls),
        "mutations": controls,
        "scope": "authored deterministic fixture only; no real application, human, model, GUI, live-view effect, or safety result",
    }
    with open(audit_path, "w", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"disposition": result["disposition"], "errors": errors, "rows": len(cases), "mutations_rejected": result["mutations_rejected"], "mutations_total": result["mutations_total"]}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
