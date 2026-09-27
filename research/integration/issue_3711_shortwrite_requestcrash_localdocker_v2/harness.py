"""Standalone synthetic characterization for Issue #3830.

This intentionally does not import or claim to test the production CLI.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_report_once(out: Path, report: dict, backend_calls: list[int], writer):
    out.mkdir()
    (out / "request.json").write_bytes(canonical({"schema": "synthetic-request-v1", "id": "alloc-3830"}))
    backend_calls.append(1)
    raw = canonical(report)
    (out / "report.json").write_bytes(raw)
    delivered = writer(raw)
    if delivered != len(raw):
        raise OSError(f"INCOMPLETE_STDOUT_WRITE:{delivered}/{len(raw)}")
    return raw


def inspect_request_only(root: Path, backend_calls: list[int]) -> dict:
    request = json.loads((root / "request.json").read_bytes())
    report_path = root / "report.json"
    if not report_path.exists():
        return {"status": "unknown_or_incomplete", "process_state": "unknown",
                "replay_allowed": False, "request_sha256": sha((root / "request.json").read_bytes()),
                "report_state": "missing", "backend_calls": len(backend_calls),
                "request_id": request["id"]}
    return {"status": "report_recorded", "replay_allowed": False}


def main(out: Path):
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "synthetic-report-v1", "status": "completed", "payload": "immutable-fixture"}
    raw_report = canonical(report)
    dispatch_calls = []

    # Short-write fault: writer accepts an exact strict prefix and returns normally.
    short_dir = out / "short-write"
    def short_writer(data):
        return len(data) - 1
    try:
        write_report_once(short_dir, report, dispatch_calls, short_writer)
        short_status = "FALSE_SUCCESS"
    except OSError as error:
        short_status = str(error)
    retained = (short_dir / "report.json").read_bytes()
    delivered = raw_report[:-1]
    recovered_report = json.loads(retained)
    (short_dir / "delivered-prefix.bin").write_bytes(delivered)
    (short_dir / "recovered-report.json").write_bytes(retained)

    # Crash point: child durably publishes request then exits before report/call.
    crash_dir = out / "request-only"
    crash_dir.mkdir()
    request_bytes = canonical({"schema": "synthetic-request-v1", "id": "crash-3830"})
    (crash_dir / "request.json").write_bytes(request_bytes)
    child = ("from pathlib import Path; import os,sys; p=Path(sys.argv[1]); "
             "(p/'request.json').write_bytes(sys.stdin.buffer.read()); os._exit(23)")
    proc = __import__("subprocess").run([sys.executable, "-c", child, str(crash_dir)],
                                        input=request_bytes, stdout=__import__("subprocess").PIPE,
                                        stderr=__import__("subprocess").PIPE, check=False)
    # No dispatch is ever permitted during read-only recovery.
    crash_calls = []
    request_only = inspect_request_only(crash_dir, crash_calls)

    # Complete delivery control, also exactly one synthetic dispatch.
    complete_dir = out / "complete-control"
    complete_calls = []
    complete_written = write_report_once(complete_dir, report, complete_calls, lambda data: len(data))

    result = {
        "allocation": "issue3711-shortwrite-requestcrash-localdocker-formal02",
        "scope": "standalone synthetic persistence/delivery mechanics; production CLI not imported",
        "short_write": {
            "status": short_status,
            "delivered_bytes": len(delivered), "producer_bytes": len(raw_report),
            "delivered_sha256": sha(delivered), "producer_sha256": sha(raw_report),
            "retained_report_sha256": sha(retained),
            "retained_report_unchanged": retained == raw_report,
            "recovered_exact_report": recovered_report == report,
            "backend_invocations": len(dispatch_calls),
        },
        "request_only_crash": {
            "child_exit": proc.returncode,
            "report_absent": not (crash_dir / "report.json").exists(),
            "recovery": request_only,
            "backend_invocations": len(crash_calls),
        },
        "complete_control": {
            "delivered_bytes": len(complete_written),
            "producer_bytes": len(raw_report),
            "exact": complete_written == raw_report,
            "backend_invocations": len(complete_calls),
        },
    }
    (out / "result.json").write_bytes(canonical(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

