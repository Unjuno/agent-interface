"""Compose bounded compiled methods through the standard supervised Win32 tools.

This is a caller-side adapter. ``observe`` and ``dispatch`` must call the
standard public MCP tools; perception and effect verification remain trusted,
application-specific caller code. The adapter pins the target generation from
the first standard observation and never retries a standard dispatch.
"""
from copy import deepcopy
import hashlib
import json
import re
import time
import uuid

from runtime.core_v1.compiled_gui import (
    ObservationAssociationChanged,
    run as run_graph,
    validate,
)
from runtime.core_v1.contract import validate_program


_GENERATION = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[0-9a-f]{32}$")
_MAX_RECOVERY_HORIZON_NS = 60_000_000_000


def _recovery_attempts_match_obligations(obligations, attempts):
    """Require a shape-valid UP attempt for each keyed release obligation."""
    if type(obligations) not in (list, tuple) or type(attempts) is not list:
        return False
    from runtime.backends.win32_v1.backend import virtual_key
    expected_attempts = []
    for item in obligations:
        if type(item) is not str:
            return False
        if not item.startswith("key:"):
            continue
        parts = item.split(":")
        if len(parts) == 3 and parts[1] and parts[2]:
            key, encoding = parts[2], "virtual_key"
        elif (len(parts) >= 4 and parts[-1]
                in ("virtual_key", "scan_code")
                and ":".join(parts[1:-2]) and parts[-2]):
            key, encoding = parts[-2], parts[-1]
        else:
            return False
        try:
            expected_attempts.append((virtual_key(key), encoding))
        except Exception:
            return False
    if len(attempts) != len(expected_attempts):
        return False
    actual_attempts = []
    for attempt in attempts:
        if (type(attempt) is not dict
                or set(attempt) not in (
                    {"virtual_key", "encoding", "status"},
                    {"virtual_key", "encoding", "status", "error_type"})
                or type(attempt.get("virtual_key")) is not int
                or not 0 <= attempt["virtual_key"] <= 0xFFFF
                or attempt.get("encoding") not in ("virtual_key", "scan_code")
                or attempt.get("status") not in ("returned", "raised")):
            return False
        if attempt["status"] == "raised":
            error_type = attempt.get("error_type")
            if type(error_type) is not str or not error_type or len(error_type) > 64:
                return False
        elif "error_type" in attempt:
            return False
        actual_attempts.append((attempt["virtual_key"], attempt["encoding"]))
    return sorted(actual_attempts) == sorted(expected_attempts)


def _verified_recovery_custody(row, action, call_id, operation_id,
                               generation, expected_call_id,
                               expected_generation):
    """Validate the public cancellation receipt for a recovered dispatch.

    A recovered call has no normal-completion custody row. Its release proof
    lives in the cancellation result and is accepted only when the recovery
    identity joins the original call/action/generation and its bounded
    post-release observation horizon is complete.
    """
    cancellation = row.get("cancellation")
    result = cancellation.get("result") if type(cancellation) is dict else None
    producer = result.get("producer_identity") if type(result) is dict else None
    readback = result.get("readback") if type(result) is dict else None
    obligations = result.get("obligations") if type(result) is dict else None
    action_obligations = action.get("obligations")
    cancellation_id = (cancellation.get("operation_id")
        if type(cancellation) is dict else None)
    recovery_id = result.get("recovery_id") if type(result) is dict else None
    horizon = result.get("late_input_horizon_ns") if type(result) is dict else None
    sample_gap = (result.get("late_input_max_sample_gap_ns")
        if type(result) is dict else None)
    observed_gap = (result.get("late_input_max_observed_gap_ns")
        if type(result) is dict else None)
    count = (result.get("late_input_observation_count")
        if type(result) is dict else None)
    release_ns = (result.get("late_input_release_received_ns")
        if type(result) is dict else None)
    start_ns = (result.get("late_input_observation_start_ns")
        if type(result) is dict else None)
    end_ns = (result.get("late_input_observation_end_ns")
        if type(result) is dict else None)
    readback_states = (readback.get("key_button_states")
        if type(readback) is dict else None)
    obligations_valid = (
        type(obligations) in (list, tuple)
        and all(type(item) is str and any(item.startswith(prefix)
            and len(item) > len(prefix)
            for prefix in ("key:", "button:", "unicode:"))
            for item in obligations)
        and len(set(obligations)) == len(obligations))
    unicode_units = (sum(item.startswith("unicode:") for item in obligations)
        if obligations_valid else None)
    key_button_units = (sum(item.startswith(("key:", "button:"))
        for item in obligations) if obligations_valid else None)
    recovery_attempts = (result.get("recovery_release_key_up_attempts")
        if type(result) is dict else None)
    attempts_valid = _recovery_attempts_match_obligations(
        obligations, recovery_attempts)
    action_result = action.get("result")
    automatic_unknown_source = (
        type(cancellation) is dict and type(action_result) is dict
        and cancellation.get("automatic_completion_recovery") is True
        and action.get("status") == "unknown"
        and action.get("release_confirmed") is False
        and action_result.get("status") == "unknown"
        and action_result.get("release_confirmed") is False
        and action_result.get("error") == "COMPLETION_EVIDENCE_UNCONFIRMED"
        and type(action_result.get("error_type")) is str
        and bool(action_result["error_type"])
        and cancellation.get("completion_error_type")
            == action_result["error_type"]
        and action.get("task_success") is None
        and action.get("replay_allowed") is False
        and action_result.get("task_success") is None
        and action_result.get("replay_allowed") is False
    )
    recovered_source = (
        action.get("status") == "recovered"
        and action.get("release_confirmed") is True
        and type(action_result) is dict
        and action_result.get("status") == "recovered"
    )
    return (
        type(cancellation) is dict and type(result) is dict
        and cancellation.get("status") == "recovered"
        and cancellation.get("owner_phase") == "recovered"
        and type(cancellation_id) is str
        and _IDENTIFIER.fullmatch(cancellation_id) is not None
        and cancellation.get("action_operation_id") == operation_id
        and cancellation.get("target_generation") == expected_generation
        and cancellation.get("release_confirmed") is True
        and cancellation.get("replay_allowed") is False
        and result.get("status") == "recovered"
        and result.get("phase") == "recovered"
        and type(recovery_id) is str
        and _IDENTIFIER.fullmatch(recovery_id) is not None
        and result.get("operation_id") == operation_id
        and result.get("target_generation") == expected_generation
        and result.get("release_confirmed") is True
        and result.get("replay_allowed") is False
        and result.get("late_input_validation_error") is None
        and type(result.get("producer_exit_code")) is int
        and type(producer) is dict
        and type(producer.get("pid")) is int and producer["pid"] > 0
        and type(producer.get("creation_time_100ns")) is int
        and producer["creation_time_100ns"] > 0
        and type(horizon) is int and 0 < horizon <= _MAX_RECOVERY_HORIZON_NS
        and type(sample_gap) is int and sample_gap > 0
        and type(observed_gap) is int and 0 <= observed_gap <= sample_gap
        and type(count) is int and count >= 2
        and type(release_ns) is int and release_ns > 0
        and type(start_ns) is int and 0 <= start_ns - release_ns <= sample_gap
        and type(end_ns) is int and end_ns >= start_ns
        and end_ns - release_ns >= horizon
        # A bounded horizon and release flag do not substitute for the
        # independently identity-bound terminal neutral readback. Preserve
        # that proof in the composed result before classifying custody.
        and type(readback) is dict
        and readback.get("operation_id") == operation_id
        and readback.get("target_generation") == expected_generation
        and readback.get("recovery_id") == recovery_id
        and readback.get("neutral") is True
        and type(readback.get("observed_monotonic_ns")) is int
        and readback["observed_monotonic_ns"] == end_ns
        and type(obligations) in (list, tuple)
        and obligations_valid
        and attempts_valid
        and type(action_obligations) in (list, tuple)
        and list(action_obligations) == list(obligations)
        and type(readback_states) is list
        and len(readback_states) == key_button_units
        and all(state is False for state in readback_states)
        and type(readback.get("unicode_event_units")) is int
        and readback.get("unicode_event_units") == unicode_units
        and call_id == expected_call_id
        and generation == expected_generation
        and row.get("call_id") == expected_call_id
        and type(operation_id) is str
        and _IDENTIFIER.fullmatch(operation_id) is not None
        and type(generation) is str
        and _GENERATION.fullmatch(generation) is not None
        and (recovered_source or automatic_unknown_source)
    )


def _content_object(reply):
    """Decode a standard MCP result or accept its already-decoded JSON row."""
    if type(reply) is dict:
        return deepcopy(reply)
    content = getattr(reply, "content", None)
    if type(content) is not list:
        raise ValueError("standard MCP tool reply has no content list")
    for block in content:
        text = getattr(block, "text", None)
        if type(text) is str:
            try:
                value = json.loads(text)
            except (TypeError, ValueError):
                continue
            if type(value) is dict:
                return value
    raise ValueError("standard MCP tool reply has no JSON object")


def _raw_report(reply):
    value = _content_object(reply)
    receipt = value.get("receipt")
    if type(receipt) is dict:
        source = receipt.get("source")
        if type(source) is dict and type(source.get("raw_report")) is dict:
            return deepcopy(source["raw_report"])
    raw = value.get("raw_result")
    if type(raw) is dict:
        return deepcopy(raw)
    return value


def _capture_ns(report):
    observation = report.get("observation")
    if type(observation) is dict:
        value = observation.get("capture_started_ns")
        if type(value) is int and value >= 0:
            return value
    value = report.get("capture_started_ns")
    if type(value) is int and value >= 0:
        return value
    raise ValueError("standard observation has no monotonic capture start")


def _terminal(reply, action_name, *, expected_call_id=None,
              expected_generation=None):
    row = _raw_report(reply)
    if (("action" in row or "supervision" in row)
            and all(key in row for key in ("status", "action_id", "effect_ref", "release"))):
        # A direct terminal must not hide retrieved or supervised custody.
        return {"status": "uncertain", "action_id": "ambiguous-interface-result",
            "effect_ref": "standard-win32-" + action_name,
            "release": {"verified": False, "keys_down": ["unknown"],
                "buttons_down": ["unknown"]}}
    if (type(row.get("status")) is str
            and type(row.get("action_id")) is str
            and type(row.get("effect_ref")) is str
            and type(row.get("release")) is dict):
        # The compiled core accepts only its terminal contract. Standard
        # Win32 receipts also carry call IDs and other caller-level evidence;
        # those are retained by the wrapper's receipt join, not forwarded as
        # undeclared terminal fields.
        terminal = {key: deepcopy(row[key]) for key in
            ("status", "action_id", "effect_ref", "release")}
        if "input_dispatched" in row:
            terminal["input_dispatched"] = deepcopy(row["input_dispatched"])
        return terminal
    # interface_results is a read-only retrieval envelope, so its outer
    # input_dispatched=false describes the query. Only the nested action and
    # its completion custody may establish the original dispatch result.
    retrieved_action = row.get("action")
    if type(retrieved_action) is dict:
        action_result = retrieved_action.get("result")
        action_result = action_result if type(action_result) is dict else {}
        custody = retrieved_action.get("completion_custody")
        call_id = row.get("call_id")
        operation_id = retrieved_action.get("operation_id")
        generation = retrieved_action.get("target_generation")
        same_call = (type(expected_call_id) is str
            and call_id == expected_call_id)
        same_generation = (type(expected_generation) is str
            and generation == expected_generation)
        custody_verified = (type(custody) is dict
            and custody.get("release_confirmed") is True
            and custody.get("completion_readback_outcome") == "verified"
            and retrieved_action.get("release_confirmed") is True
            # Public interface_results preserves the canonical release flag
            # on the action/custody row. Some runtime result shapes include
            # a duplicate boolean, while others carry the release receipt
            # only; reject an explicit contradiction but do not require the
            # redundant field to be present, but reject malformed values.
            and ("release_confirmed" not in action_result
                 or action_result["release_confirmed"] is True))
        completed = (retrieved_action.get("status") == "completed"
            and action_result.get("status") == "completed")
        recovered = (retrieved_action.get("status") == "recovered"
            and action_result.get("status") == "recovered")
        automatic_unknown_source = (
            retrieved_action.get("status") == "unknown"
            and action_result.get("status") == "unknown"
            and type(row.get("cancellation")) is dict
            and row["cancellation"].get("automatic_completion_recovery") is True)
        identity_valid = (same_call and same_generation
            and type(operation_id) is str
            and _IDENTIFIER.fullmatch(operation_id) is not None)
        recovery_custody_verified = ((recovered or automatic_unknown_source) and
            _verified_recovery_custody(row, retrieved_action, call_id,
                operation_id, generation, expected_call_id,
                expected_generation))
        verified_release = identity_valid and (
            recovery_custody_verified
            if recovered or automatic_unknown_source else custody_verified)
        outer_delivery = retrieved_action.get("input_dispatched")
        inner_delivery = action_result.get("input_dispatched")
        delivery_conflict = (
            any(value is not None and type(value) is not bool
                for value in (outer_delivery, inner_delivery))
            or (type(outer_delivery) is bool and type(inner_delivery) is bool
                and outer_delivery is not inner_delivery))
        no_input_completion = (False in (outer_delivery, inner_delivery)
            and completed)
        terminal = {"status": ("uncertain" if delivery_conflict or no_input_completion
                else "completed" if verified_release and completed
                else "delivery_uncertain" if verified_release and
                    (recovered or automatic_unknown_source)
                else "uncertain"),
            "action_id": (operation_id if identity_valid
                else "unverified-interface-result"),
            "effect_ref": "standard-win32-" + action_name,
            "release": {"verified": verified_release,
                "keys_down": [] if verified_release else ["unknown"],
                "buttons_down": [] if verified_release else ["unknown"]}}
        input_dispatched = retrieved_action.get("input_dispatched")
        if type(input_dispatched) is not bool:
            input_dispatched = action_result.get("input_dispatched")
        if (type(input_dispatched) is bool and not delivery_conflict
                and input_dispatched is not False):
            terminal["input_dispatched"] = input_dispatched
        return terminal
    supervision = row.get("supervision")
    action = supervision.get("action") if type(supervision) is dict else None
    custody = (action.get("completion_custody")
        if type(action) is dict else None)
    confirmed = (type(supervision) is dict and type(action) is dict
        and type(expected_call_id) is str
        and _IDENTIFIER.fullmatch(expected_call_id) is not None
        and row.get("call_id") == expected_call_id
        and supervision.get("call_id") == expected_call_id
        and type(expected_generation) is str
        and _GENERATION.fullmatch(expected_generation) is not None
        and row.get("target_generation") == expected_generation
        and action.get("target_generation") == expected_generation
        and type(row.get("operation_id")) is str
        and _IDENTIFIER.fullmatch(row["operation_id"]) is not None
        and action.get("operation_id") == row["operation_id"]
        and action.get("status") in ("completed", "recovered")
        and action.get("release_confirmed") is True
        and type(custody) is dict
        and custody.get("release_confirmed") is True
        and custody.get("completion_readback_outcome") == "verified")
    status = row.get("status")
    result = row.get("result")
    if type(result) is dict:
        status = result.get("status", status)
    input_dispatched = row.get("input_dispatched")
    outer = _content_object(reply)
    if type(input_dispatched) is not bool:
        input_dispatched = outer.get("input_dispatched")
    operation_invoked = row.get("operation_invoked")
    if type(operation_invoked) is not bool:
        operation_invoked = outer.get("operation_invoked")
    action_delivery = action.get("input_dispatched") if type(action) is dict else None
    action_result = action.get("result") if type(action) is dict else None
    cancellation = (supervision.get("cancellation")
        if type(supervision) is dict else None)
    automatic_unknown_source = (
        type(action) is dict and type(action_result) is dict
        and type(cancellation) is dict
        and cancellation.get("automatic_completion_recovery") is True
        and action.get("status") == "unknown"
        and action.get("release_confirmed") is False
        and action_result.get("status") == "unknown"
        and action_result.get("release_confirmed") is False
        and action_result.get("error") == "COMPLETION_EVIDENCE_UNCONFIRMED"
        and type(action_result.get("error_type")) is str
        and bool(action_result["error_type"])
        and cancellation.get("completion_error_type")
            == action_result["error_type"]
        and action.get("task_success") is None
        and action.get("replay_allowed") is False
        and action_result.get("task_success") is None
        and action_result.get("replay_allowed") is False
        and type(expected_call_id) is str
        and row.get("call_id") == expected_call_id
        and type(expected_generation) is str
        and action.get("target_generation") == expected_generation
        and action.get("operation_id") == row.get("operation_id")
        and type(row.get("operation_id")) is str
        and _IDENTIFIER.fullmatch(row["operation_id"]) is not None
        and _verified_recovery_custody(supervision, action,
            row.get("call_id"), row.get("operation_id"),
            action.get("target_generation"), expected_call_id,
            expected_generation)
    )
    nested_delivery = (action_result.get("input_dispatched")
        if type(action_result) is dict else None)
    # Preserve every explicit delivery claim before choosing a fallback; a
    # malformed raw value must not be hidden by a valid outer envelope.
    result_delivery = result.get("input_dispatched") if type(result) is dict else None
    deliveries = (row.get("input_dispatched"), outer.get("input_dispatched"),
        result_delivery, action_delivery, nested_delivery)
    known_deliveries = [value for value in deliveries if type(value) is bool]
    delivery_conflict = (any(value is not None and type(value) is not bool
        for value in deliveries) or len(set(known_deliveries)) > 1)
    refused_before_input = (input_dispatched is False
        and operation_invoked is False and not delivery_conflict)
    action_id = row.get("operation_id") or row.get("call_id")
    if type(action_id) is not str or not action_id:
        action_id = "compiled-" + uuid.uuid4().hex
    no_input_nonrefusal = (input_dispatched is False and
        (not refused_before_input or (confirmed and action.get("status") == "completed")))
    terminal = {"status": ("uncertain" if delivery_conflict or no_input_nonrefusal
            else "delivery_uncertain" if automatic_unknown_source
            else "completed" if status in ("returned", "completed") and confirmed
            and action.get("status") == "completed"
            else "refused" if refused_before_input else "uncertain"),
        "action_id": action_id,
        "effect_ref": "standard-win32-" + action_name,
        "release": {"verified": confirmed or automatic_unknown_source,
            "keys_down": [] if confirmed or automatic_unknown_source else ["unknown"],
            "buttons_down": [] if confirmed or automatic_unknown_source else ["unknown"]}}
    if input_dispatched is not None and not delivery_conflict and not no_input_nonrefusal:
        terminal["input_dispatched"] = input_dispatched
    return terminal


def _task_oracle_evidence(reply, expected_call_id, expected_generation,
                          expected_operation_id, not_before_ns, not_after_ns):
    """Accept only the standard server's exact-call task-oracle receipt."""
    row = _content_object(reply)
    effect = row.get("task_effect")
    status = row.get("status")
    verdict = row.get("task_success")
    oracle_receipt = effect.get("receipt") if type(effect) is dict else None
    requested_ns = effect.get("requested_monotonic_ns") if type(effect) is dict else None
    received_ns = (effect.get("receipt_received_monotonic_ns")
        if type(effect) is dict else None)
    verdict_shape_valid = (
        (status == "verified" and type(verdict) is bool)
        or (status == "unknown" and verdict is None)
    )
    timing = {"oracle_requested_ns": requested_ns
        if type(requested_ns) is int and requested_ns > 0 else None,
        "oracle_observed_ns": None, "oracle_receipt_accepted_ns": None,
        "oracle_id": None, "oracle_outcome": None,
        "oracle_task_operation_id": None, "effect_evidence_ref": None}
    oracle_receipt_valid = status == "unknown" and oracle_receipt is None
    if type(oracle_receipt) is dict:
        outcome = oracle_receipt.get("outcome")
        observed_ns = oracle_receipt.get("observed_monotonic_ns")
        oracle_receipt_valid = (
            set(oracle_receipt) == {"call_id", "operation_id", "target_generation",
                "oracle_id", "outcome", "observed_monotonic_ns", "evidence_ref"}
            and oracle_receipt.get("call_id") == expected_call_id
            and oracle_receipt.get("target_generation") == expected_generation
            and type(oracle_receipt.get("operation_id")) is str
            and _IDENTIFIER.fullmatch(oracle_receipt.get("operation_id")) is not None
            and oracle_receipt.get("operation_id") == expected_operation_id
            and type(oracle_receipt.get("oracle_id")) is str
            and _IDENTIFIER.fullmatch(oracle_receipt.get("oracle_id")) is not None
            and outcome in {"success", "failure", "unknown"}
            and type(observed_ns) is int and observed_ns > 0
            and type(requested_ns) is int and requested_ns > 0
            and type(received_ns) is int and received_ns > 0
            and requested_ns <= observed_ns <= received_ns
            and type(oracle_receipt.get("evidence_ref")) is str
            and bool(oracle_receipt.get("evidence_ref"))
            and ((outcome == "success" and status == "verified" and verdict is True)
                or (outcome == "failure" and status == "verified" and verdict is False)
                or (outcome == "unknown" and status == "unknown" and verdict is None))
        )
        timing.update(oracle_observed_ns=observed_ns,
            oracle_receipt_accepted_ns=received_ns,
            oracle_id=oracle_receipt.get("oracle_id"),
            oracle_outcome=outcome,
            oracle_task_operation_id=oracle_receipt.get("operation_id"),
            effect_evidence_ref=oracle_receipt.get("evidence_ref"))
    elif status == "unknown" and oracle_receipt is None:
        oracle_receipt_valid = type(requested_ns) is int and requested_ns > 0
    valid = (
        _IDENTIFIER.fullmatch(expected_call_id) is not None
        and type(expected_operation_id) is str
        and _IDENTIFIER.fullmatch(expected_operation_id) is not None
        and row.get("call_id") == expected_call_id
        and row.get("scope") == "supervised_win32"
        and row.get("operation_invoked") is False
        and row.get("input_dispatched") is False
        and row.get("replay_allowed") is False
        and type(effect) is dict
        and effect.get("status") == status
        and effect.get("task_success") is verdict
        and verdict_shape_valid
        and type(not_before_ns) is int and not_before_ns > 0
        and type(not_after_ns) is int and not_after_ns >= not_before_ns
        and type(requested_ns) is int and not_before_ns <= requested_ns <= not_after_ns
        and (oracle_receipt is None or
             (type(received_ns) is int and received_ns <= not_after_ns))
        and oracle_receipt_valid
    )
    digest = hashlib.sha256(json.dumps(row, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    return {"status": status if type(status) is str else "invalid",
        "action_call_id": expected_call_id,
        "task_success": verdict if valid and type(verdict) is bool else None,
        "valid": valid, "evidence_digest": digest, **timing}


def run_public_compiled(interface, program_templates, *, target,
        current_binding_revision, region, observe, dispatch, perceive, verify_effect,
        capture_frame="window_client",
        expected_generation=None,
        verify_task=None, resolve_pending=None, cancelled=lambda: False,
        clock=time.monotonic_ns,
        journal=None):
    """Run one compiled graph using standard supervised Win32 MCP calls.

    ``observe(target, frame, region)`` calls ``interface_observe`` and returns
    its MCP reply. ``dispatch(program, observation_seq, binding_revision)``
    calls ``interface_dispatch`` and returns its MCP reply. Program templates
    are ordinary caller-authored standard programs, one per graph action; the
    adapter supplies a fresh observation sequence, binding revision, target
    generation and one-use program/lease IDs before each standard dispatch.

    Pixel/perception predicates and effect verdicts are caller-owned. The
    optional ``verify_task(call_id)`` must call the configured standard public
    task oracle; its receipt is accepted only when bound to the exact final
    dispatch call ID and its supervised-Win32 non-action fields validate. It
    runs after graph success and after a release-verified recovered dispatch
    that ends in ``SAFE_YIELD / delivery_uncertain``. In the latter case an
    oracle verdict is recorded separately; it does not complete the graph.

    ``capture_frame`` selects the standard Win32 observation frame. Use
    ``screen_physical_px`` with an explicitly grounded screen-coordinate region
    when the target client-area capture cannot render its surface (for example,
    some GPU-backed applications); the pixels still require caller perception
    and target-generation association.
    """
    spec = validate(interface)
    if (type(target) is not str or not target
            or type(current_binding_revision) is not int
            or current_binding_revision < 1):
        raise ValueError("explicit target and positive binding revision required")
    if (expected_generation is not None
            and (type(expected_generation) is not str
                 or _GENERATION.fullmatch(expected_generation) is None)):
        raise ValueError("expected model-grounding target generation must be a SHA-256 digest")
    if (type(region) is not list or len(region) != 4
            or any(type(value) is not int for value in region)
            or not 0 <= region[0] <= 32767 or not 0 <= region[1] <= 32767
            or not 1 <= region[2] <= 8192 or not 1 <= region[3] <= 8192
            or region[2] * region[3] > 16_777_216):
        raise ValueError("bounded explicit [x,y,width,height] region required")
    if capture_frame not in ("window_client", "screen_physical_px"):
        raise ValueError("capture_frame must be a supported Win32 observation frame")
    if any(symbol["target_reference"] != target
           for symbol in spec["symbols"].values()):
        raise ValueError("compiled target references must name the configured Win32 target")
    if (type(program_templates) is not dict
            or set(program_templates) != set(spec["actions"])):
        raise ValueError("one standard program template per compiled action required")
    if not all(callable(fn) for fn in (observe, dispatch, perceive,
                                       verify_effect, cancelled, clock)):
        raise ValueError("standard tools and caller verifiers must be callable")
    if verify_task is not None and not callable(verify_task):
        raise ValueError("verify_task must call the configured standard task oracle")
    if resolve_pending is not None and not callable(resolve_pending):
        raise ValueError("resolve_pending must retrieve the exact pending public dispatch")
    if journal is not None and not callable(journal):
        raise ValueError("journal must be callable")

    templates = deepcopy(program_templates)
    for name, program in templates.items():
        if type(program) is not dict:
            raise ValueError("standard program templates must be objects")
        validate_program(program)
        source = program.get("source")
        authority = program.get("authority")
        if (type(source) is not dict or type(authority) is not dict
                or type(authority.get("expires_at_ns")) is not int):
            raise ValueError("program template requires standard source and authority")
        for operation in program.get("ops", []):
            if (operation.get("op") in ("focus", "activate")
                    and operation.get("target") != target):
                raise ValueError("program templates must remain on the configured target")

    generation = None
    sequence = 0
    latest_report = None
    latest_reply = None
    authorizations = {}
    observation_call_ids = []
    action_call_ids = []
    target_evidence = []

    def observe_adapter(_request):
        nonlocal generation, sequence, latest_report, latest_reply
        reply = observe(target, capture_frame, deepcopy(region))
        report = _raw_report(reply)
        observe_call_id = report.get("call_id") or _content_object(reply).get("call_id")
        if type(observe_call_id) is str and observe_call_id:
            observation_call_ids.append(observe_call_id)
        observation = report.get("observation")
        top_level_target = report.get("target")
        nested_target = (observation.get("target")
            if type(observation) is dict else None)
        if (top_level_target is not None and nested_target is not None
                and top_level_target != nested_target):
            raise ObservationAssociationChanged(
                "standard Win32 observation target fields disagree")
        observed_target = (top_level_target if top_level_target is not None
            else nested_target)
        observed_generation = report.get("target_generation")
        if (type(observed_generation) is not str
                or _GENERATION.fullmatch(observed_generation) is None
                or report.get("status") != "returned"
                or observed_target != target
                or report.get("target_generation_consistency") != "matched"):
            raise ObservationAssociationChanged(
                "standard Win32 observation has no valid target generation")
        if generation is None:
            if (expected_generation is not None
                    and observed_generation != expected_generation):
                raise ObservationAssociationChanged(
                    "standard Win32 target generation changed during model wait")
            generation = observed_generation
        elif generation != observed_generation:
            raise ObservationAssociationChanged(
                "standard Win32 target generation changed during compiled call")
        captured_ns = _capture_ns(report)
        retained_report, retained_reply = deepcopy(report), deepcopy(reply)
        predicates = perceive(deepcopy(report), deepcopy(reply))
        if type(predicates) is not dict:
            raise ValueError("perception callback must return a predicate object")
        sequence += 1
        latest_report = retained_report
        latest_reply = retained_reply
        raw_digest = hashlib.sha256(json.dumps(report, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        evidence_ref = report.get("observation_id")
        if type(evidence_ref) is not str or not evidence_ref:
            evidence_ref = "win32-observation-" + raw_digest[:24]
        target_evidence.append({
            "kind": "observation",
            "call_id": observe_call_id if type(observe_call_id) is str else None,
            "target": target,
            "target_generation": observed_generation,
            "target_generation_consistency": "matched",
            "observation_id": (report.get("observation_id")
                if type(report.get("observation_id")) is str else None),
            "observation_sequence": sequence,
            "evidence_ref": evidence_ref[:64],
            "evidence_digest": raw_digest,
            "captured_ns": captured_ns,
        })
        return {"sequence": sequence, "captured_ns": captured_ns,
            "surface": spec["surface"], "predicates": predicates,
            "evidence_ref": evidence_ref[:64], "evidence_digest": raw_digest}

    def admit_adapter(request):
        action_name = request["action"]
        observation = request["observation"]
        if generation is None or latest_report is None:
            return {"eligible": False, "status": "association_changed",
                "authorization": "", "expected_sequence": observation["sequence"],
                "valid_until_ns": clock()}
        template = deepcopy(templates[action_name])
        expires = template["authority"]["expires_at_ns"]
        now = clock()
        if type(expires) is not int or expires <= now:
            return {"eligible": False, "status": "stale",
                "authorization": "", "expected_sequence": observation["sequence"],
                "valid_until_ns": now}
        token = uuid.uuid4().hex
        authorizations[token] = {"action": action_name,
            "sequence": observation["sequence"], "generation": generation,
            "template": template, "expires_at_ns": expires}
        return {"eligible": True, "status": "revalidated",
            "authorization": token,
            "expected_sequence": observation["sequence"],
            "valid_until_ns": expires}

    def execute_adapter(request):
        authorization = request["authorization"]
        granted = authorizations.pop(authorization, None)
        if (type(granted) is not dict or granted["action"] != request["action"]
                or granted["sequence"] != request["expected_sequence"]
                or granted["generation"] != generation
                or granted["expires_at_ns"] <= clock()):
            return {"status": "refused", "action_id": "stale-compiled-authorization",
                "effect_ref": "stale-compiled-authorization",
                "input_dispatched": False,
                "release": {"verified": False, "keys_down": [], "buttons_down": []}}
        program = granted["template"]
        program["program_id"] = "compiled-" + uuid.uuid4().hex
        program["source"]["observation_seq"] = granted["sequence"]
        program["source"]["binding_revision"] = current_binding_revision
        program["source"]["target_generations"] = {target: granted["generation"]}
        program["authority"]["lease_id"] = "compiled-" + uuid.uuid4().hex
        program["authority"]["expires_at_ns"] = min(
            granted["expires_at_ns"], request["valid_until_ns"])
        reply = dispatch(program, granted["sequence"], current_binding_revision)
        reply_row = _raw_report(reply)
        call_id = reply_row.get("call_id") or _content_object(reply).get("call_id")
        pending_result_resolution = "not_pending"
        result_row = reply_row.get("result")
        result_status = (result_row.get("status")
            if type(result_row) is dict else None)
        if (resolve_pending is not None
                and (reply_row.get("status") in {"pending", "running", "cancel_pending"}
                    or result_status in {"pending", "running", "cancel_pending"})
                and type(call_id) is str
                and _IDENTIFIER.fullmatch(call_id) is not None):
            pending_result_resolution = "unresolved"
            try:
                resolved_reply = resolve_pending(call_id, deepcopy(reply))
                resolved_row = _raw_report(resolved_reply)
                resolved_supervision = resolved_row.get("supervision")
                resolved_supervision = (resolved_supervision
                    if type(resolved_supervision) is dict else {})
                resolved_action = resolved_row.get("action")
                if type(resolved_action) is not dict:
                    resolved_action = resolved_supervision.get("action")
                resolved_action = (resolved_action
                    if type(resolved_action) is dict else {})
                resolved_generation = (resolved_row.get("target_generation")
                    or resolved_action.get("target_generation"))
                if resolved_row.get("call_id") != call_id:
                    pending_result_resolution = "call_id_mismatch"
                elif resolved_generation != granted["generation"]:
                    pending_result_resolution = "generation_mismatch"
                else:
                    reply = resolved_reply
                    reply_row = resolved_row
                    pending_result_resolution = "same_call_id"
            except Exception as error:
                pending_result_resolution = "error:" + type(error).__name__
        if type(call_id) is str and call_id:
            action_call_ids.append(call_id)
        terminal = _terminal(reply, request["action"],
            expected_call_id=call_id, expected_generation=granted["generation"])
        target_evidence.append({
            "kind": "dispatch",
            "call_id": call_id if type(call_id) is str and call_id else None,
            "target": target,
            "target_generation": granted["generation"],
            "program_id": program["program_id"],
            "observation_sequence": granted["sequence"],
            "binding_revision": current_binding_revision,
            "action_id": terminal["action_id"],
            "effect_ref": terminal["effect_ref"],
            "status": terminal["status"],
            "pending_result_resolution": pending_result_resolution,
            "input_dispatched": terminal.get("input_dispatched"),
            "release_verified": (terminal.get("release", {}).get("verified") is True
                and terminal.get("release", {}).get("keys_down") == []
                and terminal.get("release", {}).get("buttons_down") == []),
        })
        return terminal

    def verify_adapter(request):
        return verify_effect(request, deepcopy(latest_report), latest_reply)

    adapters = {"observe": observe_adapter, "admit": admit_adapter,
        "execute": execute_adapter, "verify_effect": verify_adapter,
        "cancelled": cancelled}
    if journal is not None:
        adapters["journal"] = journal
    receipt = run_graph(spec, adapters, clock=clock)
    accepted_observations = {(row["sequence"], row["evidence_ref"])
        for row in receipt["observations"]}
    for row in target_evidence:
        if row["kind"] == "observation":
            row["compiled_observation_accepted"] = (
                (row["observation_sequence"], row["evidence_ref"])
                in accepted_observations)
    receipt["standard_observation_call_ids"] = list(observation_call_ids)
    receipt["standard_action_call_ids"] = list(action_call_ids)
    receipt["standard_target_evidence"] = deepcopy(target_evidence)
    receipt["bound_target_generation"] = generation
    receipt["task_success"] = None
    receipt["task_verification"] = None
    final_transition = (receipt["transitions"][-1]
        if receipt["transitions"] else None)
    terminal_events = [row for row in receipt["critical_events"]
        if row.get("event") == "action_terminal"]
    final_dispatch = (next((row for row in reversed(target_evidence)
        if row["kind"] == "dispatch"
        and any(event.get("action_id") == row["action_id"]
            for event in terminal_events)), None))
    final_call_id = (final_dispatch.get("call_id")
        if final_dispatch is not None else None)
    final_terminal_event = (next((event for event in reversed(terminal_events)
        if final_dispatch is not None
        and event.get("action_id") == final_dispatch["action_id"]), None))
    graph_completed = (receipt.get("outcome") == "TASK_SUCCEEDED"
        and final_transition is not None and final_dispatch is not None)
    recovered_effect_candidate = (receipt.get("outcome") == "SAFE_YIELD"
        and receipt.get("reason") == "delivery_uncertain"
        and final_dispatch is not None
        and final_dispatch.get("status") == "delivery_uncertain"
        and final_dispatch.get("release_verified") is True
        and final_terminal_event is not None
        and final_terminal_event.get("status") == "delivery_uncertain"
        and final_terminal_event.get("release_verified") is True
        and type(final_terminal_event.get("execution_accepted_ns")) is int
        and final_terminal_event["execution_accepted_ns"] > 0)
    if (verify_task is not None and (graph_completed or recovered_effect_candidate)
            and type(final_call_id) is str
            and _IDENTIFIER.fullmatch(final_call_id) is not None):
        try:
            oracle_reply = verify_task(final_call_id)
            caller_received_ns = clock()
            effect_not_before_ns = (final_transition["execution_accepted_ns"]
                if graph_completed else
                final_terminal_event.get("execution_accepted_ns"))
            task_evidence = _task_oracle_evidence(
                oracle_reply, final_call_id,
                final_dispatch["target_generation"], final_dispatch["action_id"],
                effect_not_before_ns, caller_received_ns)
            task_evidence["target_generation"] = final_dispatch["target_generation"]
            receipt["task_verification"] = task_evidence
            if task_evidence["valid"]:
                receipt["task_success"] = task_evidence["task_success"]
        except Exception as error:
            receipt["task_verification"] = {
                "status": "unavailable", "action_call_id": final_call_id,
                "target_generation": final_dispatch["target_generation"],
                "task_success": None, "valid": False,
                "error_type": type(error).__name__,
                "evidence_digest": None}
    return receipt
