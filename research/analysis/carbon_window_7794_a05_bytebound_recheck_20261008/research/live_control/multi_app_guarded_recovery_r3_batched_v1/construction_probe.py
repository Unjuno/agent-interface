#!/usr/bin/env python3
"""One excluded private-X11 construction using the exact frozen R3 session."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import sys
import tempfile
import time
import traceback
from pathlib import Path

import run_batches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--session-id", type=int, default=98)
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_NOT_FRESH")
    srcdir, source_hashes = run_batches.load_sources(Path(tempfile.mkdtemp(prefix="r3-construction-source-")) / "source")
    sys.path.insert(0, str(srcdir))
    import common

    image_id = os.environ.get("STUDY_IMAGE_ID", "UNSET")
    image = {"image_id": image_id, "platform": os.environ.get("STUDY_PLATFORM", "UNSET"), "python": platform.python_version(), "runtime_platform": platform.platform()}
    session_id = args.session_id
    roots_before = set(Path("/tmp").glob(f"ai1769-{session_id}-*"))
    processes, input_events = run_batches.install_observers(common)
    started = time.time_ns()
    mono = time.monotonic_ns()
    try:
        row = common.run_session(session_id)
        candidate_errors = common.evaluate(row)
        roots = sorted(set(Path("/tmp").glob(f"ai1769-{session_id}-*")) - roots_before)
        if len(roots) != 1:
            raise RuntimeError(f"STOP_CONSTRUCTION_SESSION_ROOTS:{len(roots)}")
        root = roots[0]
        residues = run_batches.process_snapshot(str(row["display"]), root, os.getpid())
        socket = Path("/tmp/.X11-unix") / f"X{str(row['display']).lstrip(':')}"
        cleanup_errors = []
        if residues:
            cleanup_errors.append("process_cleanup_residues")
        if socket.exists():
            cleanup_errors.append("x11_socket_remains")
        row["errors"] = candidate_errors + cleanup_errors
        row["pass"] = not row["errors"]
    except BaseException as exc:
        stop = {
            "phase": "EXCLUDED_CONSTRUCTION",
            "decision": "STOP_CONSTRUCTION_EXCEPTION",
            "formal_rows": 0,
            "session_id": session_id,
            "source_files": source_hashes,
            "image": image,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "process_receipts": processes,
            "input_event_receipts": input_events,
            "session_root_logs": run_batches.log_manifest(roots[0]) if len(roots := sorted(set(Path("/tmp").glob(f"ai1769-{session_id}-*")) - roots_before)) == 1 else [],
            "stopped_unix_ns": time.time_ns(),
        }
        raw_stop = run_batches.canonical(stop)
        run_batches.atomic_write(out / "CONSTRUCTION_STOP.json", raw_stop, replace=False)
        print(json.dumps({"phase": stop["phase"], "decision": stop["decision"], "error": stop["error"], "sha256": hashlib.sha256(raw_stop).hexdigest()}, sort_keys=True))
        return 2
    artifact = {
        "phase": "EXCLUDED_CONSTRUCTION",
        "formal_rows": 0,
        "task": common.TASK,
        "session_id": session_id,
        "started_unix_ns": started,
        "ended_unix_ns": time.time_ns(),
        "elapsed_monotonic_ns": time.monotonic_ns() - mono,
        "source_files": source_hashes,
        "image": image,
        "candidate_errors": candidate_errors,
        "cleanup_errors": cleanup_errors,
        "process_receipts": processes,
        "input_event_receipts": input_events,
        "cleanup_residues": residues,
        "x11_socket_present_after_cleanup": socket.exists(),
        "session_root_logs": run_batches.log_manifest(root),
        "row": row,
    }
    raw = run_batches.canonical(artifact)
    run_batches.atomic_write(out / "CONSTRUCTION.json", raw, replace=False)
    print(json.dumps({"phase": artifact["phase"], "pass": row["pass"], "candidate_errors": candidate_errors, "cleanup_errors": cleanup_errors, "input_events": len(input_events), "process_receipts": len(processes), "sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))
    return 0 if row["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
