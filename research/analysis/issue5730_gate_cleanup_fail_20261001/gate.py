"""CPU-only fail-closed launch and artifact-publication gate for Issue #5730."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Callable


class Stop(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_prerequisites(inventory_result, source_manifest, expected_manifest_sha256):
    if not isinstance(inventory_result, dict):
        raise Stop("STOP_INVENTORY_RESULT_MISSING_OR_WRONG_TYPE")
    if type(inventory_result.get("returncode")) is not int or inventory_result["returncode"] != 0:
        raise Stop("STOP_INVENTORY_COMMAND_FAILED")
    stdout = inventory_result.get("stdout")
    if not isinstance(stdout, bytes) or not stdout.strip():
        raise Stop("STOP_INVENTORY_OUTPUT_EMPTY_OR_MISSING")
    try:
        inventory = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Stop("STOP_INVENTORY_OUTPUT_MALFORMED") from None
    if not isinstance(inventory, dict) or not isinstance(inventory.get("compute_processes"), list):
        raise Stop("STOP_INVENTORY_SCHEMA_INVALID")

    if not isinstance(source_manifest, dict):
        raise Stop("STOP_SOURCE_IDENTITY_MISSING")
    commit = source_manifest.get("commit")
    files = source_manifest.get("files")
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise Stop("STOP_SOURCE_IDENTITY_INCOMPLETE")
    if not isinstance(files, dict) or not files:
        raise Stop("STOP_SOURCE_IDENTITY_INCOMPLETE")
    canonical = json.dumps(source_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if _sha256(canonical) != expected_manifest_sha256:
        raise Stop("STOP_SOURCE_IDENTITY_CHANGED")
    for name, digest in files.items():
        if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
            raise Stop("STOP_SOURCE_IDENTITY_INCOMPLETE")
        if any(c not in "0123456789abcdef" for c in digest):
            raise Stop("STOP_SOURCE_IDENTITY_INCOMPLETE")
    return inventory


def _publish_complete_json(output_path: Path, payload: bytes):
    try:
        text = payload.decode("utf-8")
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("top-level JSON must be an object")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise Stop("STOP_OUTPUT_MISSING_OR_TRUNCATED") from None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp", dir=output_path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        written = Path(temp_name).read_bytes()
        if written != payload or _sha256(written) != _sha256(payload):
            raise Stop("STOP_POSTWRITE_DIGEST_MISMATCH")
        os.replace(temp_name, output_path)
        final = output_path.read_bytes()
        if final != payload or _sha256(final) != _sha256(payload):
            raise Stop("STOP_POSTWRITE_DIGEST_MISMATCH")
        return _sha256(final)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def run_gated(inventory_result, source_manifest, expected_manifest_sha256,
              candidate: Callable[[], dict], output_path: Path):
    """Invoke candidate only after all gates; never score invalid candidate output."""
    try:
        validate_prerequisites(inventory_result, source_manifest, expected_manifest_sha256)
    except Stop as stop:
        return {"status": stop.reason, "candidate_invocations": 0,
                "scientific_result": "NOT_EVALUATED", "raw_sha256": None}

    try:
        result = candidate()
    except Exception as exc:  # fixture captures candidate boundary failures as STOP
        return {"status": "STOP_CANDIDATE_EXCEPTION", "candidate_invocations": 1,
                "exception_type": type(exc).__name__, "scientific_result": "NOT_EVALUATED",
                "raw_sha256": None}
    if not isinstance(result, dict) or type(result.get("returncode")) is not int:
        return {"status": "STOP_CANDIDATE_RESULT_INVALID", "candidate_invocations": 1,
                "scientific_result": "NOT_EVALUATED", "raw_sha256": None}
    if result["returncode"] != 0:
        return {"status": "STOP_CANDIDATE_NONZERO", "candidate_invocations": 1,
                "scientific_result": "NOT_EVALUATED", "raw_sha256": None}
    payload = result.get("stdout")
    if not isinstance(payload, bytes) or not payload:
        return {"status": "STOP_OUTPUT_MISSING_OR_TRUNCATED", "candidate_invocations": 1,
                "scientific_result": "NOT_EVALUATED", "raw_sha256": None}
    try:
        digest = _publish_complete_json(output_path, payload)
    except Stop as stop:
        return {"status": stop.reason, "candidate_invocations": 1,
                "scientific_result": "NOT_EVALUATED", "raw_sha256": None}
    return {"status": "ARTIFACT_PUBLISHED", "candidate_invocations": 1,
            "scientific_result": "READY_FOR_INDEPENDENT_AUDIT", "raw_sha256": digest}
