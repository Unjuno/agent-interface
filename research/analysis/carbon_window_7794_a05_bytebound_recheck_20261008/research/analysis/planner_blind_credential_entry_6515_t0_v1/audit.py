"""Independent raw-only oracle for Issue #6515's finite policy table."""

import copy
import json
import sys
from pathlib import Path


def expected(c, policy):
    if policy == "actor_only_typing" or policy == "visual_only_typing":
        decision = "DELIVERED_TO_VISUAL_TARGET" if c["visual_match"] else "NO_ACTION"
        exposure = True
    elif policy == "documented_provider_profile":
        exposure = False
        if not c["user_authorized"]:
            decision = "REFUSED_AUTHORITY"
        elif not c.get("auth_effect_required", True) or not c.get("scope_match", True):
            decision = "UNKNOWN_PROVIDER_POLICY"
        elif c["captured_origin"] != c["requested_origin"] or c["current_origin"] != c["requested_origin"]:
            decision = "REFUSED_ORIGIN"
        elif not c["field_visible"] or not c["field_identity_stable"] or not c["focus_stable"]:
            decision = "REFUSED_STALE"
        elif c["surface_origin"] is None:
            decision = "UNKNOWN_ORIGIN_SCOPE"
        elif c["surface_origin"] != c["requested_origin"]:
            decision = "REFUSED_ORIGIN"
        elif c["handle_expired"] or c["handle_used"] or c["session_captured"] != c["session_current"]:
            decision = "UNKNOWN_PROVIDER_POLICY"
        elif not c["protected_input_path"]:
            decision = "UNSUPPORTED_SECRET_ROUTE"
        else:
            decision = "DELIVERED_TO_BOUND_TARGET"
    elif policy == "request_bound_broker":
        exposure = False
        if not c["user_authorized"]:
            decision = "REFUSED_AUTHORITY"
        elif not c.get("auth_effect_required", True):
            decision = "NO_ACTION_ALREADY_AUTHENTICATED"
        elif not c.get("scope_match", True):
            decision = "REFUSED_SCOPE"
        elif c["captured_origin"] != c["requested_origin"] or c["current_origin"] != c["requested_origin"]:
            decision = "REFUSED_ORIGIN"
        elif c["surface_origin"] is None:
            decision = "UNKNOWN_ORIGIN_SCOPE"
        elif c["surface_origin"] != c["requested_origin"]:
            decision = "REFUSED_ORIGIN"
        elif c["session_captured"] != c["session_current"]:
            decision = "REFUSED_STALE"
        elif c["generation_captured"] != c["generation_current"] or not c["field_identity_stable"] or not c["focus_stable"]:
            decision = "REFUSED_STALE"
        elif c["handle_expired"]:
            decision = "REFUSED_EXPIRED"
        elif c["handle_used"]:
            decision = "REFUSED_REPLAY"
        elif not c["protected_input_path"]:
            decision = "UNSUPPORTED_SECRET_ROUTE"
        else:
            decision = "DELIVERED_TO_BOUND_TARGET"
    elif policy == "no_automation_manual":
        exposure = False
        decision = "DELIVERED_TO_HUMAN_VERIFIED_TARGET" if c["manual_action"] and c["manual_authorized"] and c["manual_target_verified"] else "NOT_AUTOMATED"
    else:
        raise ValueError(policy)

    delivered = decision in {"DELIVERED_TO_VISUAL_TARGET", "DELIVERED_TO_BOUND_TARGET", "DELIVERED_TO_HUMAN_VERIFIED_TARGET"}
    wrong = delivered and c["surface_origin"] != c["requested_origin"]
    if c["effect_oracle"] == "prior_session":
        effect = "UNATTRIBUTED_PREEXISTING_SESSION"
    elif not delivered:
        effect = "NOT_DELIVERED"
    elif wrong:
        effect = "UNKNOWN_DELIVERY"
    elif c["effect_oracle"] == "verified_success":
        effect = "AUTH_EFFECT_VERIFIED"
    elif c["effect_oracle"] in {"unknown", "masked_ack"}:
        effect = "UNKNOWN_DELIVERY"
    else:
        effect = "AUTH_EFFECT_NOT_VERIFIED"
    return {
        "case_id": c["id"], "policy": policy, "decision": decision,
        "delivered": delivered, "wrong_origin_recipient": wrong,
        "planner_secret_exposed": exposure,
        "ordinary_telemetry_secret_exposed": False,
        "effect_status": effect, "secret_bytes_in_record": False,
        "profile_basis": "documented_contract_only" if policy == "documented_provider_profile" else "synthetic_policy_model",
    }


def verify(raw, fixture):
    errors = []
    if raw.get("schema") != "planner-blind-credential-entry-raw-v1":
        errors.append("schema_mismatch")
    expected_keys = {(c["id"], p): expected(c, p) for c in fixture["cases"] for p in fixture["policies"]}
    seen = set()
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append(f"duplicate:{key}")
            continue
        seen.add(key)
        truth = expected_keys.get(key)
        if truth is None:
            errors.append(f"unexpected:{key}")
        elif row != truth:
            errors.append(f"row_mismatch:{key}")
    for key in expected_keys.keys() - seen:
        errors.append(f"missing:{key}")

    mutations = []
    wrong = next(c for c in fixture["cases"] if c["id"] == "lookalike_wrong_origin")
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == wrong["id"] and r["policy"] == "request_bound_broker")["decision"] = "DELIVERED_TO_BOUND_TARGET"; mutations.append(m)
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == "valid_bound_effect" and r["policy"] == "request_bound_broker")["planner_secret_exposed"] = True; mutations.append(m)
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == "valid_bound_effect" and r["policy"] == "request_bound_broker")["ordinary_telemetry_secret_exposed"] = True; mutations.append(m)
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == "effect_oracle_absent" and r["policy"] == "request_bound_broker")["effect_status"] = "AUTH_EFFECT_VERIFIED"; mutations.append(m)
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == wrong["id"] and r["policy"] == "actor_only_typing")["wrong_origin_recipient"] = False; mutations.append(m)
    m = copy.deepcopy(raw); m["rows"].pop(); mutations.append(m)
    m = copy.deepcopy(raw); m["rows"].append(copy.deepcopy(m["rows"][0])); mutations.append(m)
    m = copy.deepcopy(raw); next(r for r in m["rows"] if r["case_id"] == "replayed_handle" and r["policy"] == "documented_provider_profile")["decision"] = "REFUSED_REPLAY"; mutations.append(m)
    rejected = sum(bool(verify_core(m, fixture)) for m in mutations)
    return errors, {"rows": len(raw.get("rows", [])), "expected_rows": len(expected_keys), "mutation_controls_rejected": rejected, "mutation_controls_total": len(mutations)}


def verify_core(raw, fixture):
    errors, _ = verify_without_mutations(raw, fixture)
    return errors


def verify_without_mutations(raw, fixture):
    errors = []
    if raw.get("schema") != "planner-blind-credential-entry-raw-v1":
        errors.append("schema_mismatch")
    truths = {(c["id"], p): expected(c, p) for c in fixture["cases"] for p in fixture["policies"]}
    seen = set()
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append(f"duplicate:{key}")
        seen.add(key)
        if key not in truths:
            errors.append(f"unexpected:{key}")
        elif row != truths[key]:
            errors.append(f"row_mismatch:{key}")
    errors.extend(f"missing:{k}" for k in truths.keys() - seen)
    return errors, None


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: audit.py FIXTURE.json RAW.json AUDIT.json")
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    errors, checks = verify(raw, fixture)
    result = {"schema": "planner-blind-credential-entry-audit-v1", "disposition": "PASS_METHOD_SCOPED" if not errors and checks["mutation_controls_rejected"] == checks["mutation_controls_total"] else "FAIL_METHOD", "errors": errors, **checks, "scope": "finite abstract policy-table sensitivity only; no actual secret, provider, browser, or authentication effect"}
    Path(argv[3]).parent.mkdir(parents=True, exist_ok=True)
    Path(argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main(sys.argv)
