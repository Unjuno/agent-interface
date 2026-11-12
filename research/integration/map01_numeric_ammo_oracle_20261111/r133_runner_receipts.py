"""Small, offline-tested result adapters for the retained R133 runner defect."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .input_boundary import audit_expiry_key_release


def public_body(reply):
    """Accept an already-decoded public row or a one-text MCP result envelope."""
    if type(reply) is dict:
        return reply
    content = getattr(reply, "content", None)
    if not isinstance(content, list):
        raise ValueError("public result is neither a mapping nor an MCP envelope")
    texts = [item.text for item in content
             if getattr(item, "type", None) == "text"
             and isinstance(getattr(item, "text", None), str)]
    if len(texts) != 1:
        raise ValueError("expected exactly one public JSON text row")
    value = json.loads(texts[0])
    if type(value) is not dict:
        raise ValueError("public JSON row must be an object")
    return value


def submitted_expiry_ns(submission_path) -> int:
    """Read the effective deadline from the serialized dispatch, never template."""
    value = json.loads(Path(submission_path).read_text(encoding="utf-8"))
    program = value.get("program") if type(value) is dict else None
    authority = program.get("authority") if type(program) is dict else None
    expiry = authority.get("expires_at_ns") if type(authority) is dict else None
    if type(expiry) is not int or expiry <= 0:
        raise ValueError("serialized dispatch expiry is missing or invalid")
    return expiry


def resolve_and_persist_terminal(call_id, resolve, receipt_path, raw_path,
                                 normalize=public_body):
    """Persist the exact terminal row before running fallible normalization.

    The resolver owns writing its receipt atomically. This adapter independently
    checks the exact call join, creates a non-overwriting raw-row copy, and only
    then invokes the supplied normalizer.
    """
    if type(call_id) is not str or not call_id or not callable(resolve):
        raise ValueError("exact call ID and resolver are required")
    if not callable(normalize):
        raise ValueError("normalizer must be callable")
    resolved = resolve()
    receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    if (type(receipt) is not dict or receipt.get("call_id") != call_id
            or receipt.get("terminal") is not True):
        raise ValueError("resolver receipt is not terminal for the exact call")
    raw = receipt.get("latest_result")
    if type(raw) is not dict or raw.get("call_id") != call_id:
        raise ValueError("resolver receipt lacks the exact raw terminal row")
    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(raw, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with raw_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return resolved, normalize(resolved)


def runner_receipt_dry_run(call_id, resolve, receipt_path, raw_path,
                           submission_path, samples, boundary_path,
                           normalize=public_body):
    """Exercise the runner callback + raw receipt + expiry audit without I/O tools.

    Boundary and final sampled W state are written even if receipt normalization
    fails, matching the runner's exception-path evidence contract.
    """
    normalized = None
    error_type = None
    try:
        _, normalized = resolve_and_persist_terminal(call_id, resolve,
            receipt_path, raw_path, normalize=normalize)
    except Exception as error:
        error_type = type(error).__name__
    deadline = submitted_expiry_ns(submission_path)
    boundary = audit_expiry_key_release(samples, deadline)
    final_sample = samples[-1] if samples else None
    payload = {"call_id": call_id, "status": "failed" if error_type else "terminal",
        "error_type": error_type, "serialized_expiry_monotonic_ns": deadline,
        "expiry_boundary": boundary, "final_w_sample": final_sample,
        "raw_terminal_persisted": Path(raw_path).is_file(),
        "normalized_result": normalized}
    boundary_path = Path(boundary_path)
    boundary_path.parent.mkdir(parents=True, exist_ok=True)
    with boundary_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, sort_keys=True, indent=2,
            allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return payload
