"""Supervise a bounded Issue #3311 runner without rewriting its result files."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


SCHEMA = "integrated_efficiency_termination_report_v1"
REPORT_NAME = "TERMINATION_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source_pins(source_pins: dict[str, dict[str, str]]) -> dict[str, str]:
    """Return exact verified digests or fail before any child process starts.

    Each entry is ``label: {"path": absolute_path, "sha256": expected}``.
    """
    if type(source_pins) is not dict or not source_pins:
        raise ValueError("nonempty source pin map required")
    verified = {}
    for label, pin in source_pins.items():
        if (type(label) is not str or not label or type(pin) is not dict
                or set(pin) != {"path", "sha256"}
                or type(pin["path"]) is not str
                or type(pin["sha256"]) is not str
                or len(pin["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in pin["sha256"])):
            raise ValueError("exact source pin required")
        path = Path(pin["path"])
        if not path.is_file() or path.is_symlink():
            raise ValueError("pinned source must be a regular non-symlink file")
        actual = sha256_file(path)
        if actual != pin["sha256"]:
            raise ValueError("source pin mismatch: " + label)
        verified[label] = actual
    return verified


def _artifact_manifest(root: Path) -> list[dict]:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in allocation evidence tree")
        if not path.is_file() or path.name == REPORT_NAME:
            continue
        artifacts.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return artifacts


def _verified_report_pair(root: Path) -> str | None:
    try:
        report = json.loads((root / "report.json").read_text(encoding="utf-8"))
        audit = json.loads((root / "audit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if type(report) is not dict or type(audit) is not dict:
        return None
    evaluation = report.get("evaluation")
    disposition = evaluation.get("disposition") if type(evaluation) is dict else None
    if (report.get("schema") == "integrated_efficiency_live_report_v1"
            and disposition in {"RETAIN", "HOLD", "REJECT"}
            and audit.get("passed") is True
            and audit.get("disposition") == disposition
            and audit.get("errors", []) == []):
        return disposition
    return None


def _write_new_report(root: Path, report: dict) -> Path:
    target = root / REPORT_NAME
    if target.exists():
        raise FileExistsError("termination report already exists")
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix=".termination-report-", suffix=".tmp",
                                          dir=root)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Allocation IDs and this fixed report name are single-writer scoped.
        if target.exists():
            raise FileExistsError("termination report already exists")
        # A same-directory hard link publishes atomically without replacing a
        # prior allocation's report if another writer races this check.
        os.link(temporary_name, target)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return target


def supervise(command: list[str], audit_command: list[str], allocation_root: str | Path,
              source_pins: dict[str, dict[str, str]], *, allocation_id: str) -> dict:
    """Run one frozen runner and auditor, writing HOLD/STOP evidence on termination.

    A successfully audited report (including a scientific HOLD/REJECT decision)
    is left untouched. This wrapper never infers REJECT from a process exit code.
    """
    if (type(command) is not list or not command or
            any(type(part) is not str or not part for part in command)):
        raise ValueError("nonempty string argv required")
    if (type(audit_command) is not list or not audit_command or
            any(type(part) is not str or not part for part in audit_command)):
        raise ValueError("nonempty auditor argv required")
    if type(allocation_id) is not str or not allocation_id:
        raise ValueError("allocation id required")

    root = Path(allocation_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if (root / REPORT_NAME).exists():
        raise FileExistsError("termination report already exists")

    started_ns = time.monotonic_ns()
    started = False
    failure_code = None
    runner_exit = None
    auditor_exit = None
    audited_disposition = None
    phase = "source_preflight"
    verified = {}

    try:
        verified = verify_source_pins(source_pins)
    except (OSError, ValueError) as exc:
        failure_code = "STOP_SOURCE_PIN_PREFLIGHT"
        failure_type = type(exc).__name__
    else:
        prior_outputs = ("report.json", "audit.json", "runner.stdout.log",
                         "runner.stderr.log", "audit.stdout.log", "audit.stderr.log")
        if any((root / name).exists() for name in prior_outputs):
            failure_code = "STOP_OUTPUT_PATH_ALREADY_PRESENT"
            failure_type = "OutputPathNotEmpty"
            phase = "source_preflight"
    if failure_code is None:
        try:
            phase = "runner"
            with (root / "runner.stdout.log").open("xb") as stdout, \
                    (root / "runner.stderr.log").open("xb") as stderr:
                try:
                    process = subprocess.Popen(command, cwd=root, stdout=stdout,
                                               stderr=stderr)
                except OSError as exc:
                    failure_code = "STOP_RUNNER_LAUNCH"
                    failure_type = type(exc).__name__
                    process = None
                if process is not None:
                    started = True
                    runner_exit = process.wait()
            if failure_code is not None:
                pass
            elif runner_exit != 0:
                failure_code = "HOLD_RUNNER_NONZERO_EXIT"
                failure_type = "ChildProcessExit"
            elif not (root / "report.json").is_file():
                failure_code = "HOLD_RUN_REPORT_MISSING"
                failure_type = "MissingReport"
            else:
                phase = "independent_audit"
                with (root / "audit.stdout.log").open("xb") as stdout, \
                        (root / "audit.stderr.log").open("xb") as stderr:
                    audit = subprocess.run(audit_command, cwd=root, stdout=stdout,
                                            stderr=stderr, check=False)
                auditor_exit = audit.returncode
                if auditor_exit != 0:
                    failure_code = "HOLD_INDEPENDENT_AUDIT_NONZERO_EXIT"
                    failure_type = "AuditorProcessExit"
                elif not (root / "audit.json").is_file():
                    failure_code = "HOLD_AUDIT_OUTPUT_MISSING"
                    failure_type = "MissingAudit"
                else:
                    audited_disposition = _verified_report_pair(root)
                    if audited_disposition is None:
                        failure_code = "HOLD_AUDIT_DISPOSITION_OR_REPORT_INVALID"
                        failure_type = "InvalidReportAuditPair"
        except (OSError, ValueError) as exc:
            failure_code = ("STOP_RUNNER_LAUNCH" if not started
                            else "HOLD_SUPERVISOR_IO_OR_PROCESS_ERROR")
            failure_type = type(exc).__name__

    if failure_code is None:
        return {"status": "AUDITED", "allocation_id": allocation_id,
                "runner_exit": runner_exit, "auditor_exit": auditor_exit,
                "scientific_disposition": audited_disposition}

    disposition = "STOP" if failure_code.startswith("STOP_") else "HOLD"
    report = {
        "schema": SCHEMA,
        "allocation_id": allocation_id,
        "disposition": disposition,
        "reason_code": failure_code,
        "phase": phase,
        "runner_started": started,
        "runner_exit_code": runner_exit,
        "auditor_exit_code": auditor_exit,
        "failure_type": failure_type,
        "started_monotonic_ns": started_ns,
        "finished_monotonic_ns": time.monotonic_ns(),
        "source_sha256": verified,
        "artifacts": _artifact_manifest(root),
        "interpretation": (
            "Execution or evidence termination only; no task correctness or safety "
            "failure is inferred. REJECT requires an independently audited explicit "
            "correctness-gate failure."
        ),
    }
    target = _write_new_report(root, report)
    return {"status": disposition, "allocation_id": allocation_id,
            "reason_code": failure_code, "report_path": str(target),
            "report_sha256": sha256_file(target)}
