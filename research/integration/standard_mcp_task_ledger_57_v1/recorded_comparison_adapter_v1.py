"""Project a reconciled caller journal into the matched comparison contract.

This offline adapter verifies retained recorder files and journal structure. It
does not prove provider-side exhaustiveness or the truth of supplied owner,
effect, scorer, model, environment, or comparison pins.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath

from comparison_measurement_v1 import validate_measured_run
from effect_attribution_v1 import adjudicate_effect
from ledger import LedgerValidationError


_HASH = re.compile(r"^[0-9a-f]{64}$")
_METADATA_KEYS = {
    "schema", "run_id", "comparison", "task", "source",
    "environment_sha256", "model",
}
_MEASUREMENT_KEYS = {
    "started_ns", "ended_ns", "elapsed_ns", "phases",
    "model_delivered_images", "local_observations", "effect_attribution",
}
_NATIVE_MEASUREMENT_KEYS = (_MEASUREMENT_KEYS - {"effect_attribution"}) | {
    "native_owner_evidence",
}


def _fail(message: str) -> None:
    raise LedgerValidationError(message)


def _verified_raw_refs(root: Path, refs: object) -> list[dict]:
    if type(refs) is not list or not refs:
        _fail("complete caller receipt needs retained raw references")
    resolved_root = root.resolve(strict=True)
    seen: dict[str, str] = {}
    verified = []
    for ref in refs:
        if type(ref) is not dict or set(ref) != {"path", "sha256"}:
            _fail("raw reference fields do not match the recorder contract")
        relative, digest = ref["path"], ref["sha256"]
        if (not isinstance(relative, str) or "\\" in relative
                or not isinstance(digest, str) or not _HASH.fullmatch(digest)):
            _fail("raw reference path or digest is malformed")
        parsed = PurePosixPath(relative)
        if (parsed.is_absolute() or not parsed.parts or parsed.as_posix() != relative
                or any(part in ("", ".", "..") for part in parsed.parts)):
            _fail("raw reference path must stay inside its normalized run root")
        if relative in seen:
            if seen[relative] != digest:
                _fail("one raw path cannot claim multiple SHA-256 digests")
            continue
        seen[relative] = digest
        candidate = (resolved_root / Path(*parsed.parts)).resolve(strict=True)
        if not candidate.is_relative_to(resolved_root) or not candidate.is_file():
            _fail("raw reference escapes the run root or is not a file")
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != digest:
            _fail("retained raw reference digest does not match its file")
        verified.append({"path": relative, "sha256": digest})
    return verified


def _tool_body(event: dict) -> dict:
    envelope = event.get("result")
    if (type(envelope) is not dict or envelope.get("status") != "returned"
            or envelope.get("tool") != event.get("method")):
        _fail("native owner lookup lacks a returned public MCP envelope")
    result = envelope.get("result")
    content = result.get("content") if type(result) is dict else None
    if type(content) is not list:
        _fail("native owner lookup response has no public text content")
    text_rows = [item.get("text") for item in content
                 if type(item) is dict and item.get("type") == "text"
                 and isinstance(item.get("text"), str)]
    if len(text_rows) != 1:
        _fail("native owner lookup needs one unambiguous public receipt")
    import json
    try:
        body = json.loads(text_rows[0])
    except (TypeError, ValueError) as exc:
        raise LedgerValidationError(
            "native owner public receipt is malformed") from exc
    if type(body) is not dict:
        _fail("native owner public receipt must be an object")
    return body


def _derive_native_owner_attribution(events: list, evidence: object):
    required = {"lookup_tool_call_id", "action_call_id", "effect_observed_ns"}
    if type(evidence) is not dict or set(evidence) != required:
        _fail("native owner evidence needs exact lookup, action, and effect fields")
    effect_ns = evidence["effect_observed_ns"]
    if effect_ns is not None and (type(effect_ns) is not int or effect_ns < 0):
        _fail("native effect time must be a nonnegative integer or null")
    lookup_id = evidence["lookup_tool_call_id"]
    action_call_id = evidence["action_call_id"]
    if (not isinstance(lookup_id, str) or not lookup_id or
            not isinstance(action_call_id, str) or not action_call_id):
        _fail("native owner lookup and action call IDs are required")
    matches = [event for event in events if event.get("kind") == "tool_call"
               and event.get("call_id") == lookup_id]
    if len(matches) != 1 or matches[0].get("method") != "interface_results":
        _fail("native owner evidence must bind one recorded interface_results call")
    body = _tool_body(matches[0])
    if body.get("call_id") != action_call_id:
        _fail("public owner receipt belongs to a different action call")
    action_matches = [event for event in events
                      if event.get("kind") == "tool_call"
                      and event.get("call_id") == action_call_id]
    if (len(action_matches) != 1 or
            action_matches[0].get("method") != "interface_dispatch"):
        _fail("native owner evidence must bind one recorded interface_dispatch call")
    dispatch = _tool_body(action_matches[0])
    action = body.get("action")
    cancellation = body.get("cancellation")
    if type(action) is not dict or type(cancellation) is not dict:
        _fail("public owner receipt lacks action or cancellation identity")
    operation_id = action.get("operation_id")
    generation = action.get("target_generation")
    if (dispatch.get("call_id") != action_call_id or
            dispatch.get("operation_id") != operation_id or
            dispatch.get("target_generation") != generation):
        _fail("public owner receipt does not match the recorded dispatch identity")
    owner = cancellation.get("result")
    if (not isinstance(operation_id, str) or not operation_id or
            not isinstance(generation, str) or not _HASH.fullmatch(generation) or
            type(owner) is not dict):
        _fail("public owner receipt lacks operation/generation-bound result")
    if (cancellation.get("action_operation_id") != operation_id or
            cancellation.get("target_generation") != generation or
            cancellation.get("status") != "recovered" or
            cancellation.get("release_confirmed") is not True or
            owner.get("operation_id") != operation_id or
            owner.get("target_generation") != generation or
            owner.get("phase") != "recovered" or
            owner.get("release_confirmed") is not True):
        _fail("cancellation receipt does not bind a confirmed recovery to the action")
    deadline = owner.get("deadline_ns")
    release_ns = owner.get("late_input_release_received_ns")
    horizon_ns = owner.get("late_input_horizon_ns")
    horizon_start_ns = owner.get("late_input_observation_start_ns")
    horizon_end_ns = owner.get("late_input_observation_end_ns")
    count = owner.get("late_input_observation_count")
    max_gap_ns = owner.get("late_input_max_observed_gap_ns")
    allowed_gap_ns = owner.get("late_input_max_sample_gap_ns")
    if (owner.get("late_input_horizon_verified") is not True or
            type(deadline) is not int or deadline < 0 or
            type(release_ns) is not int or release_ns < deadline or
            type(horizon_ns) is not int or horizon_ns <= 0 or
            type(horizon_start_ns) is not int or horizon_start_ns < release_ns or
            type(horizon_end_ns) is not int or horizon_end_ns < horizon_start_ns or
            horizon_end_ns - release_ns < horizon_ns or
            type(count) is not int or count < 2 or
            type(max_gap_ns) is not int or max_gap_ns < 0 or
            type(allowed_gap_ns) is not int or allowed_gap_ns <= 0 or
            max_gap_ns > allowed_gap_ns):
        _fail("native release/horizon receipt is missing or unverified")
    attribution_input = {
        "effect_observed_ns": effect_ns,
        "authority_expiry_ns": deadline,
        "release_received_ns": release_ns,
        "horizon_end_ns": horizon_end_ns,
    }
    attribution = adjudicate_effect(
        task_success=None, **attribution_input)
    binding = {
        "schema": "agent-interface/native-owner-lifecycle-binding-v1",
        "lookup_tool_call_id": lookup_id,
        "action_call_id": action_call_id,
        "action_operation_id": operation_id,
        "target_generation": generation,
        "effect_observed_ns": effect_ns,
        "authority_expiry_ns": deadline,
        "release_received_ns": release_ns,
        "horizon_ns": horizon_ns,
        "horizon_observation_count": count,
        "horizon_start_ns": horizon_start_ns,
        "horizon_end_ns": horizon_end_ns,
        "release_confirmed": True,
        "horizon_verified": True,
        "effect_timing": attribution["effect_timing"],
    }
    return attribution_input, binding


def build_measured_run(receipt: object, *, recorder_root: str | Path,
                       ledger_metadata: object,
                       measurement: object) -> dict:
    """Build and validate one measured run from ProviderAttemptRecorder output.

    ``ledger_metadata`` is a frozen condition envelope containing exactly the
    schema/run/comparison/task/source/environment/model pins. ``measurement``
    supplies the contiguous full-lifecycle phases, delivered-image and local
    observation joins, plus an explicit effect-attribution envelope. Unknown
    effect timing must be represented as null, never guessed from capture time.
    """
    if type(receipt) is not dict or set(receipt) != {
            "complete", "events", "raw_refs", "unresolved_attempt_ids",
            "unresolved_tool_call_ids"}:
        _fail("caller receipt does not match the reconciled recorder schema")
    if (receipt["complete"] is not True or
            receipt["unresolved_attempt_ids"] != [] or
            receipt["unresolved_tool_call_ids"] != []):
        _fail("incomplete caller operations cannot enter a matched run")
    if type(ledger_metadata) is not dict or set(ledger_metadata) != _METADATA_KEYS:
        _fail("frozen comparison ledger metadata is incomplete or has unknown fields")
    if (type(measurement) is not dict or set(measurement) not in
            (_MEASUREMENT_KEYS, _NATIVE_MEASUREMENT_KEYS)):
        _fail("lifecycle, observation, image, and effect evidence are required")

    raw_refs = _verified_raw_refs(Path(recorder_root), receipt["raw_refs"])
    events = receipt["events"]
    if type(events) is not list or not events:
        _fail("caller receipt must contain a nonempty event list")
    top_level_refs = {(ref["path"], ref["sha256"]) for ref in raw_refs}
    recorder_root = Path(recorder_root)
    event_refs = set()
    projected = []
    for seq, event in enumerate(events, start=1):
        if type(event) is not dict or event.get("seq") != seq:
            _fail("caller receipt event sequence is not contiguous")
        refs = event.get("raw_refs")
        if type(refs) is not list or not refs:
            _fail("each caller event needs bound raw evidence")
        for ref in _verified_raw_refs(recorder_root, refs):
            event_refs.add((ref["path"], ref["sha256"]))
        kind = event.get("kind")
        common = {"seq", "kind", "started_ns", "ended_ns"}
        if kind == "model_attempt":
            required = common | {"attempt_id", "status", "usage"}
            if not required <= set(event) or event.get("response_status") not in (
                    "raw_retained", "unavailable"):
                _fail("provider attempt lacks a terminal/raw receipt")
            projected.append({key: event[key] for key in (
                "seq", "kind", "attempt_id", "status", "started_ns",
                "ended_ns", "usage")})
        elif kind == "tool_call":
            required = common | {"call_id", "model_attempt_id", "method", "result"}
            if (not required <= set(event) or
                    event.get("response_status") != "matched"):
                _fail("public MCP call lacks a matching retained response")
            projected.append({key: event[key] for key in (
                "seq", "kind", "call_id", "model_attempt_id", "method",
                "started_ns", "ended_ns", "result")})
        elif kind == "task_score":
            required = common | {"independent", "scorer_id", "task_success", "state_sha256"}
            if not required <= set(event):
                _fail("terminal independent score receipt is incomplete")
            projected.append({key: event[key] for key in (
                "seq", "kind", "independent", "scorer_id", "task_success",
                "state_sha256", "started_ns", "ended_ns")})
        else:
            _fail("caller receipt contains an unsupported event kind")

    if not event_refs <= top_level_refs:
        _fail("top-level raw references omit journal-bound event evidence")

    native_binding = None
    if "native_owner_evidence" in measurement:
        attribution, native_binding = _derive_native_owner_attribution(
            projected, measurement["native_owner_evidence"])
        normalized_measurement = {
            key: value for key, value in measurement.items()
            if key != "native_owner_evidence"}
        normalized_measurement["effect_attribution"] = attribution
    else:
        normalized_measurement = measurement
    task_ledger = {
        **ledger_metadata,
        "raw_refs": raw_refs,
        "events": projected,
    }
    if native_binding is not None:
        task_ledger["native_owner_binding"] = native_binding
    measured = {"task_ledger": task_ledger,
                "measurement": normalized_measurement}
    validate_measured_run(measured)
    return measured
