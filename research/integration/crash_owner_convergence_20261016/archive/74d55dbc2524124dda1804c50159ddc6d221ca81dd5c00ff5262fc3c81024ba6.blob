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
    lease.expected_surface = focus_id
    lease.expected_geometry = (20, 20, 300, 180)
    backend.lease = lease
    backend._input_event_context = ("v15-owner-a02", 0)
    backend.raw("a", True)
    backend.raw("d", True)
    backend.owner.call("button_down", lease, 1)
    with open(event_log, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"type": "armed", "owner_id": backend.owner.owner_id,
                                 "service_pid": backend.owner.service_pid,
                                 "display": display_name, "focus_id": focus_id,
                                 "intent_token": lease.intent_token, "keys": ["a", "d"], "button": 1}, sort_keys=True) + "\n")
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
        result = {"schema": "v39-v15-process-owner-xvfb-a15-raw-v1",
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
            from Xlib import X, Xatom
            from Xlib.display import Display
            from Xlib.ext import xtest
            focus = Display(display_name)
            root = focus.screen().root
            window = root.create_window(
                20, 20, 300, 180, 0, X.CopyFromParent, X.InputOutput,
                X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
            window.map()
            focus.set_input_focus(window, X.RevertToParent, X.CurrentTime)
            root.change_property(focus.intern_atom("_NET_ACTIVE_WINDOW"), Xatom.WINDOW,
                                 32, [window.id])
            window.warp_pointer(120, 90)
            focus.sync()
            focus_id = int(window.id)
            probe = Display(display_name)
            observer = Display(display_name)
            observed_window = observer.create_resource_object("window", focus_id)
            observed_window.change_attributes(
                event_mask=X.KeyPressMask | X.KeyReleaseMask | X.ButtonPressMask | X.ButtonReleaseMask)
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
            result["button_down_before_kill"] = bool(probe.screen().root.query_pointer().mask & X.Button1Mask)
            result["independent_keypress"] = key_press_events
            if not all(result["keymap_down_before_kill"].values()) or len(key_press_events) != len(keycodes) or not result["button_down_before_kill"]:
                raise RuntimeError("independent probe did not observe keys and button down")

            kill_requested_ns = time.perf_counter_ns()
            os.kill(service_pid, signal.SIGKILL)
            service_wait_status = signal.SIGKILL  # marks intentional kill; parent is session child
            owner_proc_state = None
            owner_proc_dead = False
            proc_deadline = time.monotonic() + 2
            while time.monotonic() < proc_deadline:
                try:
                    stat = Path(f"/proc/{service_pid}/stat").read_text()
                    owner_proc_state = stat[stat.rfind(")") + 2:].split()[0]
                    if owner_proc_state == "Z":
                        owner_proc_dead = True
                        break
                except FileNotFoundError:
                    owner_proc_dead = True
                    owner_proc_state = "absent"
                    break
                time.sleep(.01)
            result.update({"owner_kill_requested_ns": kill_requested_ns,
                           "owner_proc_state_after_kill": owner_proc_state,
                           "owner_proc_dead_or_zombie": owner_proc_dead,
                           "owner_kill_signal_sent": signal.SIGKILL})
            focus_after_owner_death = focus.get_input_focus().focus
            focus_after_owner_death = focus_after_owner_death.id if hasattr(focus_after_owner_death, "id") else focus_after_owner_death
            result["focus_identity_unchanged"] = focus_after_owner_death == focus_id
            if result["focus_identity_unchanged"] and owner_proc_dead:
                for code in keycodes.values():
                    xtest.fake_input(probe, X.KeyRelease, code)
                xtest.fake_input(probe, X.ButtonRelease, 1)
                probe.sync()
                result["supervisor_release_sent"] = True
            else:
                result["supervisor_release_sent"] = False
            release_events = {}
            button_release_event = None
            keymap_up_ns = {}
            button_up_ns = None
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                for key, code in keycodes.items():
                    if key not in keymap_up_ns and not key_down(probe, code):
                        keymap_up_ns[key] = time.perf_counter_ns()
                if button_up_ns is None and not (probe.screen().root.query_pointer().mask & X.Button1Mask):
                    button_up_ns = time.perf_counter_ns()
                ready, _, _ = select.select([observer], [], [], .05)
                if ready:
                    while observer.pending_events():
                        event = observer.next_event()
                        if event.type == X.KeyRelease and event.detail in keycodes.values():
                            release_events[event.detail] = {"type": event.type, "detail": event.detail,
                                                            "observed_ns": time.perf_counter_ns()}
                        elif event.type == X.ButtonRelease and event.detail == 1:
                            button_release_event = {"type": event.type, "detail": event.detail,
                                                    "observed_ns": time.perf_counter_ns()}
                if len(keymap_up_ns) == len(keycodes) and len(release_events) == len(keycodes) and button_up_ns is not None and button_release_event is not None:
                    break
                time.sleep(.01)
            result["independent_keyrelease"] = release_events
            result["keymap_up_observed_ns"] = keymap_up_ns
            result["independent_buttonrelease"] = button_release_event
            result["button_up_observed_ns"] = button_up_ns
            result["session_alive_after_owner_kill"] = session.poll() is None
            receipt_path = Path(ready_event["receipt_path"])
            result["receipt_exists_after_owner_kill"] = receipt_path.is_file()
            result["supervisor_emergency_release_pass"] = bool(
                result.get("owner_kill_signal_sent") == signal.SIGKILL and
                result.get("owner_proc_dead_or_zombie") is True and
                result.get("focus_identity_unchanged") is True and
                result.get("supervisor_release_sent") is True and
                len(key_press_events) == len(keycodes) and
                len(keymap_up_ns) == len(keycodes) and len(release_events) == len(keycodes) and
                button_release_event is not None and button_up_ns is not None and
                result["session_alive_after_owner_kill"] is True and
                result["receipt_exists_after_owner_kill"] is False)
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
            result["supervisor_emergency_release_pass"] = bool(
                result.get("supervisor_emergency_release_pass") and
                result["xvfb_termination_requested"] is True and
                result["xvfb_return_code"] in (0, -signal.SIGTERM) and
                result.get("forced_owner_kill") is False)
            if session is not None and session.returncode is not None:
                result["session_cleanup_return_code"] = session.returncode
        raw_path = OUT / "RAW.json"
        raw_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(json.dumps({"raw": str(raw_path),
                          "supervisor_emergency_release_pass": result.get("supervisor_emergency_release_pass", False),
                          "owner_service_return_code": result.get("owner_service_return_code"),
                          "service_wait_status": result.get("service_wait_status")},
                         sort_keys=True))
        if not result.get("supervisor_emergency_release_pass"):
            raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if RAW_RESULT is not None:
            RAW_RESULT["candidate_error"] = {
                "type": type(error).__name__, "message": str(error)[:1000]}
            RAW_RESULT["supervisor_emergency_release_pass"] = False
            raw_path = OUT / "RAW.json"
            if not raw_path.exists():
                raw_path.write_text(json.dumps(RAW_RESULT, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
        raise
