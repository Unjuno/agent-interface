"""Two-occurrence real-Xvfb keymap witness using the v39 backend raw path."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time
import types
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "cases.json"
STARTED_PATH = ROOT / "candidate.started.json"
RAW_PATH = ROOT / "candidate.raw.json"
FREEZE_PATH = ROOT / "FREEZE.json"
ENVIRONMENT_PATH = ROOT / "ENVIRONMENT.json"
SOURCES = ROOT / "sources"


class Lease:
    def __init__(self, token, focus):
        self.intent_token = token
        self.expected_focus = focus
        self.deadline = time.perf_counter_ns() + 8_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("construction lease expired")


def source_digests():
    result = {}
    for path in sorted(SOURCES.iterdir()):
        if path.is_file():
            result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_freeze(freeze):
    for rel, expected in freeze["sha256"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("STOP_SOURCE_DRIFT:" + rel)


def keymap_sample(probe, keycode):
    started = time.perf_counter_ns()
    values = probe.query_keymap()
    finished = time.perf_counter_ns()
    bitmap = bytes(values)
    keys_down = [code for code in range(256)
                 if bitmap[code // 8] & (1 << (code % 8))]
    return {
        "sample_started_ns": started,
        "bitmap_hex": bitmap.hex(),
        "bitmap_sha256": hashlib.sha256(bitmap).hexdigest(),
        "keycode": keycode,
        "key_down": bool(bitmap[keycode // 8] & (1 << (keycode % 8))),
        "keys_down": keys_down,
        "sample_finished_ns": finished,
    }


def load_runtime(display_name):
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor
    sys.path.insert(0, str(SOURCES))

    base = types.ModuleType("doom_typed_release_backend_v1")
    base.Backend = type("BaseBackend", (), {})
    base.suite = object()
    sys.modules["doom_typed_release_backend_v1"] = base

    wrapper_spec = importlib.util.spec_from_file_location(
        "input_transition_owner_v3", SOURCES / "input_transition_owner_v3.py")
    wrapper = importlib.util.module_from_spec(wrapper_spec)
    wrapper_spec.loader.exec_module(wrapper)
    sys.modules["input_transition_owner_v3"] = wrapper

    backend_spec = importlib.util.spec_from_file_location(
        "doom_typed_release_backend_v3", SOURCES / "doom_typed_release_backend_v3.py")
    backend_module = importlib.util.module_from_spec(backend_spec)
    backend_spec.loader.exec_module(backend_module)
    backend = backend_module.Backend.__new__(backend_module.Backend)
    backend.owner = wrapper.InputOwner(display_name)
    backend.held = set()
    backend._release_batch = threading.local()
    backend.emit = lambda row: events.append(dict(row))
    backend.lease = None
    return backend, events


def main():
    cases_bytes = CASES_PATH.read_bytes()
    cases = json.loads(cases_bytes.decode("utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    started = {
        "schema": "map01-v39-owner-keymap-witness-started-v1",
        "allocation_id": cases["allocation_id"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_invocation": 1,
        "source_sha256": source_digests(),
        "freeze_sha256": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        "environment_sha256": hashlib.sha256(ENVIRONMENT_PATH.read_bytes()).hexdigest(),
        "network_isolation": freeze["network_isolation"],
        "xvfb_tcp_enabled": False,
    }
    with STARTED_PATH.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(started, sort_keys=True, indent=2) + "\n")

    raw = {
        "schema": "map01-v39-owner-keymap-witness-raw-v1",
        "allocation_id": cases["allocation_id"],
        "candidate_invocations": 1,
        "source_sha256": source_digests(),
        "freeze_sha256": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        "environment_sha256": hashlib.sha256(ENVIRONMENT_PATH.read_bytes()).hexdigest(),
        "candidate_complete": False,
        "failure": None,
    }
    proc = owner = probe = None
    temp = tempfile.TemporaryDirectory(prefix="v39-keymap-c02-")
    try:
        verify_freeze(freeze)
        from Xlib import XK, display
        xvfb_args = ["Xvfb", "-displayfd", "1", "-screen", "0",
                     cases["xvfb_screen"], "-nolisten", "tcp", "-ac"]
        env = dict(os.environ, XAUTHORITY=str(Path(temp.name) / "empty.Xauthority"))
        Path(env["XAUTHORITY"]).write_bytes(b"")
        proc = subprocess.Popen(xvfb_args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        ready, _, _ = select.select([proc.stdout], [], [], 5)
        if not ready:
            raise TimeoutError("Xvfb startup timeout")
        display_number = proc.stdout.readline().strip()
        if not display_number.isdecimal():
            raise RuntimeError("Xvfb returned invalid display number")
        display_name = ":" + display_number
        probe = display.Display(display_name)
        focus = probe.get_input_focus().focus
        focus_id = focus.id if hasattr(focus, "id") else focus
        keycode = probe.keysym_to_keycode(XK.string_to_keysym(cases["key"]))
        if keycode <= 0:
            raise RuntimeError("Xvfb has no keycode for frozen key")
        if keycode != cases["expected_keycode"]:
            raise RuntimeError("Xvfb keymap differs from frozen keycode")
        backend, events = load_runtime(display_name)
        backend.owner = backend.owner
        owner = backend.owner
        backend.owner_id = owner.owner_id
        before = keymap_sample(probe, keycode)
        if before["key_down"]:
            raise RuntimeError("key already down before first occurrence")

        occurrences = []
        for index in range(cases["occurrences"]):
            token = cases["allocation_id"] + f":{index + 1:02d}"
            lease = Lease(token, focus_id)
            backend.lease = lease
            backend._release_batch.context = {
                "rows": [], "identifier": token, "step": index
            }
            pre = keymap_sample(probe, keycode)
            backend.raw(cases["key"], True)
            down = keymap_sample(probe, keycode)
            backend.raw(cases["key"], False)
            backend.owner.call("release", lease)
            up = keymap_sample(probe, keycode)
            occurrences.append({"occurrence": index + 1, "intent_token": token,
                                "pre_down": pre, "post_down": down, "post_up": up})

        owner_state_before_close = owner.call("input_state")
        owner.close()
        owner_records_after_close = owner.records
        probe.close()
        probe = None
        owner = None
        time.sleep(0.05)
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=3)
        stderr = proc.stderr.read() if proc.stderr else ""
        raw.update({
            "candidate_complete": True,
            "xvfb_argv": xvfb_args,
            "xvfb_tcp_enabled": False,
            "xvfb_display_number": int(display_number),
            "xvfb_pid": proc.pid,
            "xvfb_exit_code_after_controlled_terminate": proc.returncode,
            "xvfb_stderr": stderr,
            "xvfb_stderr_fatal": "Fatal server error" in stderr,
            "xvfb_socket_removed": not (Path("/tmp/.X11-unix") / ("X" + str(display_number))).exists(),
            "xvfb_lock_removed": not (Path("/tmp") / (".X" + str(display_number) + "-lock")).exists(),
            "xvfb_displayfd_ready": True,
            "xvfb_keycode": keycode,
            "occurrences": occurrences,
            "events": events,
            "owner_records": owner_records_after_close,
            "owner_state_before_close": owner_state_before_close,
            "scope": "actual current-main InputOwner v10 on private Xvfb; backend raw method exercised; base initializer stubbed",
        })
    except BaseException as exc:
        raw["failure"] = repr(exc)
    finally:
        if probe is not None:
            try: probe.close()
            except Exception: pass
        if owner is not None:
            try:
                owner.close()
                raw["owner_records_after_cleanup"] = owner.records
            except Exception as exc: raw["cleanup_failure"] = repr(exc)
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=3)
            except Exception: proc.kill(); proc.wait(timeout=3)
        temp.cleanup()
        raw["xvfb_exit_code_after_cleanup"] = proc.returncode if proc is not None else None
        with RAW_PATH.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps(raw, sort_keys=True))
    raise SystemExit(0 if raw["candidate_complete"] and raw["failure"] is None else 1)


if __name__ == "__main__":
    events = []
    main()
