#!/usr/bin/env python3
"""One-shot R3 runner with durable per-session first outcomes."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import platform
import gzip
import shutil
import tarfile
import tempfile
import time
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
UPSTREAM = HERE / "upstream"
FORMAL_SESSIONS = 4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def compact_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def atomic_write(path: Path, data: bytes, *, replace: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}-{time.time_ns()}")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if not replace and path.exists():
            raise FileExistsError(path)
        os.replace(temp, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except BaseException:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise


def load_sources(destination: Path) -> tuple[Path, dict[str, str]]:
    manifest = json.loads((UPSTREAM / "SOURCE_MANIFEST.json").read_text())
    encoded = (UPSTREAM / "SOURCE_BUNDLE.tar.gz.b64").read_text().strip()
    archive = base64.b64decode(encoded, validate=True)
    expected_archive = manifest["SOURCE_BUNDLE.tar.gz"]["sha256"]
    if sha256(archive) != expected_archive:
        raise RuntimeError("source bundle SHA-256 mismatch")
    if len(archive) != manifest["SOURCE_BUNDLE.tar.gz"]["bytes"]:
        raise RuntimeError("source bundle length mismatch")
    destination.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(archive)), mode="r:") as tar:
        members = tar.getmembers()
        names = {m.name for m in members if m.isfile()}
        if names != {"audit.py", "common.py", "construction.py", "formal.py"}:
            raise RuntimeError("source archive member set mismatch")
        for member in members:
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise RuntimeError("unsafe source archive path")
        tar.extractall(destination, members=members, filter="data")
    for name, expected in manifest["files"].items():
        source_path = destination / name if name in {"audit.py", "common.py", "construction.py", "formal.py"} else UPSTREAM / name
        data = source_path.read_bytes()
        actual = sha256(data)
        if len(data) != expected["bytes"] or actual != expected["sha256"]:
            raise RuntimeError(f"source member mismatch: {name}")
        files[name] = actual
    return destination, files


def process_snapshot(display: str, session_root: Path, runner_pid: int) -> list[dict[str, object]]:
    residues: list[dict[str, object]] = []
    display_bytes = display.encode()
    root_bytes = str(session_root).encode()
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(proc.name)
            if pid == runner_pid:
                continue
            env = (proc / "environ").read_bytes()
            cmd = (proc / "cmdline").read_bytes()
            if b"DISPLAY=" + display_bytes not in env.split(b"\0") and root_bytes not in cmd:
                continue
            comm = (proc / "comm").read_text(errors="replace").strip()
            residues.append({"pid": pid, "comm": comm, "display_or_session_path_match": True})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return sorted(residues, key=lambda row: int(row["pid"]))


def log_manifest(session_root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(session_root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            rows.append({
                "path": str(path.relative_to(session_root)),
                "bytes": len(data),
                "sha256": sha256(data),
                "raw_base64": base64.b64encode(data).decode("ascii"),
            })
    return rows


def install_observers(common: object) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Record cleanup and XTEST calls while delegating each call unchanged."""
    from Xlib import X

    process_receipts: list[dict[str, object]] = []
    input_receipts: list[dict[str, object]] = []
    if not hasattr(common, "_r3_original_stop"):
        common._r3_original_stop = common.stop
        common._r3_original_fake_input = common.xtest.fake_input
    original_stop = common._r3_original_stop
    original_fake_input = common._r3_original_fake_input

    def observed_stop(process: object) -> None:
        before = process.poll()
        started = time.monotonic_ns()
        error = None
        try:
            original_stop(process)
        except BaseException as exc:
            error = f"{type(exc).__name__}:{exc}"
            raise
        finally:
            process_receipts.append({
                "pid": process.pid,
                "args": process.args,
                "returncode_before_stop": before,
                "returncode_after_stop": process.poll(),
                "elapsed_monotonic_ns": time.monotonic_ns() - started,
                "error": error,
            })

    def observed_fake_input(display: object, event_type: int, detail: int = 0, **kwargs: object) -> object:
        started = time.monotonic_ns()
        record: dict[str, object] = {
            "event": "KeyPress" if event_type == X.KeyPress else "KeyRelease" if event_type == X.KeyRelease else str(event_type),
            "event_type": int(event_type),
            "keycode": int(detail),
            "display": os.environ.get("DISPLAY"),
            "started_monotonic_ns": started,
            "status": "PENDING",
        }
        input_receipts.append(record)
        try:
            result = original_fake_input(display, event_type, detail=detail, **kwargs)
        except BaseException as exc:
            record["status"] = "RAISED"
            record["error"] = f"{type(exc).__name__}:{exc}"
            raise
        record["status"] = "REQUEST_SENT"
        record["finished_monotonic_ns"] = time.monotonic_ns()
        return result

    common.stop = observed_stop
    common.xtest.fake_input = observed_fake_input
    return process_receipts, input_receipts


def write_manifest(out: Path, manifest: dict[str, object]) -> str:
    raw = canonical(manifest)
    atomic_write(out / "BATCH_MANIFEST.json", raw, replace=True)
    return sha256(raw)


def reconstruct(rows: list[dict[str, object]], source_files: dict[str, str], image: dict[str, str]) -> dict[str, object]:
    from common import CYCLES, TASK, evaluate

    errors: list[str] = []
    session_rows = [r["row"] for r in rows]
    for batch in rows:
        errors.extend(f"session{batch['session_id']}:{error}" for error in batch["candidate_errors"])
        errors.extend(f"session{batch['session_id']}:{error}" for error in batch["cleanup_errors"])
    result: dict[str, object] = {
        "task": TASK,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements_budget": 0,
        "tuning": 0,
        "sessions": len(session_rows),
        "cycles_per_session": CYCLES,
        "passed_sessions": sum(bool(r["pass"]) for r in session_rows),
        "errors": errors,
        "aggregate": {
            "refusals": sum(len(r["refusals"]) for r in session_rows),
            "refusal_zero_task_input": sum(sum(x["input_before"] == x["input_after"] for x in r["refusals"]) for r in session_rows),
            "fallback_batches": sum(len(r["task_batches"]) for r in session_rows),
            "fallback_active_match": sum(sum(x["active_before"] == x["window"] for x in r["task_batches"]) for r in session_rows),
            "effects": sum(len(r["effects"]) for r in session_rows),
            "replacement_valid": sum(sum(x["old_window"] != x["new_window"] and x["old_gone"] for x in r["replacements"]) for r in session_rows),
            "terminal_neutral": sum(bool(r["terminal_neutral"]) for r in session_rows),
        },
        "descriptive": {
            "sessions_with_nonconsecutive_raw_xid_reuse": sum(
                len({x["old_window"] for x in r["replacements"]} | {x["new_window"] for x in r["replacements"]}) < 4
                for r in session_rows
            )
        },
        "environment": {
            "python": platform.python_version(),
            "platform": image["runtime_platform"],
            "chromium": image["chromium"],
            "xterm": image["xterm"],
            "x11": "private Xvfb/Openbox",
        },
        "provenance": {"source_files": source_files, "image": image},
        "decision": "PASS_MULTI_APP_GUARDED_RECOVERY_R3_SCOPED" if len(rows) == FORMAL_SESSIONS and not errors else "FAIL_MULTI_APP_GUARDED_RECOVERY_R3",
        "rows": session_rows,
    }
    basis = compact_json({k: v for k, v in result.items() if k != "rows"})
    result["summary_digest_sha256"] = sha256(basis)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_PATH_NOT_FRESH")
    image_id = os.environ.get("STUDY_IMAGE_ID")
    image_platform = os.environ.get("STUDY_PLATFORM")
    if not image_id or not image_platform:
        raise SystemExit("STOP_IMAGE_IDENTITY_UNSET")
    source_dir, source_files = load_sources(Path(tempfile.mkdtemp(prefix="r3-source-")) / "source")
    package_dir = Path("/usr/local/share/r3")
    image = {
        "image_id": image_id,
        "platform": image_platform,
        "python": platform.python_version(),
        "runtime_platform": platform.platform(),
        "chromium": (package_dir / "chromium.txt").read_text().strip(),
        "xterm": next((line for line in (package_dir / "packages.txt").read_text().splitlines() if line.startswith("xterm=")), "xterm=missing"),
        "packages_sha256": sha256((package_dir / "packages.txt").read_bytes()),
    }
    # Keep the upstream bundle isolated and immutable; only /tmp gets extracted source.
    import sys
    sys.path.insert(0, str(source_dir))
    from common import CYCLES, TASK, evaluate, run_session

    started = time.time_ns()
    manifest: dict[str, object] = {
        "schema": "r3-session-batches-v1",
        "task": TASK,
        "formal_allocation": "r3-batched-20260926-01",
        "formal_invocations": 1,
        "expected_sessions": FORMAL_SESSIONS,
        "cycles_per_session": CYCLES,
        "reruns": 0,
        "replacements": 0,
        "tuning": 0,
        "source_bundle_sha256": json.loads((UPSTREAM / "SOURCE_MANIFEST.json").read_text())["SOURCE_BUNDLE.tar.gz"]["sha256"],
        "source_files": source_files,
        "image": image,
        "started_unix_ns": started,
        "session_status": {str(i): "UNSTARTED" for i in range(1, FORMAL_SESSIONS + 1)},
        "batches": [],
    }
    atomic_write(out / "ALLOCATION_START.json", canonical({"task": TASK, "allocation": manifest["formal_allocation"], "started_unix_ns": started, "source_files": source_files, "image": image}), replace=False)
    write_manifest(out, manifest)

    for session_id in range(1, FORMAL_SESSIONS + 1):
        session_start = time.time_ns()
        marker = {"session_id": session_id, "state": "RUNNING", "started_unix_ns": session_start}
        atomic_write(out / f"session_{session_id:02d}.START.json", canonical(marker), replace=False)
        manifest["session_status"][str(session_id)] = "RUNNING"
        write_manifest(out, manifest)
        roots_before = set(Path("/tmp").glob(f"ai1769-{session_id}-*"))
        mono_start = time.monotonic_ns()
        process_receipts, input_receipts = install_observers(sys.modules["common"])
        try:
            row = run_session(session_id)
            candidate_errors = evaluate(row)
            roots = sorted(set(Path("/tmp").glob(f"ai1769-{session_id}-*")) - roots_before)
            if len(roots) != 1:
                raise RuntimeError(f"session_root_cardinality:{len(roots)}")
            session_root = roots[0]
            residues = process_snapshot(str(row["display"]), session_root, os.getpid())
            socket = Path("/tmp/.X11-unix") / f"X{str(row['display']).lstrip(':')}"
            cleanup_errors = []
            if residues:
                cleanup_errors.append("process_cleanup_residues")
            if socket.exists():
                cleanup_errors.append("x11_socket_remains")
            row["errors"] = candidate_errors + cleanup_errors
            row["pass"] = not row["errors"]
            session_logs = log_manifest(session_root)
            batch = {
                "schema": "r3-session-batch-v1",
                "task": TASK,
                "allocation": manifest["formal_allocation"],
                "session_id": session_id,
                "started_unix_ns": session_start,
                "ended_unix_ns": time.time_ns(),
                "elapsed_monotonic_ns": time.monotonic_ns() - mono_start,
                "source_files": source_files,
                "image": image,
                "row": row,
                "candidate_errors": candidate_errors,
                "cleanup_errors": cleanup_errors,
                "process_receipts": process_receipts,
                "input_event_receipts": input_receipts,
                "cleanup_residues": residues,
                "x11_socket_present_after_cleanup": socket.exists(),
                "session_root_logs": session_logs,
            }
            raw = canonical(batch)
            filename = f"session_{session_id:02d}.json"
            atomic_write(out / filename, raw, replace=False)
            record = {"session_id": session_id, "path": filename, "bytes": len(raw), "sha256": sha256(raw), "ended_unix_ns": batch["ended_unix_ns"]}
            manifest["batches"].append(record)
            manifest["session_status"][str(session_id)] = "COMPLETE"
            write_manifest(out, manifest)
            atomic_write(out / f"session_{session_id:02d}.START.json", canonical({**marker, "state": "COMPLETE", "batch_sha256": record["sha256"], "ended_unix_ns": batch["ended_unix_ns"]}), replace=True)
        except BaseException as exc:
            stop = {"session_id": session_id, "state": "STOP", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(), "input_event_receipts": input_receipts, "process_receipts": process_receipts, "stopped_unix_ns": time.time_ns()}
            atomic_write(out / f"session_{session_id:02d}.STOP.json", canonical(stop), replace=False)
            manifest["session_status"][str(session_id)] = "STOP"
            manifest["stop"] = stop
            write_manifest(out, manifest)
            raise

    rows = [json.loads((out / f"session_{i:02d}.json").read_bytes()) for i in range(1, FORMAL_SESSIONS + 1)]
    result = reconstruct(rows, source_files, image)
    raw_result = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    atomic_write(out / "RESULT.json", raw_result, replace=False)
    manifest["completed_unix_ns"] = time.time_ns()
    manifest["result_sha256"] = sha256(raw_result)
    manifest["decision"] = result["decision"]
    manifest["session_status"] = {str(i): "COMPLETE" for i in range(1, FORMAL_SESSIONS + 1)}
    write_manifest(out, manifest)
    print(json.dumps({"decision": result["decision"], "sessions": result["sessions"], "passed_sessions": result["passed_sessions"], "errors": result["errors"], "result_sha256": sha256(raw_result)}, sort_keys=True))
    return 0 if result["decision"] == "PASS_MULTI_APP_GUARDED_RECOVERY_R3_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
