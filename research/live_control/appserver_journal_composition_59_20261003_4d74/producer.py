"""One finite Linux request/journal composition producer; no retry or model call.

The per-cell outer subprocess watchdog is containment, not an I/O hard bound.
Client methods and OS-write entry are not instrumented or monkeypatched.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True

SOURCE_NAMES = (
    "main_client.py", "send_proposal.py", "close_proposal.py",
    "composed_client.py", "bounded_journal_client.py", "echo_peer.py", "producer.py",
)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(root):
    return {name: sha256_file(root / name) for name in SOURCE_NAMES}


def write_json_exclusive(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
        stream.flush()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_inventory(root):
    # cell.json describes these files but never hashes itself.
    return [
        {"path": str(path.relative_to(root)).replace("\\", "/"),
         "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "cell.json"
    ]


def clock_record(name):
    info = time.get_clock_info(name)
    return {"implementation": info.implementation, "monotonic": info.monotonic,
            "adjustable": info.adjustable, "resolution": info.resolution}


def wait_until_ns(target_ns):
    while True:
        remaining_ns = target_ns - time.monotonic_ns()
        if remaining_ns <= 0:
            return
        # A measured wait, not a claim of exact scheduler wakeup.
        time.sleep(min(remaining_ns / 1_000_000_000, 0.01))


class Events:
    def __init__(self, path):
        self.stream = path.open("x", encoding="utf-8", newline="\n")
        self.lock = threading.Lock()
        self.sequence = 0

    def _append(self, name, extra):
        row = {"seq": self.sequence, "event": name,
               "monotonic_ns": time.monotonic_ns(), "extra": extra}
        self.sequence += 1
        self.stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False) + "\n")
        self.stream.flush()
        return row["monotonic_ns"]

    def emit(self, event_name, **extra):
        with self.lock:
            return self._append(event_name, extra)

    def checkpoint(self, snapshot):
        with self.lock:
            value = snapshot()
            observed_ns = self._append("checkpoint", value)
            return observed_ns, value

    def holder_release(self, journal_lock):
        # Begin/end bracket the actual release; neither is claimed as an
        # independently measured exact mutex-transition instant.
        with self.lock:
            began_ns = self._append("holder_release_begin", {})
            journal_lock.release()
            ended_ns = self._append("holder_released", {})
            return began_ns, ended_ns


def module_from_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("source module loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cell(fixture_path, cell_dir, cell_id):
    fixture = read_json(fixture_path)
    source_root = fixture_path.parent
    constants = fixture["constants"]
    cell_spec = next(item for item in fixture["cells"] if item["cell_id"] == cell_id)
    events = Events(cell_dir / "events.jsonl")
    row = {
        "cell_id": cell_id, "variant": cell_spec["variant"],
        "condition": cell_spec["condition"], "source_file": cell_spec["source_file"],
        "status": "COMPLETE", "stop_reason": None,
        "timestamps": {
            "caller_started_ns": None, "checkpoint_ns": None,
            "caller_finished_ns": None, "holder_acquired_ns": None,
            "holder_release_begin_ns": None, "holder_released_ns": None,
        },
        "caller": {"status": "NOT_FINISHED"},
        "checkpoint": None, "final": None, "artifacts": [],
        "source_custody": source_hashes(source_root),
        "sources_after": None, "peer_command": None,
        "worker_pid": os.getpid(), "worker_parent_pid": os.getppid(),
    }
    client = None
    caller = None
    holder = None
    cleanup_errors = []
    holder_errors = []
    caller_started = threading.Event()
    holder_acquired = threading.Event()
    holder_finished = threading.Event()
    caller_finished = threading.Event()
    thread_exception_rows = []
    original_thread_hook = threading.excepthook

    def thread_hook(args):
        record = {"thread_name": args.thread.name if args.thread else None,
                  "exception_type": args.exc_type.__name__, "message": str(args.exc_value)}
        thread_exception_rows.append(record)
        events.emit("thread_exception", **record)

    threading.excepthook = thread_hook

    def journal_count():
        path = cell_dir / "journal.jsonl"
        return path.read_bytes().count(b"\n") if path.exists() else 0

    def received_bytes():
        path = cell_dir / "peer_received.bin"
        return path.stat().st_size if path.exists() else 0

    def snapshot():
        return {
            "caller_alive": bool(caller and caller.is_alive()),
            "caller_finished": caller_finished.is_set(),
            "reader_alive": bool(client and client._reader.is_alive()),
            "peer_returncode": None if client is None else client.process.poll(),
            "peer_received_bytes": received_bytes(),
            "journal_row_count": journal_count(),
            "holder_alive": bool(holder and holder.is_alive()),
            "holder_finished": holder_finished.is_set(),
        }

    def call():
        row["timestamps"]["caller_started_ns"] = events.emit(
            "caller_started", timeout_ns=constants["request_timeout_ns"])
        caller_started.set()
        try:
            result = client.request(
                fixture["request"]["method"], fixture["request"]["params"],
                timeout=constants["request_timeout_ns"] / 1_000_000_000)
            row["caller"] = {"status": "RETURN", "result": result}
        except BaseException as error:
            row["caller"] = {"status": "EXCEPTION",
                             "exception_type": type(error).__name__, "message": str(error)}
        finally:
            row["timestamps"]["caller_finished_ns"] = events.emit(
                "caller_finished", **row["caller"])
            caller_finished.set()

    def hold():
        try:
            client._journal_lock.acquire()
            row["timestamps"]["holder_acquired_ns"] = events.emit("holder_acquired")
            holder_acquired.set()
            if not caller_started.wait(timeout=0.20):
                raise RuntimeError("caller-start rendezvous absent")
            release_target = (row["timestamps"]["caller_started_ns"] +
                              constants["holder_release_offset_ns"])
            events.emit("holder_wait", release_target_ns=release_target)
            wait_until_ns(release_target)
        except BaseException as error:
            holder_errors.append({"exception_type": type(error).__name__, "message": str(error)})
            events.emit("holder_error", exception_type=type(error).__name__, message=str(error))
        finally:
            if holder_acquired.is_set():
                began_ns, ended_ns = events.holder_release(client._journal_lock)
                row["timestamps"]["holder_release_begin_ns"] = began_ns
                row["timestamps"]["holder_released_ns"] = ended_ns
            holder_finished.set()

    try:
        if os.name != "posix" or platform.system() != "Linux":
            raise RuntimeError("this frozen producer requires actual Linux POSIX pipes")
        events.emit("cell_started", spec=cell_spec)
        client_module = module_from_path(
            source_root / cell_spec["source_file"], "fixture_" + cell_spec["variant"])
        peer_command = [sys.executable, "-B", str(source_root / "echo_peer.py"),
                        "--directory", str(cell_dir)]
        row["peer_command"] = peer_command
        events.emit("client_construct_begin", peer_command=peer_command)
        client = client_module.CodexAppServerClient(
            peer_command, journal_path=str(cell_dir / "journal.jsonl"))
        events.emit("client_constructed", child_pid=client.process.pid,
                    reader_name=client._reader.name)
        ready_path = cell_dir / "peer_ready.json"
        ready_deadline_ns = time.monotonic_ns() + 350_000_000
        while not ready_path.exists():
            if client.process.poll() is not None:
                raise RuntimeError("peer exited before independent file readiness")
            if time.monotonic_ns() >= ready_deadline_ns:
                raise RuntimeError("peer file readiness deadline exceeded")
            time.sleep(0.002)
        ready = read_json(ready_path)
        if ready["pid"] != client.process.pid or ready["parent_pid"] != os.getpid():
            raise RuntimeError("peer readiness PID/parent identity mismatch")
        events.emit("peer_ready_observed", ready=ready)
        if cell_spec["condition"] == "held_journal":
            holder = threading.Thread(target=hold, name="journal-holder", daemon=True)
            holder.start()
            if not holder_acquired.wait(timeout=0.20):
                raise RuntimeError("journal holder did not acquire before caller")
        caller = threading.Thread(target=call, name="request-caller", daemon=True)
        caller.start()
        if not caller_started.wait(timeout=0.20):
            raise RuntimeError("caller did not report start")
        checkpoint_target_ns = (row["timestamps"]["caller_started_ns"] +
                                constants["checkpoint_offset_ns"])
        wait_until_ns(checkpoint_target_ns)
        checkpoint_ns, checkpoint = events.checkpoint(snapshot)
        row["timestamps"]["checkpoint_ns"] = checkpoint_ns
        row["checkpoint"] = checkpoint
        if holder is not None:
            # The holder retains the mutex until +0.40 s even if bounded caller
            # has already returned at the +0.25 s observation.
            release_target = (row["timestamps"]["caller_started_ns"] +
                              constants["holder_release_offset_ns"])
            wait_until_ns(release_target)
            holder.join(timeout=constants["cleanup_join_timeout_ns"] / 1_000_000_000)
            events.emit("holder_joined", alive=holder.is_alive())
            if holder.is_alive() or holder_errors:
                raise RuntimeError("holder failed to finish its fixed release")
        caller.join(timeout=constants["cleanup_join_timeout_ns"] / 1_000_000_000)
        events.emit("caller_joined", alive=caller.is_alive())
        if caller.is_alive():
            raise RuntimeError("caller remains live after bounded final join")
    except BaseException as error:
        row["status"] = "STOP"
        row["stop_reason"] = {"exception_type": type(error).__name__, "message": str(error)}
        events.emit("cell_stop", **row["stop_reason"])
    finally:
        if client is not None:
            # Close the driver's owned stdin explicitly to obtain peer EOF;
            # healthy peers are not counted as naturally exiting beforehand.
            try:
                if not client.process.stdin.closed:
                    events.emit("pipe_close_begin", name="stdin")
                    client.process.stdin.close()
                events.emit("stdin_closed_for_peer_eof", closed=client.process.stdin.closed)
            except BaseException as error:
                cleanup_errors.append({"stage": "stdin_close", "type": type(error).__name__,
                                       "message": str(error)})
                events.emit("cleanup_error", **cleanup_errors[-1])
            try:
                client.process.wait(timeout=constants["client_close_timeout_ns"] / 1_000_000_000)
            except subprocess.TimeoutExpired:
                events.emit("child_terminate", child_pid=client.process.pid)
                client.process.terminate()
                try:
                    client.process.wait(
                        timeout=constants["client_close_timeout_ns"] / 1_000_000_000)
                except subprocess.TimeoutExpired:
                    events.emit("child_kill", child_pid=client.process.pid)
                    client.process.kill()
                    try:
                        client.process.wait(
                            timeout=constants["client_close_timeout_ns"] / 1_000_000_000)
                    except BaseException as error:
                        cleanup_errors.append({"stage": "child_wait", "type": type(error).__name__,
                                               "message": str(error)})
                        events.emit("cleanup_error", **cleanup_errors[-1])
            except BaseException as error:
                cleanup_errors.append({"stage": "child_wait", "type": type(error).__name__,
                                       "message": str(error)})
                events.emit("cleanup_error", **cleanup_errors[-1])
            events.emit("child_reaped", child_pid=client.process.pid,
                        returncode=client.process.poll())
            try:
                events.emit("client_close_begin", timeout_ns=constants["client_close_timeout_ns"])
                client.close(timeout=constants["client_close_timeout_ns"] / 1_000_000_000)
                events.emit("client_close_returned")
            except BaseException as error:
                cleanup_errors.append({"stage": "client_close", "type": type(error).__name__,
                                       "message": str(error)})
                events.emit("cleanup_error", **cleanup_errors[-1])
            client._reader.join(
                timeout=constants["cleanup_join_timeout_ns"] / 1_000_000_000)
            events.emit("reader_joined", alive=client._reader.is_alive())
            # Child is terminal before stderr read. It is an owned echo peer
            # with no descendants; the external cell watchdog remains in force.
            if client.process.poll() is not None:
                try:
                    stderr_text = client.process.stderr.read()
                    with (cell_dir / "peer_stderr.bin").open("xb") as stream:
                        stream.write(stderr_text.encode("utf-8"))
                except BaseException as error:
                    cleanup_errors.append({"stage": "stderr_capture", "type": type(error).__name__,
                                           "message": str(error)})
                    events.emit("cleanup_error", **cleanup_errors[-1])
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(client.process, name)
                try:
                    if not stream.closed:
                        events.emit("pipe_close_begin", name=name)
                        stream.close()
                    events.emit("pipe_closed", name=name, closed=stream.closed)
                except BaseException as error:
                    cleanup_errors.append({"stage": name + "_close", "type": type(error).__name__,
                                           "message": str(error)})
                    events.emit("cleanup_error", **cleanup_errors[-1])
            try:
                if client._journal is not None and not client._journal.closed:
                    events.emit("driver_journal_close_begin")
                    client._journal.close()
                events.emit("journal_closed",
                            closed=client._journal is None or client._journal.closed)
            except BaseException as error:
                cleanup_errors.append({"stage": "journal_close", "type": type(error).__name__,
                                       "message": str(error)})
                events.emit("cleanup_error", **cleanup_errors[-1])
            if caller is not None:
                caller.join(timeout=constants["cleanup_join_timeout_ns"] / 1_000_000_000)
            if holder is not None:
                holder.join(timeout=constants["cleanup_join_timeout_ns"] / 1_000_000_000)
            row["final"] = {
                "caller_alive": bool(caller and caller.is_alive()),
                "reader_alive": client._reader.is_alive(),
                "holder_alive": bool(holder and holder.is_alive()),
                "child_pid": client.process.pid, "child_returncode": client.process.poll(),
                "explicit_pipe_closed": {
                    name: getattr(client.process, name).closed
                    for name in ("stdin", "stdout", "stderr")
                },
                "journal_closed": client._journal is None or client._journal.closed,
                "peer_received_bytes": received_bytes(), "journal_row_count": journal_count(),
                "cleanup_errors": cleanup_errors, "thread_exceptions": thread_exception_rows,
            }
            events.emit("cleanup_done", **row["final"])
            if (cleanup_errors or thread_exception_rows or row["final"]["caller_alive"] or
                    row["final"]["reader_alive"] or row["final"]["holder_alive"] or
                    row["final"]["child_returncode"] is None or
                    not all(row["final"]["explicit_pipe_closed"].values()) or
                    not row["final"]["journal_closed"]):
                row["status"] = "STOP"
                row["stop_reason"] = {"exception_type": "IncompleteCleanup",
                                      "message": "see final cleanup and thread records"}
        else:
            row["final"] = {"caller_alive": False, "reader_alive": False, "holder_alive": False,
                            "child_pid": None, "child_returncode": None,
                            "explicit_pipe_closed": {}, "journal_closed": True,
                            "cleanup_errors": cleanup_errors, "thread_exceptions": thread_exception_rows}
        row["sources_after"] = source_hashes(source_root)
        if row["sources_after"] != row["source_custody"]:
            row["status"] = "STOP"
            row["stop_reason"] = {"exception_type": "SourceDrift",
                                  "message": "source hashes changed during cell"}
        events.emit("cell_finished", status=row["status"], stop_reason=row["stop_reason"])
        threading.excepthook = original_thread_hook
        events.stream.close()
        row["artifacts"] = artifact_inventory(cell_dir)
        write_json_exclusive(cell_dir / "cell.json", row)
    return 0 if row["status"] == "COMPLETE" else 2


def stopped_row(spec, reason):
    return {
        "cell_id": spec["cell_id"], "variant": spec["variant"],
        "condition": spec["condition"], "source_file": spec["source_file"],
        "status": "STOP", "stop_reason": reason,
        "timestamps": {
            "caller_started_ns": None, "checkpoint_ns": None, "caller_finished_ns": None,
            "holder_acquired_ns": None, "holder_release_begin_ns": None, "holder_released_ns": None,
        },
        "caller": {"status": "NOT_FINISHED"}, "checkpoint": None,
        "final": None, "artifacts": [], "source_custody": None, "sources_after": None,
        "peer_command": None, "worker_pid": None, "worker_parent_pid": None,
    }


def run_producer(fixture_path, out_path):
    fixture = read_json(fixture_path)
    source_root = fixture_path.parent
    if out_path.exists():
        raise RuntimeError("raw output already exists: no overwrite or retry")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cells_root = out_path.parent / "cells"
    cells_root.mkdir()  # An existing cells directory is a preflight failure.
    initial_hashes = source_hashes(source_root)
    fixture_hash = sha256_file(fixture_path)
    monotonic = clock_record("monotonic")
    perf_counter = clock_record("perf_counter")
    raw = {
        "schema": "issue59-request-journal-composition-v1",
        "fixture_id": fixture["fixture_id"], "fixture_sha256": fixture_hash,
        "source_custody": initial_hashes, "sources_after": None,
        "producer": {
            "pid": os.getpid(), "parent_pid": os.getppid(),
            "argv": sys.argv, "started_monotonic_ns": time.monotonic_ns(),
            "finished_monotonic_ns": None, "python": sys.version,
            "executable": sys.executable, "platform": platform.platform(),
            "clock_info": {"monotonic": monotonic, "perf_counter": perf_counter},
        },
        "status": "COMPLETE", "preflight_errors": [], "cells": [],
        "scope": fixture["scope"],
    }
    if initial_hashes != fixture["source_sha256"]:
        raw["preflight_errors"].append("fixture.source_sha256 does not match exact source bytes")
    if (monotonic["implementation"] != perf_counter["implementation"] or
            not monotonic["monotonic"] or not perf_counter["monotonic"] or
            monotonic["adjustable"] or perf_counter["adjustable"]):
        raw["preflight_errors"].append("journal and driver clocks are not qualified as the same clock")
    if os.name != "posix" or platform.system() != "Linux":
        raw["preflight_errors"].append("Linux POSIX runtime required")
    progress = (out_path.parent / "producer_progress.jsonl").open(
        "x", encoding="utf-8", newline="\n")
    containment_failed = False
    for spec in fixture["cells"]:
        cell_dir = cells_root / spec["cell_id"]
        cell_dir.mkdir()
        if raw["preflight_errors"] or containment_failed:
            row = stopped_row(spec, {"exception_type": "PreflightStop",
                                     "message": "; ".join(raw["preflight_errors"]) or
                                     "previous cell containment did not complete"})
            row["supervisor"] = {"started": False, "watchdog_fired": False}
        else:
            command = [sys.executable, "-B", str(source_root / "producer.py"),
                       "--fixture", str(fixture_path), "--cell", spec["cell_id"],
                       "--cell-dir", str(cell_dir)]
            began_ns = time.monotonic_ns()
            try:
                worker = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          start_new_session=True)
            except BaseException as error:
                containment_failed = True
                row = stopped_row(spec, {"exception_type": type(error).__name__,
                                         "message": str(error)})
                row["supervisor"] = {"started": False, "command": command,
                                     "started_monotonic_ns": began_ns,
                                     "finished_monotonic_ns": time.monotonic_ns(),
                                     "watchdog_fired": False, "containment_failed": True}
                raw["cells"].append(row)
                progress.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                          allow_nan=False) + "\n")
                progress.flush()
                continue
            watchdog_fired = False
            kill_error = None
            supervision_error = None
            capture_error = None
            try:
                stdout, stderr = worker.communicate(
                    timeout=fixture["constants"]["cell_watchdog_ns"] / 1_000_000_000)
            except subprocess.TimeoutExpired:
                watchdog_fired = True
                try:
                    os.killpg(worker.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except BaseException as error:
                    kill_error = {"type": type(error).__name__, "message": str(error)}
                    containment_failed = True
                try:
                    stdout, stderr = worker.communicate(timeout=0.50)
                except subprocess.TimeoutExpired as error:
                    containment_failed = True
                    stdout, stderr = error.output or b"", error.stderr or b""
            except BaseException as error:
                supervision_error = {"type": type(error).__name__, "message": str(error)}
                try:
                    os.killpg(worker.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except BaseException as cleanup_error:
                    kill_error = {"type": type(cleanup_error).__name__,
                                  "message": str(cleanup_error)}
                    containment_failed = True
                try:
                    stdout, stderr = worker.communicate(timeout=0.50)
                except BaseException as cleanup_error:
                    containment_failed = True
                    capture_error = {"type": type(cleanup_error).__name__,
                                     "message": str(cleanup_error)}
                    stdout, stderr = b"", b""
            ended_ns = time.monotonic_ns()
            with (cell_dir / "worker.stdout.bin").open("xb") as stream:
                stream.write(stdout)
            with (cell_dir / "worker.stderr.bin").open("xb") as stream:
                stream.write(stderr)
            worker_pipe_closed = {}
            for name in ("stdout", "stderr"):
                stream = getattr(worker, name)
                if worker.poll() is not None and not stream.closed:
                    stream.close()
                worker_pipe_closed[name] = stream.closed
            supervisor = {
                "started": True, "command": command, "worker_pid": worker.pid,
                "started_monotonic_ns": began_ns, "finished_monotonic_ns": ended_ns,
                "watchdog_fired": watchdog_fired, "worker_returncode": worker.poll(),
                "kill_error": kill_error, "supervision_error": supervision_error,
                "capture_error": capture_error, "worker_pipe_closed": worker_pipe_closed,
                "containment_failed": containment_failed,
            }
            cell_path = cell_dir / "cell.json"
            if cell_path.exists():
                row = read_json(cell_path)
            else:
                row = stopped_row(spec, {"exception_type": "MissingCellRecord",
                                         "message": "see retained partial cell files and supervisor"})
            row["supervisor"] = supervisor
            if (watchdog_fired or kill_error is not None or supervision_error is not None or
                    worker.poll() is None):
                row["status"] = "STOP"
                row["stop_reason"] = {"exception_type": "ExternalCellWatchdog",
                                      "message": "2 s containment boundary; no retry"}
            elif worker.returncode != 0 and row["status"] == "COMPLETE":
                row["status"] = "STOP"
                row["stop_reason"] = {"exception_type": "WorkerExit",
                                      "message": "worker returned nonzero"}
            if row["status"] == "STOP" and not watchdog_fired:
                # A failed worker may have left its own peer alive. Its
                # private session/group is the only group addressed here.
                group_cleanup = {"attempted": True, "monotonic_ns": time.monotonic_ns()}
                try:
                    os.killpg(worker.pid, signal.SIGKILL)
                    group_cleanup["result"] = "signal_sent"
                except ProcessLookupError:
                    group_cleanup["result"] = "group_absent"
                except BaseException as error:
                    group_cleanup["result"] = "error"
                    group_cleanup["type"] = type(error).__name__
                    group_cleanup["message"] = str(error)
                    containment_failed = True
                supervisor["stop_group_cleanup"] = group_cleanup
            row["artifacts"] = artifact_inventory(cell_dir)
        raw["cells"].append(row)
        progress.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                  allow_nan=False) + "\n")
        progress.flush()
    progress.close()
    raw["sources_after"] = source_hashes(source_root)
    if raw["sources_after"] != initial_hashes or sha256_file(fixture_path) != fixture_hash:
        raw["preflight_errors"].append("source or fixture drift during producer")
    raw["status"] = ("STOP" if raw["preflight_errors"] or
                     any(row["status"] != "COMPLETE" for row in raw["cells"]) else "COMPLETE")
    raw["producer"]["finished_monotonic_ns"] = time.monotonic_ns()
    write_json_exclusive(out_path, raw)
    return 0 if raw["status"] == "COMPLETE" else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--cell")
    parser.add_argument("--cell-dir", type=Path)
    args = parser.parse_args()
    if args.cell is not None:
        if args.cell_dir is None or args.out is not None:
            parser.error("internal cell mode requires --cell-dir and forbids --out")
        return run_cell(args.fixture.resolve(), args.cell_dir.resolve(), args.cell)
    if args.out is None or args.cell_dir is not None:
        parser.error("producer mode requires --out and forbids --cell-dir")
    return run_producer(args.fixture.resolve(), args.out.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
