"""Finite synthetic policy-table candidate for Issue #6515; no secret bytes."""

import json
import sys
from pathlib import Path


def _safe_provider(c):
    if not c["user_authorized"]:
        return "REFUSED_AUTHORITY"
    if not c.get("auth_effect_required", True) or not c.get("scope_match", True):
        return "UNKNOWN_PROVIDER_POLICY"
    if c["captured_origin"] != c["requested_origin"] or c["current_origin"] != c["requested_origin"]:
        return "REFUSED_ORIGIN"
    if not c["field_visible"] or not c["field_identity_stable"] or not c["focus_stable"]:
        return "REFUSED_STALE"
    if c["surface_origin"] is None:
        return "UNKNOWN_ORIGIN_SCOPE"
    if c["surface_origin"] != c["requested_origin"]:
        return "REFUSED_ORIGIN"
    if c["handle_expired"] or c["handle_used"] or c["session_captured"] != c["session_current"]:
        return "UNKNOWN_PROVIDER_POLICY"
    if not c["protected_input_path"]:
        return "UNSUPPORTED_SECRET_ROUTE"
    return "DELIVERED_TO_BOUND_TARGET"


def _broker(c):
    if not c["user_authorized"]:
        return "REFUSED_AUTHORITY"
    if not c.get("auth_effect_required", True):
        return "NO_ACTION_ALREADY_AUTHENTICATED"
    if not c.get("scope_match", True):
        return "REFUSED_SCOPE"
    if c["captured_origin"] != c["requested_origin"] or c["current_origin"] != c["requested_origin"]:
        return "REFUSED_ORIGIN"
    if c["surface_origin"] is None:
        return "UNKNOWN_ORIGIN_SCOPE"
    if c["surface_origin"] != c["requested_origin"]:
        return "REFUSED_ORIGIN"
    if c["session_captured"] != c["session_current"]:
        return "REFUSED_STALE"
    if c["generation_captured"] != c["generation_current"] or not c["field_identity_stable"] or not c["focus_stable"]:
        return "REFUSED_STALE"
    if c["handle_expired"]:
        return "REFUSED_EXPIRED"
    if c["handle_used"]:
        return "REFUSED_REPLAY"
    if not c["protected_input_path"]:
        return "UNSUPPORTED_SECRET_ROUTE"
    return "DELIVERED_TO_BOUND_TARGET"


def _actor(c):
    return "DELIVERED_TO_VISUAL_TARGET" if c["visual_match"] else "NO_ACTION"


def _manual(c):
    if c["manual_action"] and c["manual_authorized"] and c["manual_target_verified"]:
        return "DELIVERED_TO_HUMAN_VERIFIED_TARGET"
    return "NOT_AUTOMATED"


def run(fixture):
    rows = []
    for c in fixture["cases"]:
        for policy in fixture["policies"]:
            if policy == "actor_only_typing":
                decision = _actor(c)
                planner_exposure = True
            elif policy == "visual_only_typing":
                decision = _actor(c)
                planner_exposure = True
            elif policy == "documented_provider_profile":
                decision = _safe_provider(c)
                planner_exposure = False
            elif policy == "request_bound_broker":
                decision = _broker(c)
                planner_exposure = False
            elif policy == "no_automation_manual":
                decision = _manual(c)
                planner_exposure = False
            else:
                raise ValueError(f"unknown policy: {policy}")

            delivered = decision in {
                "DELIVERED_TO_VISUAL_TARGET",
                "DELIVERED_TO_BOUND_TARGET",
                "DELIVERED_TO_HUMAN_VERIFIED_TARGET",
            }
            wrong_recipient = delivered and c["surface_origin"] != c["requested_origin"]
            if c["effect_oracle"] == "prior_session":
                effect_status = "UNATTRIBUTED_PREEXISTING_SESSION"
            elif not delivered:
                effect_status = "NOT_DELIVERED"
            elif wrong_recipient:
                effect_status = "UNKNOWN_DELIVERY"
            elif c["effect_oracle"] == "verified_success":
                effect_status = "AUTH_EFFECT_VERIFIED"
            elif c["effect_oracle"] == "masked_ack":
                effect_status = "UNKNOWN_DELIVERY"
            elif c["effect_oracle"] == "unknown":
                effect_status = "UNKNOWN_DELIVERY"
            else:
                effect_status = "AUTH_EFFECT_NOT_VERIFIED"

            rows.append({
                "case_id": c["id"],
                "policy": policy,
                "decision": decision,
                "delivered": delivered,
                "wrong_origin_recipient": wrong_recipient,
                "planner_secret_exposed": planner_exposure,
                "ordinary_telemetry_secret_exposed": False,
                "effect_status": effect_status,
                "secret_bytes_in_record": False,
                "profile_basis": "documented_contract_only" if policy == "documented_provider_profile" else "synthetic_policy_model",
            })
    return {"schema": "planner-blind-credential-entry-raw-v1", "rows": rows}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json RAW.json")
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(argv[2]).parent.mkdir(parents=True, exist_ok=True)
    Path(argv[2]).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(raw["rows"]), "schema": raw["schema"]}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
