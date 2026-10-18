"""Independent oracle for a passive refresh with no active input lease."""
from __future__ import annotations

import json
from pathlib import Path
import re

CASE = Path(__file__).resolve().with_name("CASE.json")


def audit(case: dict) -> dict:
    command = case.get("refresh_command", {})
    accepted = case.get("accepted_event", {})
    fresh = case.get("fresh_observation", {})
    terminal = case.get("terminal_event", {})
    release = terminal.get("release", {})
    prior = case.get("preceding_active_program", {})
    prior_release = prior.get("input_release", {}).get("owner_release", {})
    source_signals = case.get("source_observation", {}).get("signals", {})
    fresh_signals = fresh.get("signals", {})

    def token_placeholders_are_opaque(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"intent_token", "accepted_token", "interruption_token"}:
                    if child is not None and (not isinstance(child, str) or
                            re.fullmatch(r"opaque-intent-token-[1-9][0-9]*", child) is None):
                        return False
                if not token_placeholders_are_opaque(child):
                    return False
        elif isinstance(value, list):
            return all(token_placeholders_are_opaque(child) for child in value)
        return True

    def binding_ids_are_pseudonymized(signals):
        return all(
            type(signals.get(name, {}).get("binding", {}).get(field)) is int and
            1 <= signals[name]["binding"][field] <= 16
            for name in ("health", "ammo") for field in ("focus", "surface")
        )

    checks = {
        "exact_single_observe_command": (
            command.get("op") == "submit" and
            command.get("steps") == [{"op": "observe"}] and
            command.get("id") == accepted.get("id") == terminal.get("id") == fresh.get("id")
        ),
        "no_input_admission_for_refresh": (
            type(case.get("matching_input_admission_count")) is int and
            case["matching_input_admission_count"] == 0
        ),
        "public_protocol_tokens_are_opaque": token_placeholders_are_opaque(case),
        "public_x11_binding_ids_are_pseudonymized": (
            binding_ids_are_pseudonymized(source_signals) and
            binding_ids_are_pseudonymized(fresh_signals)
        ),
        "preceding_active_lease_was_released_before_refresh": (
            len(prior.get("input_admissions", [])) > 0 and
            type(prior.get("id")) is str and bool(prior["id"]) and
            type(prior.get("accepted_token")) is str and bool(prior["accepted_token"]) and
            all(admission.get("event") == "input_admission" and
                admission.get("id") == prior["id"] and
                admission.get("intent_token") == prior["accepted_token"]
                for admission in prior.get("input_admissions", [])) and
            prior.get("cancel_requested", {}).get("matched") is True and
            prior.get("cancel_requested", {}).get("id") == prior["id"] and
            prior_release.get("verified") is True and
            prior_release.get("intent_token") == prior.get("accepted_token") ==
                prior.get("input_release", {}).get("intent_token") ==
                prior.get("terminal", {}).get("interruption_token") and
            prior.get("input_release", {}).get("event") == "input_released" and
            prior.get("input_release", {}).get("id") == prior["id"] and
            prior.get("terminal", {}).get("id") == prior["id"] and
            prior_release.get("event") == "owner_release" and
            prior_release.get("reason") == "cancelled" and
            prior_release.get("keys_down") == [] and
            prior_release.get("buttons_down") == [] and
            prior_release.get("keys_unknown") == [] and
            prior_release.get("key_state_errors") == [] and
            prior.get("terminal", {}).get("status") == "cancelled"
        ),
        "prior_cancel_release_terminal_order_is_valid": (
            type(prior.get("cancel_requested", {}).get("requested_ns")) is int and
            type(prior_release.get("verified_ns")) is int and
            type(prior.get("terminal", {}).get("terminal_ns")) is int and
            prior["cancel_requested"]["requested_ns"] <= prior_release["verified_ns"] <=
                prior["terminal"]["terminal_ns"]
        ),
        "prior_terminal_precedes_passive_refresh": (
            type(prior.get("terminal", {}).get("terminal_ns")) is int and
            type(case.get("refresh_command_received_ns")) is int and
            prior["terminal"]["terminal_ns"] < case["refresh_command_received_ns"] and
            type(command.get("expected_sequence")) is int and
            case.get("source_observation", {}).get("sequence") == command.get("expected_sequence")
        ),
        "fresh_pair_is_observed_and_advancing": (
            fresh.get("event") == "typed_observation" and
            type(fresh.get("sequence")) is int and
            fresh["sequence"] > case.get("source_observation", {}).get("sequence", 0) and
            all(fresh_signals.get(name, {}).get("status") == "observed"
                and type(fresh_signals.get(name, {}).get("value")) is int
                and fresh_signals.get(name, {}).get("sequence") == fresh.get("sequence")
                and fresh_signals.get(name, {}).get("capture_ns") == fresh.get("capture_ns")
                for name in ("health", "ammo")) and
            1 <= fresh_signals.get("health", {}).get("value", 0) <= 200 and
            0 <= fresh_signals.get("ammo", {}).get("value", -1) <= 999 and
            all(source_signals.get(name, {}).get("status") == "unknown"
                for name in ("health", "ammo"))
        ),
        "terminal_is_completed_with_one_step": (
            terminal.get("status") == "completed" and
            type(terminal.get("steps_completed")) is int and
            terminal["steps_completed"] == 1
        ),
        "tokenless_release_is_verified_empty": (
            accepted.get("event") == "accepted" and
            type(accepted.get("intent_token")) is str and bool(accepted["intent_token"]) and
            release.get("intent_token") is None and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [] and release.get("key_state_errors") == []
            and release.get("event") == "owner_release" and
            release.get("reason") == "release"
        ),
        "original_runtime_refused_this_case": (
            case.get("original_refusal", {}).get("status") == "refused" and
            case.get("original_refusal", {}).get("reason") == "refresh_release_unqualified"
        ),
    }
    return {
        "schema": "source-refresh-no-lease-empty-release-independent-audit-v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "scope": "trace-slice contract only; does not establish physical key state",
        "checks": checks,
    }


def main() -> int:
    case = json.loads(CASE.read_text(encoding="utf-8"))
    result = audit(case)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
