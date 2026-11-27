"""Bind independent effect score receipts to one observed action and owner horizon.

Research-only adapter. It consumes retained local observations and public owner
receipts; it makes no live provider or GUI claim.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from comparison_measurement_v1 import validate_measured_run
from effect_attribution_v1 import adjudicate_effect
from ledger import LedgerValidationError
from recorded_comparison_adapter_v1 import (
    _derive_native_owner_attribution,
    _public_dispatch_event,
    _tool_body,
)

_HASH = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "agent-interface/task-effect-score-receipt-v1"
_FIELDS = {"schema", "task_id", "lookup_tool_call_id", "action_call_id",
           "action_operation_id", "target_generation", "scorer_id",
           "scorer_sha256",
           "task_success", "state_sha256", "before_task_success",
           "before_state_sha256", "before_observation", "after_observation",
           "effect_interval_ns"}


def _fail(message):
    raise LedgerValidationError(message)


def _read_receipt(root: Path, relative: str):
    if not isinstance(relative, str) or "\\" in relative:
        _fail("receipt path must be normalized relative POSIX path")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or not parsed.parts or parsed.as_posix() != relative or any(
            part in ("", ".", "..") for part in parsed.parts):
        _fail("receipt path escapes evidence root")
    base = root.resolve(strict=True)
    path = (base / Path(*parsed.parts)).resolve(strict=True)
    if not path.is_relative_to(base) or not path.is_file():
        _fail("receipt path is not a file inside evidence root")
    data = path.read_bytes()
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerValidationError("effect receipt is not valid JSON") from exc
    if type(value) is not dict or set(value) != _FIELDS or value.get("schema") != _SCHEMA:
        _fail("effect receipt does not match exact versioned schema")
    return value, hashlib.sha256(data).hexdigest(), data


def _capture(value, observations, calls, target_generation):
    guarded_fields = {
        "tool_call_id", "source_sequence", "captured_ns", "image_sha256"}
    public_fields = {
        "tool_call_id", "observation_id", "target_generation",
        "capture_started_ns", "capture_ended_ns", "image_sha256"}
    if type(value) is not dict or set(value) not in (guarded_fields, public_fields):
        _fail("capture reference fields do not match local observation contract")
    matches = [item for item in observations if item == value]
    call = calls.get(value["tool_call_id"])
    if len(matches) != 1 or call is None:
        _fail("capture reference is not a unique retained local observation")
    if set(value) == guarded_fields:
        if call.get("method") not in {
                "interface_guarded_observe", "interface_guarded_review_window",
                "interface_guarded_feedback"}:
            _fail("source-sequence capture must use a guarded observation call")
        if (type(value["captured_ns"]) is not int or
                type(value["source_sequence"]) is not int or
                value["source_sequence"] <= 0):
            _fail("capture time and positive source sequence must be integers")
        if not call["started_ns"] <= value["captured_ns"] <= call["ended_ns"]:
            _fail("guarded capture time lies outside its public observation call")
        return {**value, "capture_started_ns": value["captured_ns"],
                "capture_ended_ns": value["captured_ns"],
                "capture_kind": "guarded"}

    if (call.get("method") != "interface_observe" or
            not isinstance(value["observation_id"], str) or
            re.fullmatch(r"[0-9a-f]{32}", value["observation_id"]) is None or
            value["target_generation"] != target_generation or
            not isinstance(value["target_generation"], str) or
            _HASH.fullmatch(value["target_generation"]) is None):
        _fail("public capture must bind the exact observation and action generation")
    capture_start = value["capture_started_ns"]
    capture_end = value["capture_ended_ns"]
    if (type(capture_start) is not int or type(capture_end) is not int or
            capture_end < capture_start or
            not call["started_ns"] <= capture_start <= capture_end <= call["ended_ns"]):
        _fail("public capture interval lies outside its observation tool call")
    return {**value, "capture_kind": "public"}


def _derive_completed_owner_attribution(events, evidence, public_receipt):
    """Bind a normal completed dispatch to its public release/horizon receipt.

    Recovery receipts remain handled by ``_derive_native_owner_attribution``.
    This path accepts only the distinct normal-completion shape, and requires
    the exact dispatched program expiry plus verified release and readback.
    """
    action_call_id = evidence["action_call_id"]
    _, dispatch = _public_dispatch_event(events, action_call_id)
    action = public_receipt.get("action")
    if (type(action) is not dict or public_receipt.get("call_id") != action_call_id
            or action.get("status") != "completed"
            or action.get("release_confirmed") is not True):
        _fail("public result does not contain a confirmed completed action")
    operation_id = action.get("operation_id")
    generation = action.get("target_generation")
    if (dispatch.get("call_id") != action_call_id
            or dispatch.get("operation_id") != operation_id
            or dispatch.get("target_generation") != generation
            or not isinstance(operation_id, str) or not operation_id
            or not isinstance(generation, str) or not _HASH.fullmatch(generation)):
        _fail("completed public result does not match the recorded dispatch identity")

    program = dispatch.get("standard_program")
    authority = program.get("authority") if type(program) is dict else None
    expiry = authority.get("expires_at_ns") if type(authority) is dict else None
    custody = action.get("completion_custody")
    if (type(expiry) is not int or expiry < 0 or type(custody) is not dict
            or custody.get("operation_id") != operation_id
            or custody.get("target_generation") != generation
            or custody.get("phase") != "completed"
            or custody.get("status") != "completed"
            or custody.get("deadline_ns") != expiry
            or custody.get("release_confirmed") is not True
            or custody.get("completion_readback_outcome") != "verified"):
        _fail("completed owner custody is incomplete or belongs to another authority")

    release = custody.get("completion_release_receipt")
    if (type(release) is not dict or release.get("verified") is not True
            or any(release.get(key) != [] for key in (
                "keys_down", "buttons_down", "keys_unknown", "buttons_unknown",
                "release_errors"))):
        _fail("completed owner receipt lacks an independently verified neutral release")
    release_ns = release.get("monotonic_ns")
    readback = custody.get("completion_readback")
    if (type(readback) is not dict
            or readback.get("operation_id") != operation_id
            or readback.get("target_generation") != generation
            or readback.get("neutral") is not True
            or readback.get("late_input_horizon_verified") is not True):
        _fail("completed owner receipt lacks a generation-bound neutral horizon")
    horizon_ns = readback.get("late_input_horizon_ns")
    start_ns = readback.get("late_input_observation_start_monotonic_ns",
                             readback.get("late_input_observation_start_ns"))
    end_ns = readback.get("late_input_observation_end_monotonic_ns",
                           readback.get("late_input_observation_end_ns"))
    count = readback.get("late_input_observation_count")
    max_gap_ns = readback.get("late_input_max_observed_gap_ns")
    allowed_gap_ns = readback.get("late_input_max_sample_gap_ns")
    if (type(release_ns) is not int or release_ns < 0
            or type(horizon_ns) is not int or horizon_ns <= 0
            or type(start_ns) is not int or start_ns < release_ns
            or type(end_ns) is not int or end_ns < start_ns
            or end_ns - release_ns < horizon_ns
            or type(count) is not int or count < 2
            or type(max_gap_ns) is not int or max_gap_ns < 0
            or type(allowed_gap_ns) is not int or allowed_gap_ns <= 0
            or max_gap_ns > allowed_gap_ns):
        _fail("completed neutral horizon is missing or unverified")

    attribution_input = {
        "effect_observed_ns": evidence["effect_observed_ns"],
        "authority_expiry_ns": expiry,
        "release_received_ns": release_ns,
        "horizon_end_ns": end_ns,
    }
    attribution = adjudicate_effect(task_success=None, **attribution_input)
    binding = {
        "schema": "agent-interface/native-owner-lifecycle-binding-v1",
        "lookup_tool_call_id": evidence["lookup_tool_call_id"],
        "action_call_id": action_call_id,
        "action_operation_id": operation_id,
        "target_generation": generation,
        "effect_observed_ns": evidence["effect_observed_ns"],
        "authority_expiry_ns": expiry,
        "release_received_ns": release_ns,
        "horizon_ns": horizon_ns,
        "horizon_observation_count": count,
        "horizon_start_ns": start_ns,
        "horizon_end_ns": end_ns,
        "release_confirmed": True,
        "horizon_verified": True,
        "effect_timing": attribution["effect_timing"],
    }
    return attribution_input, binding


def adapt_measured_run(measured: object, *, receipt_root: str | Path,
                       receipt_path: str) -> dict:
    """Verify the effect receipt and return a newly validated adapted run.

    An interval qualifies only when both endpoints are inside the same
    authority band. Unknown, overlapping, or post-horizon intervals are
    conservatively ineligible; factual final-state success is preserved.
    """
    validate_measured_run(measured)
    receipt, digest, receipt_bytes = _read_receipt(
        Path(receipt_root), receipt_path)
    run = copy.deepcopy(measured)
    ledger = run["task_ledger"]
    measurement = run["measurement"]
    events = ledger["events"]
    scores = [event for event in events if event["kind"] == "task_score"]
    if len(scores) != 1 or scores[0]["independent"] is not True:
        _fail("effect receipt requires one independent terminal task score")
    score = scores[0]
    task_id = ledger["task"]["task_id"]
    if (receipt["task_id"] != task_id or receipt["scorer_id"] != score["scorer_id"] or
            receipt["scorer_sha256"] != ledger["task"]["scorer_sha256"]):
        _fail("effect receipt task or scorer identity differs from measured run")
    for key in ("task_success", "state_sha256"):
        if receipt[key] != score[key]:
            _fail("effect receipt score differs from terminal independent score")
    if (type(receipt["task_success"]) is not bool or
            not isinstance(receipt["state_sha256"], str) or
            not _HASH.fullmatch(receipt["state_sha256"])):
        _fail("effect receipt final score fields are malformed")
    if (type(receipt["before_task_success"]) is not bool or
            not isinstance(receipt["before_state_sha256"], str) or
            not _HASH.fullmatch(receipt["before_state_sha256"])):
        _fail("effect receipt baseline state is malformed")
    if receipt["task_success"] and (receipt["before_task_success"] or
            receipt["state_sha256"] == receipt["before_state_sha256"]):
        _fail("successful final state must be independently shown to differ from an unsuccessful baseline")

    owner_evidence = {
        "lookup_tool_call_id": receipt["lookup_tool_call_id"],
        "action_call_id": receipt["action_call_id"],
        "effect_observed_ns": None,
    }
    lookup_events = [event for event in events if event.get("kind") == "tool_call"
                     and event.get("call_id") == receipt["lookup_tool_call_id"]]
    if len(lookup_events) != 1:
        _fail("effect receipt must bind one exact public results lookup")
    owner_public = _tool_body(lookup_events[0])
    if owner_public.get("cancellation") is None:
        attribution_input, binding = _derive_completed_owner_attribution(
            events, owner_evidence, owner_public)
    else:
        attribution_input, binding = _derive_native_owner_attribution(
            events, owner_evidence)
    action_event, action_body = _public_dispatch_event(
        events, receipt["action_call_id"])
    operation_id = action_body.get("operation_id")
    generation = action_body.get("target_generation")
    if (receipt["action_operation_id"] != operation_id or
            receipt["target_generation"] != generation or
            not isinstance(receipt["target_generation"], str) or
            not _HASH.fullmatch(receipt["target_generation"])):
        _fail("effect receipt is stale or belongs to another action generation")

    observations = measurement["local_observations"]
    calls = {event["call_id"]: event for event in events if event["kind"] == "tool_call"}
    before = _capture(receipt["before_observation"], observations, calls,
                      receipt["target_generation"])
    after = _capture(receipt["after_observation"], observations, calls,
                     receipt["target_generation"])
    lookup_event = next(event for event in events
                        if event.get("call_id") == receipt["lookup_tool_call_id"])
    before_call = calls[before["tool_call_id"]]
    after_call = calls[after["tool_call_id"]]
    before_end = before["capture_ended_ns"]
    after_start = after["capture_started_ns"]
    same_capture_kind = before["capture_kind"] == after["capture_kind"]
    source_order_ok = (before["capture_kind"] == "public" or
                       before["source_sequence"] < after["source_sequence"])
    if (not same_capture_kind or before_end >= after_start or not source_order_ok or
            before_call["seq"] >= action_event["seq"] or
            action_event["seq"] >= lookup_event["seq"] or
            lookup_event["seq"] >= after_call["seq"] or
            before_end > action_event["started_ns"] or
            after_start < lookup_event["ended_ns"]):
        _fail("effect captures must bracket the same action and its public result")

    interval = receipt["effect_interval_ns"]
    effect_ns = None
    timing_status = "unknown"
    if interval is not None:
        if type(interval) is not dict or set(interval) != {"lower_ns", "upper_ns"}:
            _fail("effect interval requires exact lower and upper bounds")
        lower, upper = interval["lower_ns"], interval["upper_ns"]
        if (type(lower) is not int or type(upper) is not int or
                lower < before_end or upper > after_start or lower > upper):
            _fail("effect interval must be ordered inside its capture bracket")
        bands = lambda t: ("within_authority" if t <= binding["authority_expiry_ns"] else
                           "after_authority_before_release" if t <= binding["release_received_ns"] else
                           "after_release_within_horizon" if t <= binding["horizon_end_ns"] else
                           "after_release_horizon")
        low_band, high_band = bands(lower), bands(upper)
        if low_band == high_band:
            effect_ns = upper
            timing_status = low_band
        else:
            timing_status = "ambiguous_boundary"

    attribution_input["effect_observed_ns"] = effect_ns
    attribution = adjudicate_effect(task_success=score["task_success"], **attribution_input)
    measurement["effect_attribution"] = attribution_input
    binding["effect_observed_ns"] = effect_ns
    binding["effect_timing"] = attribution["effect_timing"]
    ledger["native_owner_binding"] = binding
    relative_to_ledger = f"raw/effect-score-{digest}.json"
    raw_target = Path(receipt_root).resolve() / relative_to_ledger
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    if raw_target.exists():
        if raw_target.read_bytes() != receipt_bytes:
            _fail("retained receipt destination already contains different bytes")
    else:
        raw_target.write_bytes(receipt_bytes)
    ledger["raw_refs"].append({"path": relative_to_ledger, "sha256": digest})
    validate_measured_run(run)
    summary = validate_measured_run(run)
    return {"measured_run": run, "receipt_sha256": digest,
            "timing_status": timing_status,
            "factual_task_success": summary["factual_task_success"],
            "eligible_task_success": summary["task_success"],
            "authority_binding": binding}
