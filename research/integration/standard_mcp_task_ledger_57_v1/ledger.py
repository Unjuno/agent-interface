"""Strict summary rules for a single standard-MCP comparison task."""

import re
from pathlib import PurePosixPath


class LedgerValidationError(ValueError):
    pass


_HASH = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_ATTEMPT_STATUSES = {
    "completed", "failed", "timeout", "cancelled", "refused", "malformed",
    "abstained",
}


def _is_int(value):
    return type(value) is int and value >= 0


def _interval(row):
    if not _is_int(row.get("started_ns")) or not _is_int(row.get("ended_ns")):
        raise LedgerValidationError("event needs nonnegative integer monotonic times")
    if row["ended_ns"] < row["started_ns"]:
        raise LedgerValidationError("event ended before it started")


def _validate_usage(usage):
    if not isinstance(usage, dict):
        raise LedgerValidationError("model attempt needs a usage record")
    status = usage.get("status")
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    for name, value in (("input_tokens", input_tokens),
                        ("output_tokens", output_tokens)):
        if value is not None and not _is_int(value):
            raise LedgerValidationError(f"{name} must be a nonnegative integer or null")
    if status == "reported" and (input_tokens is None or output_tokens is None):
        raise LedgerValidationError("reported usage requires both token counts")
    if status == "partial" and input_tokens is None and output_tokens is None:
        raise LedgerValidationError("partial usage requires at least one token count")
    if status == "unavailable" and (input_tokens is not None or output_tokens is not None):
        raise LedgerValidationError("unavailable usage cannot contain token counts")
    if status not in ("reported", "partial", "unavailable"):
        raise LedgerValidationError("unknown usage status")
    return status, input_tokens, output_tokens


def summarize(events):
    """Validate linked all-attempt events and return conservative task totals.

    Missing usage makes the whole route total unknown. A runtime result field
    named ``task_success`` is never accepted as an independent task score.
    """
    if not isinstance(events, list):
        raise LedgerValidationError("events must be a list")

    attempt_ids = set()
    call_ids = set()
    attempts = []
    independent_score = None
    previous_started = -1

    for expected_seq, row in enumerate(events, start=1):
        if not isinstance(row, dict):
            raise LedgerValidationError("each event must be an object")
        if row.get("seq") != expected_seq or type(row.get("seq")) is not int:
            raise LedgerValidationError("event sequence must be contiguous from one")
        _interval(row)
        if row["started_ns"] < previous_started:
            raise LedgerValidationError("events must be ordered by monotonic start time")
        previous_started = row["started_ns"]

        kind = row.get("kind")
        if kind == "model_attempt":
            attempt_id = row.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise LedgerValidationError("model attempt needs an id")
            if attempt_id in attempt_ids:
                raise LedgerValidationError("duplicate model attempt id")
            if row.get("status") not in _ATTEMPT_STATUSES:
                raise LedgerValidationError("unknown model attempt status")
            attempt_ids.add(attempt_id)
            attempts.append(row)
            _validate_usage(row.get("usage"))
        elif kind == "tool_call":
            call_id = row.get("call_id")
            if not isinstance(call_id, str) or not call_id or call_id in call_ids:
                raise LedgerValidationError("tool call id is missing or duplicated")
            call_ids.add(call_id)
            if not isinstance(row.get("method"), str) or not row["method"]:
                raise LedgerValidationError("tool call needs a method name")
            if not isinstance(row.get("result"), dict):
                raise LedgerValidationError("tool call needs its retained result object")
            response_status = row.get("response_status")
            if response_status is not None and response_status not in (
                    "matched", "unavailable"):
                raise LedgerValidationError(
                    "tool response bytes do not match the retained result")
            attempt_id = row.get("model_attempt_id")
            if attempt_id is not None and attempt_id not in attempt_ids:
                raise LedgerValidationError("tool call references an unrecorded model attempt")
        elif kind == "task_score":
            if expected_seq != len(events):
                raise LedgerValidationError("independent task score must be terminal")
            if independent_score is not None:
                raise LedgerValidationError("multiple terminal task scores are ambiguous")
            if row.get("independent") is not True:
                raise LedgerValidationError("task score must come from an independent oracle")
            if not isinstance(row.get("scorer_id"), str) or not row["scorer_id"]:
                raise LedgerValidationError("independent score needs a scorer id")
            if not isinstance(row.get("state_sha256"), str) or not _HASH.fullmatch(
                    row["state_sha256"]):
                raise LedgerValidationError("independent score needs a state digest")
            if row.get("task_success") not in (True, False, None) or type(
                    row.get("task_success")) not in (bool, type(None)):
                raise LedgerValidationError("task score must be true, false, or unknown")
            independent_score = row
        else:
            raise LedgerValidationError("unknown ledger event kind")

    usage_rows = [_validate_usage(row["usage"]) for row in attempts]
    if not attempts:
        usage_status, input_total, output_total = "not_applicable", 0, 0
    elif all(status == "reported" for status, _, _ in usage_rows):
        usage_status = "complete"
        input_total = sum(input for _, input, _ in usage_rows)
        output_total = sum(output for _, _, output in usage_rows)
    else:
        usage_status, input_total, output_total = "incomplete", None, None

    return {
        "model_attempt_count": len(attempts),
        "tool_call_count": len(call_ids),
        "input_tokens": input_total,
        "output_tokens": output_total,
        "usage_status": usage_status,
        "independent_score_status": (
            "missing" if independent_score is None else "recorded"),
        "task_success": (
            None if independent_score is None else independent_score["task_success"]),
    }


def validate_record(record):
    """Validate the frozen conditions and provenance envelope for one task."""
    if not isinstance(record, dict):
        raise LedgerValidationError("task ledger must be an object")
    if record.get("schema") != "agent-interface/standard-mcp-task-ledger-v1":
        raise LedgerValidationError("unsupported task-ledger schema")
    if not isinstance(record.get("run_id"), str) or not record["run_id"]:
        raise LedgerValidationError("run id is required")

    comparison = record.get("comparison")
    if not isinstance(comparison, dict):
        raise LedgerValidationError("comparison conditions are required")
    if not isinstance(comparison.get("arm"), str) or not comparison["arm"]:
        raise LedgerValidationError("comparison arm is required")
    for name in ("block", "order"):
        value = comparison.get(name)
        if type(value) is not int or value < 1:
            raise LedgerValidationError(f"comparison {name} must be a positive integer")
    if not isinstance(comparison.get("task_seed"), str) or not comparison["task_seed"]:
        raise LedgerValidationError("task seed is required")

    task = record.get("task")
    if not isinstance(task, dict) or not isinstance(task.get("task_id"), str) or not task[
            "task_id"]:
        raise LedgerValidationError("task identity is required")
    for name in ("fixture_sha256", "scorer_sha256"):
        if not isinstance(task.get(name), str) or not _HASH.fullmatch(task[name]):
            raise LedgerValidationError(f"task {name} is required")

    source = record.get("source")
    if not isinstance(source, dict):
        raise LedgerValidationError("source pins are required")
    if not isinstance(source.get("commit"), str) or not _COMMIT.fullmatch(
            source["commit"]):
        raise LedgerValidationError("source commit must be a full hexadecimal id")
    if not isinstance(source.get("route_sha256"), str) or not _HASH.fullmatch(
            source["route_sha256"]):
        raise LedgerValidationError("route source digest is required")
    if not isinstance(record.get("environment_sha256"), str) or not _HASH.fullmatch(
            record["environment_sha256"]):
        raise LedgerValidationError("environment digest is required")

    model = record.get("model")
    if model is not None:
        if not isinstance(model, dict):
            raise LedgerValidationError("model condition must be an object or null")
        for name in ("id", "effort"):
            if not isinstance(model.get(name), str) or not model[name]:
                raise LedgerValidationError(f"model {name} is required")
        if not isinstance(model.get("request_config_sha256"), str) or not _HASH.fullmatch(
                model["request_config_sha256"]):
            raise LedgerValidationError("model request configuration digest is required")

    raw_refs = record.get("raw_refs")
    if not isinstance(raw_refs, list) or not raw_refs:
        raise LedgerValidationError("at least one raw-evidence reference is required")
    paths = set()
    for raw_ref in raw_refs:
        if not isinstance(raw_ref, dict):
            raise LedgerValidationError("raw reference must be an object")
        path = raw_ref.get("path")
        if not isinstance(path, str) or not path or "\\" in path:
            raise LedgerValidationError("raw path must be a relative POSIX path")
        parsed = PurePosixPath(path)
        if (parsed.is_absolute() or not parsed.parts or parsed.as_posix() != path
                or any(part in ("", ".", "..") for part in parsed.parts)):
            raise LedgerValidationError("raw path must be a normalized relative file path")
        if path in paths:
            raise LedgerValidationError("raw path is duplicated")
        paths.add(path)
        if not isinstance(raw_ref.get("sha256"), str) or not _HASH.fullmatch(
                raw_ref["sha256"]):
            raise LedgerValidationError("raw reference digest is required")

    events = record.get("events")
    summary = summarize(events)
    if model is None and summary["model_attempt_count"]:
        raise LedgerValidationError("model attempts require a frozen model condition")
    summary.update({
        "run_id": record["run_id"],
        "arm": comparison["arm"],
        "block": comparison["block"],
        "order": comparison["order"],
        "task_id": task["task_id"],
        "raw_ref_count": len(raw_refs),
    })
    return summary
