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
        identity_valid = (same_call and same_generation
            and type(operation_id) is str
            and _IDENTIFIER.fullmatch(operation_id) is not None)
        verified_release = identity_valid and custody_verified
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
                else "delivery_uncertain" if verified_release and recovered
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
            else "completed" if status in ("returned", "completed") and confirmed
            and action.get("status") == "completed"
            else "refused" if refused_before_input else "uncertain"),
        "action_id": action_id,
        "effect_ref": "standard-win32-" + action_name,
        "release": {"verified": confirmed,
            "keys_down": [] if confirmed else ["unknown"],
            "buttons_down": [] if confirmed else ["unknown"]}}
    if input_dispatched is not None and not delivery_conflict and not no_input_nonrefusal:
        terminal["input_dispatched"] = input_dispatched
    return terminal


def _task_oracle_evidence(reply, expected_call_id, expected_generation,
                          expected_operation_id):
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
    dispatch call ID and its supervised-Win32 non-action fields validate.

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
    final_dispatch = (next((row for row in reversed(target_evidence)
        if row["kind"] == "dispatch"
        and final_transition is not None
        and row["action_id"] == final_transition["action_id"]), None))
    final_call_id = (final_dispatch.get("call_id")
        if final_dispatch is not None else None)
    if (verify_task is not None and receipt.get("outcome") == "TASK_SUCCEEDED"
            and type(final_call_id) is str
            and _IDENTIFIER.fullmatch(final_call_id) is not None):
        try:
            task_evidence = _task_oracle_evidence(
                verify_task(final_call_id), final_call_id,
                final_dispatch["target_generation"], final_dispatch["action_id"])
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
