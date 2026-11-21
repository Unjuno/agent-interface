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
from recorded_comparison_adapter_v1 import _derive_native_owner_attribution

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


def _capture(value, observations, calls):
    fields = {"tool_call_id", "source_sequence", "captured_ns", "image_sha256"}
    if type(value) is not dict or set(value) != fields:
        _fail("capture reference fields do not match local observation contract")
    matches = [item for item in observations if item == value]
    call = calls.get(value["tool_call_id"])
    if len(matches) != 1 or call is None:
        _fail("capture reference is not a unique retained local observation")
    if type(value["captured_ns"]) is not int or type(value["source_sequence"]) is not int:
        _fail("capture time and source sequence must be integers")
    return value


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

    attribution_input, binding = _derive_native_owner_attribution(events, {
        "lookup_tool_call_id": receipt["lookup_tool_call_id"],
        "action_call_id": receipt["action_call_id"],
        "effect_observed_ns": None,
    })
    action_event = next(event for event in events if event.get("call_id") == receipt["action_call_id"])
    action_body = json.loads(action_event["result"]["result"]["content"][0]["text"])
    operation_id = action_body.get("operation_id")
    generation = action_body.get("target_generation")
    if (receipt["action_operation_id"] != operation_id or
            receipt["target_generation"] != generation or
            not isinstance(receipt["target_generation"], str) or
            not _HASH.fullmatch(receipt["target_generation"])):
        _fail("effect receipt is stale or belongs to another action generation")

    observations = measurement["local_observations"]
    calls = {event["call_id"]: event for event in events if event["kind"] == "tool_call"}
    before = _capture(receipt["before_observation"], observations, calls)
    after = _capture(receipt["after_observation"], observations, calls)
    lookup_event = next(event for event in events
                        if event.get("call_id") == receipt["lookup_tool_call_id"])
    if (before["captured_ns"] >= after["captured_ns"] or
            before["source_sequence"] >= after["source_sequence"] or
            calls[before["tool_call_id"]]["seq"] >= action_event["seq"] or
            action_event["seq"] >= lookup_event["seq"] or
            lookup_event["seq"] >= calls[after["tool_call_id"]]["seq"] or
            before["captured_ns"] > action_event["started_ns"] or
            after["captured_ns"] < lookup_event["ended_ns"]):
        _fail("effect captures must bracket the same action and its public result")
    if before["captured_ns"] < calls[before["tool_call_id"]]["started_ns"] or after[
            "captured_ns"] > calls[after["tool_call_id"]]["ended_ns"]:
        _fail("effect capture lies outside its public observation call")

    interval = receipt["effect_interval_ns"]
    effect_ns = None
    timing_status = "unknown"
    if interval is not None:
        if type(interval) is not dict or set(interval) != {"lower_ns", "upper_ns"}:
            _fail("effect interval requires exact lower and upper bounds")
        lower, upper = interval["lower_ns"], interval["upper_ns"]
        if (type(lower) is not int or type(upper) is not int or
                lower < before["captured_ns"] or upper > after["captured_ns"] or lower > upper):
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
