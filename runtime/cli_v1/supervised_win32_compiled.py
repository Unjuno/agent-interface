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


def _terminal(reply, action_name):
    row = _raw_report(reply)
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
    supervision = row.get("supervision")
    action = supervision.get("action") if type(supervision) is dict else None
    custody = (action.get("completion_custody")
        if type(action) is dict else None)
    confirmed = (type(custody) is dict
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
    refused_before_input = (input_dispatched is False
        and operation_invoked is False)
    action_id = row.get("operation_id") or row.get("call_id")
    if type(action_id) is not str or not action_id:
        action_id = "compiled-" + uuid.uuid4().hex
    terminal = {"status": ("completed" if status in ("returned", "completed") and confirmed
            else "refused" if refused_before_input else "uncertain"),
        "action_id": action_id,
        "effect_ref": "standard-win32-" + action_name,
        "release": {"verified": confirmed,
            "keys_down": [] if confirmed else ["unknown"],
            "buttons_down": [] if confirmed else ["unknown"]}}
    if input_dispatched is not None:
        terminal["input_dispatched"] = input_dispatched
    return terminal


def run_public_compiled(interface, program_templates, *, target,
        current_binding_revision, region, observe, dispatch, perceive, verify_effect,
        expected_generation=None,
        cancelled=lambda: False, clock=time.monotonic_ns, journal=None):
    """Run one compiled graph using standard supervised Win32 MCP calls.

    ``observe(target, frame, region)`` calls ``interface_observe`` and returns
    its MCP reply. ``dispatch(program, observation_seq, binding_revision)``
    calls ``interface_dispatch`` and returns its MCP reply. Program templates
    are ordinary caller-authored standard programs, one per graph action; the
    adapter supplies a fresh observation sequence, binding revision, target
    generation and one-use program/lease IDs before each standard dispatch.

    This adapter does not provide an application oracle. Pixel/perception
    predicates and effect verdicts are caller-owned, and ``TASK_SUCCEEDED`` is
    only the compiled method's verdict. Independently verify the task through
    the configured standard task oracle when one exists.
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
    if any(symbol["target_reference"] != target
           for symbol in spec["symbols"].values()):
        raise ValueError("compiled target references must name the configured Win32 target")
    if (type(program_templates) is not dict
            or set(program_templates) != set(spec["actions"])):
        raise ValueError("one standard program template per compiled action required")
    if not all(callable(fn) for fn in (observe, dispatch, perceive,
                                       verify_effect, cancelled, clock)):
        raise ValueError("standard tools and caller verifiers must be callable")
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

    def observe_adapter(_request):
        nonlocal generation, sequence, latest_report, latest_reply
        reply = observe(target, "window_client", deepcopy(region))
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
        if type(call_id) is str and call_id:
            action_call_ids.append(call_id)
        return _terminal(reply, request["action"])

    def verify_adapter(request):
        return verify_effect(request, deepcopy(latest_report), latest_reply)

    adapters = {"observe": observe_adapter, "admit": admit_adapter,
        "execute": execute_adapter, "verify_effect": verify_adapter,
        "cancelled": cancelled}
    if journal is not None:
        adapters["journal"] = journal
    receipt = run_graph(spec, adapters, clock=clock)
    receipt["standard_observation_call_ids"] = list(observation_call_ids)
    receipt["standard_action_call_ids"] = list(action_call_ids)
    receipt["task_success"] = None
    return receipt
