"""Fail-closed synthetic harness for GPU diagnostic publication tests.

This module contains no GPU, model, game, GUI, or container code. The runner
interface is dependency-injected so tests can prove that failed gates never
invoke a candidate.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Callable, Sequence


Runner = Callable[[Sequence[str], Path, Path], int]


@dataclass(frozen=True)
class GateResult:
    status: str
    scientific_result: str
    candidate_invocations: int
    audited: bool
    raw_sha256: str | None
    audit_errors: tuple[str, ...]
    receipt: dict


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def subprocess_runner(argv: Sequence[str], stdout_path: Path, stderr_path: Path) -> int:
    """Execute without buffering child output in memory or a tool response."""
    with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
        process = subprocess.Popen(list(argv), stdout=stdout_stream, stderr=stderr_stream, shell=False)
        return process.wait()


def _persist_stop(output_dir: Path, status: str, source_sha256: str | None) -> dict:
    receipt = {
        "schema": "gpu-diagnostic-receipt-v1",
        "status": status,
        "scientific_result": "NOT_EVALUATED",
        "candidate_exit_code": None,
        "source_sha256": source_sha256,
        "raw_sha256": None,
        "stderr_sha256": None,
    }
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True)
            _atomic_json(output_dir / "receipt.json", receipt)
        except OSError:
            pass
    return receipt


def execute(
    *,
    gpu_snapshot: str | None,
    compute_apps: Sequence[str] | None,
    gpu_query_exit: int,
    apps_query_exit: int,
    source_expected: str,
    source_path: Path,
    output_dir: Path,
    argv: Sequence[str],
    runner: Runner,
) -> GateResult:
    """Run a synthetic candidate only after inventory, identity, and path gates."""
    try:
        source_sha = _sha256(source_path.read_bytes()) if source_path.is_file() and not source_path.is_symlink() else None
    except OSError:
        source_sha = None
    stop: str | None = None
    if gpu_query_exit != 0 or apps_query_exit != 0:
        stop = "STOP_INVENTORY_QUERY_FAILED"
    elif not isinstance(gpu_snapshot, str) or not re.fullmatch(r"\s*0\s*%,\s*0\s*MiB\s*", gpu_snapshot):
        stop = "STOP_GPU_INVENTORY_INVALID"
    elif compute_apps is not None and any(not isinstance(row, str) for row in compute_apps):
        stop = "STOP_GPU_INVENTORY_INVALID"
    elif compute_apps is not None and any(row.strip() for row in compute_apps):
        stop = "STOP_COMPETING_PROCESS"
    elif not re.fullmatch(r"[0-9a-f]{64}", source_expected or "") or source_sha != source_expected:
        stop = "STOP_SOURCE_IDENTITY_MISMATCH"
    elif output_dir.exists():
        stop = "STOP_OUTPUT_PATH_NOT_EMPTY"

    if stop:
        receipt = _persist_stop(output_dir, stop, source_sha)
        return GateResult(stop, "NOT_EVALUATED", 0, False, None, (), receipt)

    try:
        output_dir.mkdir(parents=True)
    except OSError:
        receipt = _persist_stop(output_dir, "STOP_OUTPUT_CREATE_FAILED", source_sha)
        return GateResult("STOP_OUTPUT_CREATE_FAILED", "NOT_EVALUATED", 0, False, None, (), receipt)

    raw_path = output_dir / "candidate.stdout.json"
    stderr_path = output_dir / "candidate.stderr.bin"
    try:
        exit_code = runner(argv, raw_path, stderr_path)
    except Exception as exc:  # preserve a typed runner crash, never continue to audit
        exit_code = 127
        stderr_path.write_text(f"runner exception: {type(exc).__name__}: {exc}\n", encoding="utf-8")

    for path in (raw_path, stderr_path):
        if path.is_file():
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
    stderr_sha = _sha256(stderr_path.read_bytes()) if stderr_path.is_file() else None
    raw_bytes = raw_path.read_bytes() if raw_path.is_file() else None
    raw_sha = _sha256(raw_bytes) if raw_bytes is not None else None

    status = "CANDIDATE_ARTIFACT_VALID"
    if exit_code != 0:
        status = "STOP_CANDIDATE_NONZERO"
    elif raw_bytes is None:
        status = "STOP_RAW_MISSING"
    else:
        try:
            doc = json.loads(raw_bytes)
        except (UnicodeError, json.JSONDecodeError):
            doc = None
        if not isinstance(doc, dict) or doc.get("schema") != "gpu-diagnostic-raw-v1" or doc.get("complete") is not True or not isinstance(doc.get("rows"), list):
            status = "STOP_RAW_INVALID"

    # A raw digest is published only for a fully valid zero-exit artifact.
    published_raw_sha = raw_sha if status == "CANDIDATE_ARTIFACT_VALID" else None
    receipt = {
        "schema": "gpu-diagnostic-receipt-v1",
        "status": status,
        "scientific_result": "NOT_EVALUATED",
        "candidate_exit_code": exit_code,
        "source_sha256": source_sha,
        "raw_sha256": published_raw_sha,
        "stderr_sha256": stderr_sha,
    }
    try:
        _atomic_json(output_dir / "receipt.json", receipt)
    except OSError:
        return GateResult("STOP_RECEIPT_WRITE_FAILED", "NOT_EVALUATED", 1, False, None, ("receipt_write",), receipt)

    if status != "CANDIDATE_ARTIFACT_VALID":
        return GateResult(status, "NOT_EVALUATED", 1, False, None, (), receipt)

    auditor_path = Path(__file__).with_name("raw_auditor.py")
    try:
        auditor_stdout = output_dir / "auditor.stdout.json"
        auditor_stderr = output_dir / "auditor.stderr.bin"
        audit_exit = subprocess_runner(
            [sys.executable, "-B", str(auditor_path), str(raw_path), str(output_dir / "receipt.json")],
            auditor_stdout,
            auditor_stderr,
        )
        for path in (auditor_stdout, auditor_stderr):
            with path.open("r+b") as stream:
                os.fsync(stream.fileno())
        audit_stdout_bytes = auditor_stdout.read_bytes()
        audit_stderr_bytes = auditor_stderr.read_bytes()
        audit_doc = json.loads(audit_stdout_bytes)
        errors = tuple(audit_doc.get("errors", ["auditor_output_shape"]))
        if audit_exit != 0 and not errors:
            errors = ("auditor_nonzero",)
        receipt["auditor_exit_code"] = audit_exit
        receipt["auditor_stdout_sha256"] = _sha256(audit_stdout_bytes)
        receipt["auditor_stderr_sha256"] = _sha256(audit_stderr_bytes)
        receipt["audit_errors"] = list(errors)
        _atomic_json(output_dir / "receipt.json", receipt)
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        errors = ("auditor_invocation_or_output",)
    if errors:
        return GateResult("STOP_RAW_AUDIT_FAILED", "NOT_EVALUATED", 1, False, None, errors, receipt)
    return GateResult("PASS_CONSTRUCTION_ONLY", "NOT_EVALUATED", 1, True, published_raw_sha, (), receipt)
