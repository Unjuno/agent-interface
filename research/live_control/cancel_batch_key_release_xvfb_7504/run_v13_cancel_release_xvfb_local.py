"""One nonformal isolated WSL-Xvfb check of v13 cancel key-release bounds.

No game, model, real desktop input, container, or shared X server is used.
This checks X server state/event delivery only and is not a formal allocation.
"""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import threading
import time
import traceback

from Xlib import X, XK, display
from input_owner_v13 import InputOwner


HERE = Path(__file__).resolve().parent
DISPLAY_NAME = ":99"
OUT = HERE / "RUN-REAL-XVFB-CANCEL-04.json"


class Lease:
    def __init__(self, focus):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.intent_token = "real-xvfb-cancel-01"
        self.cancel = threading.Event()
        self.expected_focus = focus
        self.interruption = None
        self.interrupted = threading.Event()

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("lease cancelled")

    def record_interruption(self, record):
        self.interruption = dict(record)
        self.interrupted.set()


def key_down(bits, code):
    return bool(bits[code // 8] & (1 << (code % 8)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    result = {
        "schema": "nonformal-real-xvfb-v13-cancel-release-v1",
        "run_id": "MAP01-V39-PERKEY-CANCEL-XVFB-LOCAL-04",
        "classification": "local WSL Xvfb source-bound smoke; not formal allocation",
        "display": DISPLAY_NAME,
        "status": "STOP",
        "limits": [
            "No game, model, external provider, user desktop input, or container",
            "X server request/state and test-client events only",
            "Not hardware transition, application effect, useful feedback, recovery, or MAP01 evidence",
        ],
        "source_sha256": {
            name: sha(HERE / name)
            for name in ("input_owner_v13.py", "input_owner_v11.py", "input_owner_v10.py")
        },
    }
    server = None
    owner = None
    observer = None
    query = None
    event_thread = None
    stop_events = threading.Event()
    observed = []
    server_pid = None
    try:
        display_number = DISPLAY_NAME.lstrip(":").split(".", 1)[0]
        socket_path = Path(f"/tmp/.X11-unix/X{display_number}")
        lock_path = Path(f"/tmp/.X{display_number}-lock")
        if socket_path.exists() or lock_path.exists():
            raise RuntimeError(f"private display {DISPLAY_NAME} is already occupied")
        server = subprocess.Popen(
            ["Xvfb", DISPLAY_NAME, "-screen", "0", "800x600x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        server_pid = server.pid
        result["xvfb_pid"] = server_pid
        result["xvfb_command"] = [
            "Xvfb", DISPLAY_NAME, "-screen", "0", "800x600x24", "-nolisten", "tcp"
        ]
        deadline = time.monotonic() + 3
        probe_connected = False
        while time.monotonic() < deadline and server.poll() is None:
            try:
                probe = display.Display(DISPLAY_NAME)
                probe.close()
                probe_connected = True
                break
            except Exception:
                time.sleep(0.02)
        if server.poll() is not None or not probe_connected:
            if server.poll() is None:
                server.terminate()
            _out, err = server.communicate(timeout=2)
            raise RuntimeError(
                "private Xvfb did not accept a client: " + (err or b"").decode("utf-8", "replace")[-1200:]
            )

        observer = display.Display(DISPLAY_NAME)
        screen = observer.screen()
        window = screen.root.create_window(
            20, 20, 240, 140, 0, X.CopyFromParent, X.InputOutput, X.CopyFromParent,
            event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        observer.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        observer.sync()
        focus_id = observer.get_input_focus().focus.id
        if focus_id != window.id:
            raise RuntimeError("observer test window did not receive input focus")

        query = display.Display(DISPLAY_NAME)
        keycode = observer.keysym_to_keycode(XK.string_to_keysym("w"))
        lease = Lease(focus_id)
        owner = InputOwner(DISPLAY_NAME)

        def collect_events():
            fd = observer.fileno()
            while not stop_events.is_set() or observer.pending_events():
                ready, _, _ = select.select([fd], [], [], 0.01)
                if not ready and not observer.pending_events():
                    continue
                while observer.pending_events():
                    event = observer.next_event()
                    if event.type in (X.KeyPress, X.KeyRelease):
                        observed.append({
                            "type": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                            "keycode": int(event.detail),
                            "received_ns": time.perf_counter_ns(),
                        })

        event_thread = threading.Thread(target=collect_events, daemon=False)
        event_thread.start()
        admission = owner.call("down", lease, "w")
        result["keycode"] = keycode
        result["admission"] = admission
        if admission.get("event") != "input_admission" or admission.get("key") != "w":
            raise RuntimeError("owner admission did not identify the requested key")

        deadline = time.monotonic() + 2
        while not any(e["type"] == "KeyPress" and e["keycode"] == keycode for e in observed):
            if time.monotonic() >= deadline:
                raise TimeoutError("focused test client did not receive KeyPress")
            time.sleep(0.001)
        pressed_state = key_down(query.query_keymap(), keycode)
        if not pressed_state:
            raise RuntimeError("server keymap did not show admitted key down")

        lease.cancel.set()
        if not lease.interrupted.wait(2):
            raise TimeoutError("owner did not record cancellation cleanup")
        release = lease.interruption
        result["owner_release"] = release
        released_state = key_down(query.query_keymap(), keycode)
        result["keymap_down_before_cancel"] = pressed_state
        result["keymap_down_after_cancel"] = released_state
        deadline = time.monotonic() + 2
        while not any(e["type"] == "KeyRelease" and e["keycode"] == keycode for e in observed):
            if time.monotonic() >= deadline:
                raise TimeoutError("focused test client did not receive KeyRelease")
            time.sleep(0.001)
        result["client_key_events"] = list(observed)
        bounds = release.get("key_release_intervals_ns", []) if release else []
        if len(bounds) != 1:
            raise RuntimeError("owner_release did not include one key-specific interval")
        item = bounds[0]
        lo, hi = item["interval_ns"]
        checks = {
            "admission_identity": admission.get("key") == "w" and item.get("keycode") == keycode,
            "cancelled_cause": release.get("reason") == "cancelled",
            "verified_empty": release.get("verified") is True and not released_state,
            "single_interval": len(bounds) == 1,
            "interval_order": type(lo) is int and type(hi) is int and lo <= hi,
            "sync_before_owner_verification": hi <= release.get("verified_ns", -1),
            "client_saw_press_and_release": any(e["type"] == "KeyPress" and e["keycode"] == keycode for e in observed)
                and any(e["type"] == "KeyRelease" and e["keycode"] == keycode for e in observed),
        }
        result["checks"] = checks
        result["status"] = "PASS_NONFORMAL_XVFB_SMOKE" if all(checks.values()) else "FAIL"
    except BaseException as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        result["traceback"] = traceback.format_exc()
    finally:
        stop_events.set()
        if owner is not None:
            try:
                owner.close()
            except BaseException as exc:
                result["owner_close_error"] = {"type": type(exc).__name__, "message": str(exc)}
        if event_thread is not None:
            event_thread.join(timeout=1)
            result["event_thread_stopped"] = not event_thread.is_alive()
        for conn in (query, observer):
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        if server is not None:
            server.terminate()
            try:
                _out, err = server.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                _out, err = server.communicate()
            result["xvfb_exit_code"] = server.returncode
            result["xvfb_stderr"] = (err or b"").decode("utf-8", "replace")[-1200:]
            result["xvfb_pid_stopped"] = server.poll() is not None
            result["xvfb_filesystem_socket_absent"] = not socket_path.exists()
            result["xvfb_lock_removed"] = not lock_path.exists()
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_NONFORMAL_XVFB_SMOKE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

