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
    if type(measurement) is not dict or set(measurement) != _MEASUREMENT_KEYS:
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

    task_ledger = {
        **ledger_metadata,
        "raw_refs": raw_refs,
        "events": projected,
    }
    measured = {"task_ledger": task_ledger, "measurement": measurement}
    validate_measured_run(measured)
    return measured
