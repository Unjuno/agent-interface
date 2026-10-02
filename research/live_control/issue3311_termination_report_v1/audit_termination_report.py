"""Independent raw-file audit for Issue #3311 termination reports."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from pathlib import PurePosixPath


REQUIRED = {
    "schema", "allocation_id", "disposition", "reason_code", "phase",
    "runner_started", "runner_exit_code", "auditor_exit_code", "failure_type",
    "started_monotonic_ns", "finished_monotonic_ns", "source_sha256",
    "artifacts", "interpretation",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(path: str | Path) -> dict:
    report_path = Path(path).resolve()
    root = report_path.parent
    errors = []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"passed": False, "errors": ["report unreadable: " + type(exc).__name__]}
    if type(report) is not dict or set(report) != REQUIRED:
        return {"passed": False, "errors": ["exact termination report fields required"]}

    if report["schema"] != "integrated_efficiency_termination_report_v1":
        errors.append("unsupported schema")
    if type(report["allocation_id"]) is not str or not report["allocation_id"]:
        errors.append("allocation id required")
    reason = report["reason_code"]
    allowed_reasons = {
        "STOP_SOURCE_PIN_PREFLIGHT", "STOP_RUNNER_LAUNCH",
        "STOP_OUTPUT_PATH_ALREADY_PRESENT",
        "HOLD_RUNNER_NONZERO_EXIT", "HOLD_RUN_REPORT_MISSING",
        "HOLD_INDEPENDENT_AUDIT_NONZERO_EXIT", "HOLD_AUDIT_OUTPUT_MISSING",
        "HOLD_AUDIT_DISPOSITION_OR_REPORT_INVALID",
        "HOLD_SUPERVISOR_IO_OR_PROCESS_ERROR",
    }
    if type(reason) is not str or reason not in allowed_reasons:
        errors.append("unknown termination reason")
    if (type(report["disposition"]) is not str
            or report["disposition"] not in {"HOLD", "STOP"}):
        errors.append("termination disposition must be HOLD or STOP")
    elif (report["disposition"] == "STOP") != (
            type(reason) is str and reason.startswith("STOP_")):
        errors.append("disposition/reason mismatch")
    if type(report["runner_started"]) is not bool:
        errors.append("runner_started must be boolean")
    if (type(report["phase"]) is not str
            or report["phase"] not in {"source_preflight", "runner", "independent_audit"}):
        errors.append("unknown execution phase")
    if report["disposition"] == "STOP" and report["runner_started"] is True:
        errors.append("STOP cannot follow a started runner")
    if report["disposition"] == "HOLD" and report["runner_started"] is not True:
        errors.append("HOLD requires a started runner")
    if reason == "STOP_RUNNER_LAUNCH" and report["runner_started"] is not False:
        errors.append("runner launch STOP must precede process start")
    if (reason == "STOP_SOURCE_PIN_PREFLIGHT"
            or reason == "STOP_OUTPUT_PATH_ALREADY_PRESENT") \
            and report["phase"] != "source_preflight":
        errors.append("source pin STOP phase mismatch")
    if any(type(report[key]) is not int or report[key] < 0 for key in
           ("started_monotonic_ns", "finished_monotonic_ns")):
        errors.append("monotonic timestamps required")
    elif report["finished_monotonic_ns"] < report["started_monotonic_ns"]:
        errors.append("monotonic timestamp order invalid")
    if type(report["source_sha256"]) is not dict:
        errors.append("source digest map required")
    else:
        for label, digest in report["source_sha256"].items():
            if (type(label) is not str or type(digest) is not str or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)):
                errors.append("invalid source digest")
                break

    artifacts = report["artifacts"]
    if type(artifacts) is not list:
        errors.append("artifact list required")
    else:
        seen = set()
        for row in artifacts:
            if type(row) is not dict or set(row) != {"path", "size_bytes", "sha256"}:
                errors.append("exact artifact row required")
                continue
            relative = row["path"]
            posix_path = PurePosixPath(relative) if type(relative) is str else None
            if (type(relative) is not str or not relative or "\\" in relative
                    or posix_path.is_absolute() or ".." in posix_path.parts
                    or ":" in posix_path.parts[0] or relative in seen):
                errors.append("artifact path must be unique and relative")
                continue
            seen.add(relative)
            candidate = root / Path(relative)
            try:
                cursor = root
                for part in posix_path.parts:
                    cursor = cursor / part
                    if cursor.is_symlink():
                        raise OSError("symlink path component")
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(root)
                if candidate.is_symlink() or not resolved.is_file():
                    raise OSError("not a regular file")
                if type(row["size_bytes"]) is not int or row["size_bytes"] < 0:
                    errors.append("invalid artifact size: " + relative)
                elif resolved.stat().st_size != row["size_bytes"]:
                    errors.append("artifact size mismatch: " + relative)
                if sha256_file(resolved) != row["sha256"]:
                    errors.append("artifact digest mismatch: " + relative)
            except (OSError, ValueError):
                errors.append("artifact missing or escapes allocation: " + relative)
    if report["interpretation"] != (
            "Execution or evidence termination only; no task correctness or safety "
            "failure is inferred. REJECT requires an independently audited explicit "
            "correctness-gate failure."):
        errors.append("interpretation boundary missing")
    return {"passed": not errors, "errors": errors,
            "disposition": report.get("disposition"),
            "reason_code": report.get("reason_code"),
            "artifact_count": len(artifacts) if type(artifacts) is list else None}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)
