"""One-shot Xvfb execution of retained-input per-key release receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
import types

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
PATTERN = [
    ("a", True), ("a", False),
    ("a", True), ("a", False),
    ("a", True), ("space", True), ("space", False), ("a", False),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class NoopOwner:
    def close(self):
        return None


class Lease:
    def __init__(self, deadline, focus, token):
        self.deadline = deadline
        self.expected_focus = focus
        self.intent_token = token
        self.cancel = threading.Event()
        self.focus_invalid = False
        self._interruption = None

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired")

    def interruption_snapshot(self):
        return self._interruption

    def record_interruption(self, record):
        self._interruption = record


def install_import_shims():
    """Isolate the raw-method boundary; retain the actual X11 owner modules."""
    exceptions = types.ModuleType("executor_v3")
    exceptions.Cancelled = type("Cancelled", (Exception,), {})
    exceptions.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = exceptions

    parent = types.ModuleType("doom_typed_coast_backend_v1")

    class Parent:
        def __init__(self, session, out, emit, signal_readers):
            self.session = session
            self.out = out
            self.emit = emit
            self.signal_readers = signal_readers
            self.owner = NoopOwner()
            self.held = set()
            self.lease = None

        def execute(self, step, cancel, identifier, index):
            for key, down in step["actions"]:
                self.raw(key, down)
                step["edge_observations"].append(
                    {"key": key, "down": down,
                     "keymap": {name: keymap_state(name) for name in _keycodes}}
                )
            return "ok"

    parent.Backend = Parent
    parent.suite = object()
    sys.modules["doom_typed_coast_backend_v1"] = parent


_observer = None
_keycodes = {}


def keymap_state(key):
    bitmap = _observer.query_keymap()
    code = _keycodes[key]
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def wait_event(expected_type, expected_code, expected_window, timeout_s=1.0):
    ready, _, _ = select.select([_observer.fileno()], [], [], timeout_s)
    if not ready:
        raise TimeoutError("client event dispatch timeout")
    event = _observer.next_event()
    result = {
        "event_type": int(event.type),
        "event_name": "KeyPress" if event.type == X.KeyPress else (
            "KeyRelease" if event.type == X.KeyRelease else f"type-{event.type}"
        ),
        "keycode": int(event.detail),
        "server_time_ms": int(event.time),
        "event_window": int(event.window.id),
        "dispatch_ns": time.perf_counter_ns(),
    }
    if (event.type != expected_type or int(event.detail) != expected_code
            or int(event.window.id) != expected_window):
        result["expected"] = {
            "event_type": int(expected_type), "keycode": int(expected_code),
            "event_window": expected_window
        }
        raise ValueError("unexpected client-dispatched event: " + json.dumps(result))
    return result


def main():
    global X, XK, display
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--cycles", type=int, default=10)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit("output directory already exists; refusing overwrite")
    out.mkdir(parents=True)
    cycles = args.cycles
    if cycles != 10:
        raise SystemExit("frozen candidate requires exactly 10 cycles")

    raw = {
        "schema": "map01-v39-xvfb-per-key-release-raw-a02-v1",
        "status": "STOP",
        "cycles_requested": cycles,
        "actions": [],
        "emitted_rows": [],
        "client_events": [],
        "errors": [],
        "cleanup": {},
        "scope": "one isolated Xvfb client; no game, model, physical input, or task effect",
    }
    freeze_path = HERE.parent / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    raw["source_sha256"] = freeze["source_sha256"]
    raw["candidate_sha256"] = sha(__file__)
    if sha(__file__) != freeze["candidate_sha256"]:
        raise SystemExit("candidate hash differs from frozen source")
    for name, expected_sha in freeze["source_sha256"].items():
        if sha(SOURCE / name) != expected_sha:
            raise SystemExit(f"frozen source hash mismatch: {name}")
    xvfb = None
    owner = None
    observer = None
    window = None
    try:
        sys.path.insert(0, str(SOURCE))
        sys.path.insert(0, str(SOURCE / "source"))
        from Xlib import X as xlib_X, XK as xlib_XK, display as xlib_display
        X, XK, display = xlib_X, xlib_XK, xlib_display
        env = dict(os.environ)
        env["DISPLAY"] = ":117"
        xvfb = subprocess.Popen(
            ["Xvfb", ":117", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-noreset", "-ac"],
            env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        raw["xvfb_pid"] = xvfb.pid
        deadline = time.monotonic() + 5.0
        last_error = None
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                last_error = xvfb.stderr.read().decode("utf-8", "replace")
                raise RuntimeError("Xvfb exited during startup: " + last_error)
            try:
                observer = display.Display(":117")
                break
            except Exception as exc:
                last_error = repr(exc)
                time.sleep(0.05)
        if observer is None:
            raise TimeoutError("Xvfb display startup timed out: " + str(last_error))

        root = observer.screen().root
        window = root.create_window(
            20, 20, 320, 200, 0, observer.screen().root_depth,
            X.InputOutput, X.CopyFromParent,
            event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        observer.set_input_focus(X.RevertToParent, window, X.CurrentTime)
        observer.sync()
        raw["client_window"] = int(window.id)
        _keycodes.update({
            key: int(observer.keysym_to_keycode(XK.string_to_keysym(key)))
            for key in ("a", "space")
        })
        if not all(_keycodes.values()):
            raise RuntimeError("Xvfb keymap missing a frozen test key")
        raw["keycodes"] = dict(_keycodes)
        for _ in range(100):
            if observer.get_input_focus().focus.id == window.id:
                break
            time.sleep(0.01)
        else:
            raise RuntimeError("test client did not receive input focus")
        while observer.pending_events():
            observer.next_event()

        global _observer
        _observer = observer
        install_import_shims()
        from doom_retained_input_backend_v4 import Backend

        class Session:
            name = ":117"

        rows = []
        backend = Backend(Session(), out, rows.append, {})
        owner = backend.owner
        lease = Lease(time.perf_counter_ns() + 30_000_000_000,
                      int(window.id), "xvfb-per-key-a02")
        backend.lease = lease
        actions = PATTERN * cycles
        edge_observations = []
        started_ns = time.perf_counter_ns()
        result = backend.execute(
            {"actions": actions, "edge_observations": edge_observations},
            lease.cancel, "xvfb-per-key-a02", 7,
        )
        ended_ns = time.perf_counter_ns()
        raw["backend_result"] = result
        raw["execute_started_ns"] = started_ns
        raw["execute_ended_ns"] = ended_ns
        raw["actions"] = edge_observations
        for cycle in range(cycles):
            for offset, (key, down) in enumerate(PATTERN):
                event = wait_event(
                    X.KeyPress if down else X.KeyRelease, _keycodes[key],
                    int(window.id)
                )
                raw["client_events"].append({
                    "cycle": cycle, "edge": offset, "key": key,
                    "down": down, **event,
                })
        raw["emitted_rows"] = rows
        raw["server_keymap_empty_after_edges"] = not any(
            keymap_state(key) for key in ("a", "space")
        )
        explicit_release = owner.call("release", lease)
        owner_close_return = owner.close()
        close_records = [
            row for row in owner.records
            if isinstance(row, dict) and row.get("event") == "owner_release"
            and row.get("reason") == "close"
        ]
        raw["cleanup"]["explicit_owner_release"] = explicit_release
        raw["cleanup"]["owner_close_return"] = owner_close_return
        raw["cleanup"]["owner_close_result"] = close_records[-1] if close_records else None
        raw["cleanup"]["owner_closed"] = owner._inner.closed
        raw["cleanup"]["owner_stopped"] = owner._inner.stopped.is_set()
        raw["cleanup"]["owner_thread_alive"] = owner._inner.thread.is_alive()
        raw["cleanup"]["server_keymap_empty_after_close"] = not any(
            keymap_state(key) for key in ("a", "space")
        )
        raw["status"] = "CANDIDATE_COMPLETE"
    except Exception as exc:
        raw["errors"].append(repr(exc))
        raw["status"] = "CANDIDATE_ERROR"
    finally:
        if owner is not None and not owner._inner.closed:
            try:
                owner.close()
            except Exception as exc:
                raw["cleanup"]["owner_close_error"] = repr(exc)
        if observer is not None:
            try:
                observer.close()
            except Exception as exc:
                raw["cleanup"]["observer_close_error"] = repr(exc)
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
            except Exception as exc:
                raw["cleanup"]["xvfb_terminate_error"] = repr(exc)
                try:
                    xvfb.kill()
                    xvfb.wait(timeout=5)
                except Exception as kill_exc:
                    raw["cleanup"]["xvfb_kill_error"] = repr(kill_exc)
            raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            raw["cleanup"]["xvfb_stopped"] = xvfb.poll() is not None
        out.joinpath("RAW.json").write_text(
            json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    return 0 if raw["status"] == "CANDIDATE_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
