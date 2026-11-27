"""One-shot V15 process-backend/session-death test on private Xvfb."""
import ctypes
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import types

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
for path in (DOOM, LIVE, ROOT / "research" / "observation_tiles",
             ROOT / "research" / "observation_gating", ROOT / "research" / "real_apps_v1"):
    sys.path.insert(0, str(path))

# Pillow is absent from the base WSL Python. This isolated path tests only the
# backend's input composition; capture methods remain unreachable in both arms.
pil = types.ModuleType("PIL")
pil.__path__ = []
pil.Image = types.ModuleType("PIL.Image")
pil.Image.frombytes = lambda *_args, **_kwargs: (_ for _ in ()).throw(
    AssertionError("image capture is outside this candidate"))
pil.ImageGrab = types.ModuleType("PIL.ImageGrab")
pil.ImageGrab.grab = lambda **_kwargs: (_ for _ in ()).throw(
    AssertionError("image capture is outside this candidate"))
sys.modules.setdefault("PIL", pil)
sys.modules.setdefault("PIL.Image", pil.Image)
sys.modules.setdefault("PIL.ImageGrab", pil.ImageGrab)
suite_stub = types.ModuleType("gui_suite")
suite_stub.APPS = ()
sys.modules.setdefault("gui_suite", suite_stub)

OUT = Path(os.environ.get("V15_OWNER_OUT", ROOT / "research/doom/v39_v15_process_owner_xvfb_a06_20261012/results/A01"))
RAW_RESULT = None


def session_child(display_name, focus_id, out, event_log):
    import Xlib.display
    from doom_owner_thread_release_batch_backend_process_v1 import Backend
    from lease_release_v1 import Lease

    class Session:
        name = display_name
        def __init__(self):
            self.d = Xlib.display.Display(display_name)

    def emit(event):
        row = {"type": "backend_event", "event": event}
        with open(event_log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    backend = Backend(Session(), out, emit,
                      {"health": object(), "ammo": object()})
    lease = Lease(time.perf_counter_ns() + 25_000_000_000)
    lease.expected_focus = focus_id
    lease.expected_surface = None
    lease.expected_geometry = None
    backend.lease = lease
    backend._input_event_context = ("v15-owner-a02", 0)
    backend.raw("a", True)
    backend.raw("d", True)
    with open(event_log, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"type": "armed", "owner_id": backend.owner.owner_id,
                                 "service_pid": backend.owner.service_pid,
                                 "display": display_name, "focus_id": focus_id,
                                 "intent_token": lease.intent_token, "keys": ["a", "d"]}, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    while True:
        time.sleep(1)


def key_down(display_conn, keycode):
    bitmap = display_conn.query_keymap()
    return bool(bitmap[keycode // 8] & (1 << (keycode % 8)))


def wait_line(stream, timeout):
    ready, _, _ = select.select([stream], [], [], timeout)
    if not ready:
        raise TimeoutError("session child output deadline")
    line = stream.readline()
    if not line:
        raise EOFError("session child ended before armed record")
    return json.loads(line)


def main():
    global RAW_RESULT
    if sys.argv[1:] == ["--preflight"]:
        from doom_owner_thread_release_batch_backend_process_v1 import Backend
        print(json.dumps({"preflight": "BACKEND_IMPORT_OK",
                          "mro": [cls.__name__ for cls in Backend.__mro__[:5]]}))
        return
    if len(sys.argv) == 6 and sys.argv[1] == "--session-child":
        session_child(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]))
        return

    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER failed")

    OUT.mkdir(parents=True, exist_ok=False)
    event_log = OUT / "session-events.jsonl"
    child_stdout = OUT / "session.stdout.log"
    child_stderr = OUT / "session.stderr.log"
    with tempfile.TemporaryDirectory(prefix="v15-owner-a02-") as temp:
        auth = Path(temp) / "Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        xvfb = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env)
        session = None
        service_pid = None
        service_wait_status = None
        receipt = None
        result = {"schema": "v39-v15-process-owner-xvfb-a10-raw-v1",
                  "xvfb_pid": xvfb.pid, "xvfb_tcp_enabled": False,
                  "physical_input": False, "game_or_model": False,
                  "session_kill_signal": signal.SIGKILL,
                  "forced_owner_kill": False}
        RAW_RESULT = result
        try:
            ready, _, _ = select.select([xvfb.stdout], [], [], 5)
            if not ready:
                raise TimeoutError("Xvfb display allocation deadline")
            number = xvfb.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("Xvfb displayfd did not return a decimal display")
            display_name = ":" + number
            from Xlib import X
            from Xlib.display import Display
            focus = Display(display_name)
            root = focus.screen().root
            window = root.create_window(
                20, 20, 300, 180, 0, X.CopyFromParent, X.InputOutput,
                X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
            window.map()
            focus.set_input_focus(window, X.RevertToParent, X.CurrentTime)
            focus.sync()
            focus_id = int(window.id)
            probe = Display(display_name)
            observer = Display(display_name)
            observed_window = observer.create_resource_object("window", focus_id)
            observed_window.change_attributes(
                event_mask=X.KeyPressMask | X.KeyReleaseMask)
            observer.sync()
            keycodes = {key: probe.keysym_to_keycode(ord(key)) for key in ("a", "d")}
            result.update({"display": display_name, "focus_id": focus_id,
                           "keycodes": keycodes, "xvfb_displayfd_ready": True})

            stdout_file = child_stdout.open("wb")
            stderr_file = child_stderr.open("wb")
            session = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--session-child",
                 display_name, str(focus_id), str(OUT), str(event_log)],
                stdin=subprocess.DEVNULL, stdout=stdout_file,
                stderr=stderr_file, text=False, env=env, start_new_session=True)
            ready_event = None
            armed = None
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline and armed is None:
                rows = []
                if event_log.is_file():
                    rows = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
                for row in rows:
                    if row.get("type") == "backend_event":
                        event = row.get("event", {})
                        if event.get("event") == "input_owner_process_ready":
                            ready_event = event
                    elif row.get("type") == "armed":
                        armed = row
                if armed is None:
                    time.sleep(.05)
            if ready_event is None or armed is None:
                raise RuntimeError("backend did not publish owner readiness and held-key arm")
            service_pid = ready_event["service_pid"]
            result["ready_event"] = ready_event
            result["armed"] = armed
            key_press_events = {}
            press_deadline = time.monotonic() + .5
            while time.monotonic() < press_deadline and len(key_press_events) < len(keycodes):
                ready, _, _ = select.select([observer], [], [], .05)
                if ready:
                    while observer.pending_events():
                        event = observer.next_event()
                        if event.type == X.KeyPress and event.detail in keycodes.values():
                            key_press_events[event.detail] = {"type": event.type,
                                                              "detail": event.detail,
                                                              "observed_ns": time.perf_counter_ns()}
            result["keymap_down_before_kill"] = {key: key_down(probe, code) for key, code in keycodes.items()}
            result["independent_keypress"] = key_press_events
            if not all(result["keymap_down_before_kill"].values()) or len(key_press_events) != len(keycodes):
                raise RuntimeError("independent XQueryKeymap did not observe both admitted keys down")

            kill_requested_ns = time.perf_counter_ns()
            os.kill(session.pid, signal.SIGKILL)
            session_return = session.wait(timeout=3)
            result.update({"session_pid": session.pid, "session_return_code": session_return,
                           "kill_requested_ns": kill_requested_ns})
            release_events = {}
            keymap_up_ns = {}
            deadline = time.monotonic() + 6
            while time.monotonic() < deadline:
                for key, code in keycodes.items():
                    if key not in keymap_up_ns and not key_down(probe, code):
                        keymap_up_ns[key] = time.perf_counter_ns()
                ready, _, _ = select.select([observer], [], [], .05)
                if ready:
                    while observer.pending_events():
                        event = observer.next_event()
                        if event.type == X.KeyRelease and event.detail in keycodes.values():
                            release_events[event.detail] = {"type": event.type, "detail": event.detail,
                                                            "observed_ns": time.perf_counter_ns()}
                receipt_path = Path(ready_event["receipt_path"])
                if receipt_path.is_file() and len(keymap_up_ns) == len(keycodes) and len(release_events) == len(keycodes):
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                    try:
                        waited_pid, status = os.waitpid(service_pid, os.WNOHANG)
                    except ChildProcessError:
                        waited_pid, status = 0, None
                    if waited_pid == service_pid:
                        service_wait_status = status
                        break
                time.sleep(.01)

            result["independent_keyrelease"] = release_events
            result["keymap_up_observed_ns"] = keymap_up_ns
            result["receipt"] = receipt
            result["service_wait_status"] = service_wait_status
            receipt_keycodes = set()
            if receipt is not None:
                for row in receipt.get("release_records", []):
                    receipt_keycodes.update(row.get("key_release_attempts", {}).keys())
            required_keycodes = {str(code) for code in keycodes.values()}
            result["recovery_pass"] = bool(
                session_return == -signal.SIGKILL and len(keymap_up_ns) == len(keycodes) and
                len(release_events) == len(keycodes) and receipt is not None and
                len(key_press_events) == len(keycodes) and required_keycodes.issubset(receipt_keycodes) and
                receipt.get("recovery_verified") is True and
                receipt.get("service_pid") == service_pid and
                receipt.get("owner_id") == ready_event.get("owner_id") and
                receipt.get("display") == display_name and
                receipt.get("trigger") == "rpc_eof" and
                receipt.get("receipt_fsynced") is True and
                receipt.get("owner_thread_stopped") is True and
                service_wait_status is not None and os.WIFEXITED(service_wait_status) and
                os.WEXITSTATUS(service_wait_status) == 0 and
                all(row.get("verified") is True and row.get("keys_down") == [] and
                    row.get("buttons_down") == []
                    for row in receipt.get("release_records", [])) and
                bool(receipt.get("release_records")) and
                receipt["release_records"][-1].get("reason") == "close")
        finally:
            if session is not None and session.poll() is None:
                session.kill()
                session.wait(timeout=2)
            if service_pid is not None and service_wait_status is None:
                try:
                    os.kill(service_pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    os.kill(service_pid, signal.SIGTERM)
                    result["forced_owner_kill"] = True
                    reap_deadline = time.monotonic() + 2
                    while time.monotonic() < reap_deadline:
                        try:
                            waited_pid, status = os.waitpid(service_pid, os.WNOHANG)
                        except ChildProcessError:
                            break
                        if waited_pid == service_pid:
                            service_wait_status = status
                            result["service_wait_status"] = status
                            break
                        time.sleep(.02)
            result["xvfb_return_code"] = None
            if xvfb.poll() is None:
                result["xvfb_termination_requested"] = True
                xvfb.terminate()
                try:
                    result["xvfb_return_code"] = xvfb.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    xvfb.kill()
                    result["xvfb_return_code"] = xvfb.wait(timeout=3)
            if session is not None:
                result["session_stdout"] = child_stdout.read_text(encoding="utf-8", errors="replace") if child_stdout.exists() else ""
                result["session_stderr"] = child_stderr.read_text(encoding="utf-8", errors="replace") if child_stderr.exists() else ""
                if session.stdout is not None:
                    session.stdout.close()
                if session.stderr is not None:
                    session.stderr.close()
            result["xvfb_stderr"] = xvfb.stderr.read()
            xvfb.stdout.close()
            xvfb.stderr.close()
            result["recovery_pass"] = bool(
                result.get("recovery_pass") and
                result["xvfb_termination_requested"] is True and
                result["xvfb_return_code"] in (0, -signal.SIGTERM) and
                result.get("forced_owner_kill") is False)
        raw_path = OUT / "RAW.json"
        raw_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(json.dumps({"raw": str(raw_path),
                          "recovery_pass": result.get("recovery_pass", False),
                          "session_return_code": result.get("session_return_code"),
                          "service_wait_status": result.get("service_wait_status")},
                         sort_keys=True))
        if not result.get("recovery_pass"):
            raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if RAW_RESULT is not None:
            RAW_RESULT["candidate_error"] = {
                "type": type(error).__name__, "message": str(error)[:1000]}
            RAW_RESULT["recovery_pass"] = False
            raw_path = OUT / "RAW.json"
            if not raw_path.exists():
                raw_path.write_text(json.dumps(RAW_RESULT, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
        raise
