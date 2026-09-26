from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback

from Xlib import XK, display as xdisplay

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1 import api as runtime_api

ALLOCATION = "safety-graph-live-x11-3066-20260927-v4-01"
DEADLINE_MS = 150
GRACE_MS = 50
CONFIGS = ("bare", "openbox")
SCHEDULES = ("cleanup_failure",)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def proc_snapshot(role: str, pid: int | None) -> dict:
    if pid is None:
        return {"role": role, "pid": None, "present": False}
    root = Path(f"/proc/{pid}")
    row = {"role": role, "pid": pid, "present": root.exists()}
    if not root.exists():
        return row
    try:
        stat = (root / "stat").read_text()
        tail = stat[stat.rfind(")") + 2:].split()
        row["ppid"] = int(tail[1])
        row["state"] = tail[0]
        row["argv"] = [x.decode(errors="replace") for x in (root / "cmdline").read_bytes().split(b"\0") if x]
        env = (root / "environ").read_bytes().split(b"\0")
        row["display"] = next((x.split(b"=", 1)[1].decode(errors="replace") for x in env if x.startswith(b"DISPLAY=")), None)
        links = {}
        for fd in (root / "fd").iterdir():
            try:
                links[fd.name] = os.readlink(fd)
            except OSError:
                # A process can close an fd between enumeration and readlink.
                # Record the race explicitly; it is evidence incompleteness,
                # not a reason to abort or silently claim a complete graph.
                row.setdefault("fd_snapshot_races", []).append(fd.name)
        row["fd_links"] = links
    except (OSError, ValueError, IndexError) as error:
        row["snapshot_error"] = repr(error)
    return row


def unix_socket_paths() -> dict[str, str]:
    rows = {}
    try:
        for line in Path("/proc/net/unix").read_text().splitlines()[1:]:
            cols = line.split()
            if len(cols) >= 7:
                rows[cols[6]] = cols[7] if len(cols) > 7 else ""
    except OSError:
        pass
    return rows


def add_socket_paths(process: dict, socket_rows: dict[str, str]) -> None:
    paths = []
    for link in process.get("fd_links", {}).values():
        if link.startswith("socket:["):
            inode = link[8:-1]
            path = socket_rows.get(inode)
            if path:
                paths.append(path)
    process["unix_socket_paths"] = sorted(set(paths))


def display_env(display_name: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(DISPLAY=display_name, XAUTHORITY="/dev/null", PYTHONPATH="/src", PYTHONDONTWRITEBYTECODE="1")
    return env


class KeymapMonitor:
    def __init__(self, display_name: str):
        self.display_name = display_name
        self.d = xdisplay.Display(display_name)
        self.code = self.d.keysym_to_keycode(XK.string_to_keysym("F8"))
        self.transitions: list[dict] = []
        self.changed = threading.Condition()
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _sample(self) -> bool:
        keymap = self.d.query_keymap()
        return bool(keymap[self.code // 8] & (1 << (self.code % 8)))

    def _run(self) -> None:
        try:
            last = self._sample()
            with self.changed:
                self.transitions.append({"down": last, "observed_ns": time.monotonic_ns(), "kind": "initial"})
                self.changed.notify_all()
            while not self.stopped.is_set():
                value = self._sample()
                if value != last:
                    last = value
                    with self.changed:
                        self.transitions.append({"down": value, "observed_ns": time.monotonic_ns(), "kind": "transition"})
                        self.changed.notify_all()
                time.sleep(0.001)
        except Exception as error:
            with self.changed:
                self.transitions.append({"error": repr(error), "observed_ns": time.monotonic_ns()})
                self.changed.notify_all()

    def wait_for(self, state: bool, timeout: float = 4.0) -> dict | None:
        end = time.monotonic() + timeout
        with self.changed:
            while time.monotonic() < end:
                for row in self.transitions:
                    if row.get("down") is state and row.get("kind") == "transition":
                        return row
                remaining = end - time.monotonic()
                if remaining > 0:
                    self.changed.wait(min(remaining, 0.05))
        return None

    def current(self) -> bool | None:
        # The sampler owns its connection. A fresh connection supplies an
        # independent terminal sample without sharing Xlib state across threads.
        d = None
        try:
            d = xdisplay.Display(self.display_name)
            keycode = d.keysym_to_keycode(XK.string_to_keysym("F8"))
            keymap = d.query_keymap()
            return bool(keymap[keycode // 8] & (1 << (keycode % 8)))
        except Exception:
            return None
        finally:
            if d is not None:
                d.close()

    def close(self) -> None:
        self.stopped.set()
        self.thread.join(timeout=2)
        try:
            self.d.close()
        except Exception:
            pass


def start_xvfb(number: int, config: str, env: dict[str, str]):
    name = f":{number}"
    xvfb = subprocess.Popen(
        ["Xvfb", name, "-screen", "0", "640x480x24", "-nolisten", "tcp", "-ac"],
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    socket = Path(f"/tmp/.X11-unix/X{number}")
    until = time.monotonic() + 4
    while time.monotonic() < until and not socket.exists():
        if xvfb.poll() is not None:
            break
        time.sleep(0.01)
    if not socket.exists():
        error = xvfb.stderr.read().decode(errors="replace") if xvfb.poll() is not None else "socket deadline"
        raise RuntimeError(f"STOP_XVFB_START:{error}")
    wm = None
    if config == "openbox":
        wm = subprocess.Popen(
            ["openbox"], env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        time.sleep(0.12)
        if wm.poll() is not None:
            error = wm.stderr.read().decode(errors="replace")
            raise RuntimeError(f"STOP_OPENBOX_START:{error}")
    return name, xvfb, wm


def keycode_for(display_name: str) -> int:
    d = xdisplay.Display(display_name)
    try:
        return d.keysym_to_keycode(XK.string_to_keysym("F8"))
    finally:
        d.close()


def supervisor_release(display_name: str) -> dict:
    backend = X11Backend(display_name, {"target": 1})
    try:
        backend.held_keycodes["F8"] = backend._keycode("F8")
        started = time.monotonic_ns()
        release = backend.release_all()
        return {"started_ns": started, "finished_ns": time.monotonic_ns(), "release": release}
    finally:
        backend.close()


def worker(display_name: str, xid: int, schedule: str, start_receipt_path: Path) -> int:
    class FailingReleaseBackend(X11Backend):
        def release_all(self):
            raise RuntimeError("INJECTED_RELEASE_PATH_FAILURE")

    faulty = schedule == "cleanup_failure"
    backend_type = FailingReleaseBackend if faulty else X11Backend
    backend = backend_type(display_name, {"target": xid})
    started = backend.monotonic_ns()
    deadline = started + DEADLINE_MS * 1_000_000
    wait_ms = {
        "normal": 30, "ipc_delay": 30, "display_stall": 30,
        "owner_death": 4000, "target_replacement": 30, "cleanup_failure": 120,
    }.get(schedule, 30)
    program = {
        "schema": "agent-interface/program-v1",
        "program_id": f"safety3066v4-{schedule}",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": f"safety3066v4-lease-{schedule}", "expires_at_ns": deadline},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "target"},
            {"op": "key_state", "key": "F8", "down": True},
            {"op": "wait_update", "timeout_ms": wait_ms},
            {"op": "release_all"},
        ],
    }
    receipt = {
        "pid": os.getpid(), "started_ns": started, "authority_deadline_ns": deadline,
        "authority_lease_ms": DEADLINE_MS, "wait_update_ms": wait_ms,
        "schedule": schedule, "fault_injected_release_method": faulty,
        "loaded_runtime": {
            "session": X11RuntimeSession.__module__ + "." + X11RuntimeSession.__name__,
            "backend": backend.__class__.__module__ + "." + backend.__class__.__name__,
            "dispatch_facade": "runtime.cli_v1.api.dispatch",
        },
    }
    write_json(start_receipt_path, receipt)
    try:
        if faulty:
            # Keep the normal public CLI facade but inject the precise native
            # release failure at its session factory boundary.
            original_open_session = runtime_api.open_session

            def open_failing_session(*_args, **_kwargs):
                return X11RuntimeSession(backend)

            runtime_api.open_session = open_failing_session
        receipt["dispatch_result"] = runtime_api.dispatch(
            program, {"target": xid},
            current_observation_seq=1, current_binding_revision=1,
            display_name=display_name,
        )
    except Exception as error:
        receipt.update(dispatch_exception=repr(error), traceback=traceback.format_exc())
    finally:
        if faulty:
            runtime_api.open_session = original_open_session
        receipt["finished_ns"] = time.monotonic_ns()
    sys.stdout.write(json.dumps(receipt, sort_keys=True) + "\n")
    sys.stdout.flush()
    return 0


def observer_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"decode_error": line})
    return rows


def wait_observer_event(path: Path, kind: str, timeout: float = 5.0) -> dict | None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        for event in observer_events(path):
            if event.get("kind") == kind:
                return event
        time.sleep(0.001)
    return None


def stop_process(p: subprocess.Popen | None, grace: float = 0.5) -> dict:
    if p is None:
        return {"pid": None, "exited": True, "returncode": None}
    before = time.monotonic_ns()
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=grace)
    return {"pid": p.pid, "returncode": p.returncode, "stopped_ns": before, "exited": p.poll() is not None}


def run_case(config: str, schedule: str, index: int, outroot: Path) -> dict:
    case_dir = outroot / f"{index:02d}-{config}-{schedule}"
    case_dir.mkdir(parents=True)
    display_name = f":{630 + index}"
    env = display_env(display_name)
    row = {
        "config": config, "schedule": schedule, "case_index": index,
        "allocation": ALLOCATION, "started_ns": time.monotonic_ns(),
        "runner_pid": os.getpid(), "display": display_name,
        "authority_deadline_ms": DEADLINE_MS, "grace_ms": GRACE_MS,
        "schedule_order": list(SCHEDULES), "expected_input": "F8",
    }
    xvfb = wm = app = child = None
    monitor = None
    read_stdout_later = False
    stdout_pipe_links = {}
    try:
        display_name, xvfb, wm = start_xvfb(630 + index, config, env)
        row["xvfb_pid"] = xvfb.pid
        row["wm_pid"] = wm.pid if wm else None
        monitor = KeymapMonitor(display_name)
        monitor.start()

        meta_path = case_dir / "observer.meta.json"
        event_path = case_dir / "observer.events.jsonl"
        app = subprocess.Popen(
            [sys.executable, "/exp/observer.py", "--meta", str(meta_path), "--events", str(event_path)],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        row["observer_pid"] = app.pid
        end = time.monotonic() + 4
        while time.monotonic() < end and not meta_path.exists():
            if app.poll() is not None:
                break
            time.sleep(0.01)
        if not meta_path.exists():
            raise RuntimeError("STOP_TARGET_OBSERVER_START")
        xid = int(read_json(meta_path)["window_id"])
        row["target_xid"] = xid
        row["target_mapped_ns"] = read_json(meta_path)["mapped_ns"]

        if schedule == "unknown_dependency":
            row.update(
                execution_disposition="STOP_UNKNOWN_DEPENDENCY",
                typed_stop=True, input_dispatched=False,
                unknown_dependency="unclassified_server_side_input_owner",
                unknown_guard_ns=time.monotonic_ns(),
            )
        else:
            child = subprocess.Popen(
                [sys.executable, "/exp/run.py", "--worker", "--display", display_name,
                 "--xid", str(xid), "--schedule", schedule,
                 "--start-receipt", str(case_dir / "worker.start.json")],
                env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            row["worker_pid"] = child.pid
            row["worker_stdout_fd"] = child.stdout.fileno()
            row["worker_stdout_link"] = os.readlink(f"/proc/{child.pid}/fd/1")
            row["parent_stdout_link"] = os.readlink(f"/proc/{os.getpid()}/fd/{child.stdout.fileno()}")
            row["worker_snapshot_start"] = proc_snapshot("worker", child.pid)
            press = wait_observer_event(event_path, "press", timeout=5)
            row["key_down_observed"] = press
            if press is None and schedule != "unknown_dependency":
                raise RuntimeError("HOLD_KEY_PRESS_NOT_OBSERVED")
            row["key_down_observer_ns"] = press.get("monotonic_ns") if press else None
            row["worker_snapshot_at_keydown"] = proc_snapshot("worker", child.pid)
            start_receipt_path = case_dir / "worker.start.json"
            if start_receipt_path.exists():
                row["worker_start_receipt"] = read_json(start_receipt_path)

            if schedule == "display_stall":
                row["xvfb_sigstop_ns"] = time.monotonic_ns()
                os.kill(xvfb.pid, signal.SIGSTOP)
                time.sleep(0.180)
                row["xvfb_sigcont_ns"] = time.monotonic_ns()
                os.kill(xvfb.pid, signal.SIGCONT)
                resumed = monitor.wait_for(False, timeout=5)
                row["post_stall_release_transition"] = resumed
            elif schedule == "owner_death":
                row["worker_sigkill_ns"] = time.monotonic_ns()
                child.kill()
                child.wait(timeout=2)
                row["worker_returncode"] = child.returncode
                row["worker_snapshot_at_death"] = row["worker_snapshot_start"]
                row["cleanup_supervisor_pid"] = os.getpid()
                row["supervisor_release"] = supervisor_release(display_name)
            elif schedule == "target_replacement":
                row["target_terminate_ns"] = time.monotonic_ns()
                app.kill()
                app.wait(timeout=2)
                row["target_returncode"] = app.returncode
            if schedule == "ipc_delay":
                child.wait(timeout=5)
                row["worker_finished_before_result_read"] = True
                row["result_pipe_read_not_before_ns"] = time.monotonic_ns() + 200_000_000
                time.sleep(0.200)
                read_stdout_later = True
            else:
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    row["worker_timeout"] = True
                    child.kill()
                    child.wait(timeout=2)
            row["worker_returncode"] = child.returncode
            row["worker_snapshot_after"] = proc_snapshot("worker", child.pid)
            row["worker_stderr"] = child.stderr.read().decode(errors="replace")
            if child.returncode == 0 and schedule != "owner_death":
                output = child.stdout.read().decode(errors="replace")
                row["result_pipe_read_ns"] = time.monotonic_ns()
                row["worker_stdout"] = output
                for line in reversed(output.splitlines()):
                    try:
                        row["worker_receipt"] = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
                if "worker_receipt" not in row:
                    row["worker_receipt_decode_error"] = True
                elif schedule == "cleanup_failure":
                    # v3 deliberately waited until deadline + 60 ms even though
                    # this receipt was already available. This allocation tests
                    # one immediate, single-shot recovery after the typed
                    # recovery_required result becomes visible to the caller.
                    row["recovery_receipt_observed_ns"] = time.monotonic_ns()
                    dispatch = row["worker_receipt"].get("dispatch_result", {})
                    runtime_result = dispatch.get("result", {}) if isinstance(dispatch, dict) else {}
                    row["recovery_trigger"] = {
                        "kind": "typed_runtime_recovery_required"
                        if runtime_result.get("status") == "execution_failed"
                        and runtime_result.get("recovery_required") is True
                        else "typed_runtime_recovery_required_missing",
                        "observed_ns": row["recovery_receipt_observed_ns"],
                        "runtime_status": runtime_result.get("status"),
                        "recovery_required": runtime_result.get("recovery_required"),
                    }
                    if row["recovery_trigger"]["kind"] == "typed_runtime_recovery_required":
                        row["cleanup_supervisor_pid"] = os.getpid()
                        row["supervisor_attempt_count"] = 1
                        row["supervisor_release"] = supervisor_release(display_name)
                        row["recovery_receipt_to_release_finish_ms"] = (
                            row["supervisor_release"]["finished_ns"]
                            - row["recovery_receipt_observed_ns"]
                        ) / 1_000_000
                        row["post_cleanup_release_transition"] = monitor.wait_for(False, timeout=1.0)
            elif schedule == "owner_death":
                row["worker_stdout"] = child.stdout.read().decode(errors="replace")
            if schedule == "cleanup_failure" and not isinstance(row.get("worker_receipt"), dict):
                raise RuntimeError(f"HOLD_CLEANUP_RECEIPT_MISSING:rc={child.returncode};stdout={row.get('worker_stdout')!r};stderr={row.get('worker_stderr')!r}")
            if read_stdout_later:
                if isinstance(row.get("worker_receipt"), dict):
                    row["result_delivery_delay_ms"] = (
                        row["result_pipe_read_ns"] - row["worker_receipt"]["finished_ns"]
                    ) / 1_000_000

        row["terminal_key_down"] = monitor.current()
        row["keymap_transitions"] = list(monitor.transitions)
        row["observer_events"] = observer_events(event_path)
        releases = [e["monotonic_ns"] for e in row["observer_events"] if e.get("kind") == "release"]
        ups = [e["observed_ns"] for e in row["keymap_transitions"] if e.get("down") is False and e.get("kind") == "transition"]
        row["app_release_ns"] = releases[0] if releases else None
        row["keymap_release_upper_bound_ns"] = ups[0] if ups else None
        witnesses = [x for x in (row["app_release_ns"], row["keymap_release_upper_bound_ns"]) if x is not None]
        row["release_witness_upper_bound_ns"] = min(witnesses) if witnesses else None
        if schedule == "cleanup_failure":
            row["terminal_key_down"] = monitor.current()
            row["post_cleanup_key_down"] = monitor.current()
            if row["terminal_key_down"]:
                row["supervisor_fallback_suppressed"] = "single_attempt_policy"
        if schedule == "unknown_dependency":
            row["input_dispatched"] = False
        process_rows = [
            proc_snapshot("runner", os.getpid()),
            proc_snapshot("xvfb", xvfb.pid),
            proc_snapshot("openbox", wm.pid if wm else None),
            proc_snapshot("observer", app.pid if app else None),
            row.get("worker_snapshot_at_keydown") or row.get("worker_snapshot_start") or proc_snapshot("worker", child.pid if child else None),
        ]
        for process in process_rows:
            add_socket_paths(process, unix_socket_paths())
        row["processes"] = process_rows
        row["unix_sockets_by_inode"] = unix_socket_paths()
        row["ended_ns"] = time.monotonic_ns()
    finally:
        if xvfb is not None and xvfb.poll() is None:
            try:
                os.kill(xvfb.pid, signal.SIGCONT)
            except OSError:
                pass
        if monitor is not None:
            monitor.close()
        row.setdefault("cleanup", {})
        row["cleanup"]["observer"] = stop_process(app)
        row["cleanup"]["openbox"] = stop_process(wm)
        row["cleanup"]["xvfb"] = stop_process(xvfb)
    return row


def formal(out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_FORMAL_OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    index = 0
    for config in CONFIGS:
        for schedule in SCHEDULES:
            try:
                rows.append(run_case(config, schedule, index, out))
            except Exception as error:
                rows.append({
                    "config": config, "schedule": schedule, "case_index": index,
                    "allocation": ALLOCATION, "execution_disposition": "STOP_INFRASTRUCTURE_OR_EVIDENCE",
                    "error": repr(error), "traceback": traceback.format_exc(),
                    "failed_ns": time.monotonic_ns(),
                })
                write_json(out / "RAW.json", rows)
                write_json(out / "STOP.json", {
                    "allocation": ALLOCATION, "completed_case_rows": len(rows) - 1,
                    "failed_case_index": index, "status": "STOP_INFRASTRUCTURE_OR_EVIDENCE",
                    "reruns": 0, "replacements": 0, "postfreeze_tuning": 0,
                })
                return 2
            write_json(out / "RAW.json", rows)
            index += 1
    print(json.dumps({"allocation": ALLOCATION, "cases": len(rows), "raw": str(out / "RAW.json")}, sort_keys=True))
    return 0


def construction(out: Path) -> int:
    """Exercise the complete harness once; output is never formal evidence."""
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    index = 0
    for config in CONFIGS:
        for schedule in SCHEDULES:
            try:
                row = run_case(config, schedule, index, out)
                row["construction_only"] = True
                rows.append(row)
                write_json(out / "CONSTRUCTION.json", rows)
            except Exception as error:
                rows.append({
                    "config": config, "schedule": schedule, "case_index": index,
                    "allocation": ALLOCATION, "construction_only": True,
                    "execution_disposition": "STOP_CONSTRUCTION_ONLY",
                    "error": repr(error), "traceback": traceback.format_exc(),
                })
                write_json(out / "CONSTRUCTION.json", rows)
                return 2
            index += 1
    print(json.dumps({"construction_only": True, "formal_invocations": 0, "cases": len(rows), "output": str(out)}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--display")
    parser.add_argument("--xid", type=int)
    parser.add_argument("--schedule")
    parser.add_argument("--start-receipt", type=Path)
    parser.add_argument("--formal")
    parser.add_argument("--construction")
    args = parser.parse_args()
    if args.worker:
        if args.start_receipt is None:
            parser.error("--start-receipt is required for worker mode")
        return worker(args.display, args.xid, args.schedule, args.start_receipt)
    if args.formal:
        return formal(Path(args.formal))
    if args.construction:
        return construction(Path(args.construction))
    parser.error("choose --worker or --formal")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
