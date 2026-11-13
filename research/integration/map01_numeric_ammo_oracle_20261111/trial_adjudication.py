"""Compose exact-call MAP01 effect and lease-boundary evidence checks.

This module consumes already-retained records. It performs no GUI, input,
process, network, or filesystem operations and does not mutate source evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

from receipt_adjudication import adjudicate_public_ammo_effect
from input_boundary import audit_expiry_key_release
from input_evidence_join import load_held_input_evidence


def adjudicate_trial(public_result, oracle_receipt, ammo_transition, *,
                     expected_call_id, key_samples, lease_deadline_ns,
                     sampler_report, max_key_bracket_ns=20_000_000):
    """Require exact-call ammo effect and a tightly sampled deadline release."""
    effect = adjudicate_public_ammo_effect(public_result, oracle_receipt,
        ammo_transition, expected_call_id=expected_call_id)
    boundary = audit_expiry_key_release(key_samples, lease_deadline_ns,
        max_bracket_ns=max_key_bracket_ns)
    sampler_report = sampler_report if type(sampler_report) is dict else {}
    gaps_valid = (type(sampler_report.get("max_observed_gap_ns")) is int
        and 0 <= sampler_report["max_observed_gap_ns"] <= max_key_bracket_ns)
    sampler_healthy = (
        sampler_report.get("clock") == "time.perf_counter_ns"
        and sampler_report.get("lease_clock") == "time.monotonic_ns"
        and sampler_report.get("sample_count") == len(key_samples)
        and sampler_report.get("read_error_type") is None
        and sampler_report.get("sample_limit_reached") is False
        and gaps_valid)
    checks = {
        "exact_call_task_effect": effect["status"] == "verified",
        "expiry_key_release_boundary": boundary["status"] == "verified",
        "sampler_health": sampler_healthy,
    }
    return {"status": "verified" if all(checks.values()) else "not_verified",
        "checks": checks, "effect": effect, "key_boundary": boundary,
        "sampler_health": {"valid": sampler_healthy,
            "clock": sampler_report.get("clock"),
            "lease_clock": sampler_report.get("lease_clock"),
            "sample_count": sampler_report.get("sample_count"),
            "max_observed_gap_ns": sampler_report.get("max_observed_gap_ns"),
            "sample_limit_reached": sampler_report.get("sample_limit_reached"),
            "read_error_type": sampler_report.get("read_error_type")}}


def adjudicate_retained_trial(public_result, oracle_receipt, ammo_transition, *,
        expected_call_id, action_submission, raw_sampler_report,
        max_key_bracket_ns=20_000_000):
    """Compose retained records, deriving deadline and samples from sources.

    The submitted program is the authority for the lease deadline. Sampler
    rows must be the complete retained sequence; callers cannot supply a
    projected boundary excerpt or a separately copied deadline.
    """
    try:
        program = action_submission["program"]
        authority = program["authority"]
        deadline = authority["expires_at_ns"]
        rows = raw_sampler_report["samples"]
        report = {key: raw_sampler_report[key] for key in (
            "clock", "lease_clock", "sample_count", "max_observed_gap_ns",
            "sample_limit_reached", "read_error_type")}
    except (KeyError, TypeError):
        return {"status": "not_verified", "reason": "missing_source_fields"}
    if type(public_result) is dict and type(public_result.get(
            "task_effect")) is not dict and type(public_result.get(
            "task_success")) is bool:
        public_result = {"call_id": public_result.get("call_id"),
            "task_success": public_result.get("task_success"),
            "task_effect": public_result.get("task_effect")}
    if (type(deadline) is not int or type(rows) is not list
            or type(report["sample_count"]) is not int
            or report["sample_count"] != len(rows)):
        return {"status": "not_verified", "reason": "incomplete_or_malformed_sampler"}
    if type(public_result) is dict and public_result.get("status") == "verified" and type(public_result.get(
            "task_effect")) is not dict:
        return {"status": "not_verified", "reason": "malformed_task_receipt"}
    return adjudicate_trial(public_result, oracle_receipt, ammo_transition,
        expected_call_id=expected_call_id, key_samples=rows,
        lease_deadline_ns=deadline, sampler_report=report,
        max_key_bracket_ns=max_key_bracket_ns)


def adjudicate_retained_trial_directory(trial_directory, *, expected_call_id,
        max_key_bracket_ns=20_000_000):
    """Adjudicate retained files without treating absent optional receipts as fatal.

    Missing task-oracle artifacts remain explicit and therefore cannot pass the
    effect check. Missing/malformed required submission or expiry-sampler
    evidence returns not_verified. Resolver and expiry-sampler key evidence is
    joined with provenance, never promoted between the two sources.
    """
    trial = Path(trial_directory)

    def read_optional(name):
        path = trial / name
        if not path.is_file():
            return None, "missing"
        try:
            return json.loads(path.read_text(encoding="utf-8")), None
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return None, type(error).__name__

    public_result, public_error = read_optional("verified-task-effect.json")
    oracle_receipt, oracle_error = read_optional("oracle-receipt.json")
    ammo_transition, ammo_error = read_optional("ammo-transition.json")
    action_submission, submission_error = read_optional("action-submission.json")
    sampler_report, sampler_error = read_optional("expiry-boundary-key-samples.json")
    held_state, held_join = load_held_input_evidence(trial)
    artifacts = {
        "public_task_result": public_error,
        "oracle_receipt": oracle_error,
        "ammo_transition": ammo_error,
        "action_submission": submission_error,
        "expiry_sampler": sampler_error,
        "held_input": held_join["classification"],
    }
    if submission_error is not None or sampler_error is not None:
        return {"status": "not_verified", "reason": "required_artifact_missing_or_invalid",
            "artifacts": artifacts, "held_input_evidence": held_join,
            "observed_w_down_before_terminal": held_state.get(
                "observed_w_down_before_terminal"),
            "terminal_w_down": held_state.get("terminal_w_down"),
            "task_success": None}
    result = adjudicate_retained_trial(public_result, oracle_receipt,
        ammo_transition, expected_call_id=expected_call_id,
        action_submission=action_submission, raw_sampler_report=sampler_report,
        max_key_bracket_ns=max_key_bracket_ns)
    result.update({"artifacts": artifacts, "held_input_evidence": held_join,
        "observed_w_down_before_terminal": held_state.get(
            "observed_w_down_before_terminal"),
        "terminal_w_down": held_state.get("terminal_w_down"),
        "public_task_success_claim": (public_result.get("task_success")
            if type(public_result) is dict else None),
        "task_success": True if result.get("status") == "verified" else None})
    return result
