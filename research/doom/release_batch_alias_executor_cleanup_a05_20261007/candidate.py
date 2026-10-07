#!/usr/bin/env python3
"""One-shot V13/V15 fake-X alias refusal and executor cleanup composition probe."""
from __future__ import annotations

import json
import ast
import pathlib
import sys
import threading
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "guarded"), str(HERE / "source" / "current")]

X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                          ButtonRelease=5, MotionNotify=6, Button1Mask=256,
                          AnyPropertyType=0, IsViewable=2)
active_display = None
drop_key_release = False
dropped_keyrelease_count = 0
server_down = set()


class Focus:
    id = 41


class Pointer:
    mask = 0
    root_x = 10
    root_y = 10


class Root:
    def query_pointer(self):
        return Pointer()

    def translate_coords(self, _window, x, y):
        return types.SimpleNamespace(x=x, y=y)


class Screen:
    root = Root()


class FakeDisplay:
    def __init__(self, _name):
        global active_display
        active_display = self
        self.down = server_down
        self.closed = False

    def get_input_focus(self):
        return types.SimpleNamespace(focus=Focus())

    def keysym_to_keycode(self, _sym):
        return 38

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return Screen()

    def sync(self):
        pass

    def close(self):
        self.closed = True

    def create_resource_object(self, _kind, _ident):
        return types.SimpleNamespace(
            get_attributes=lambda: types.SimpleNamespace(map_state=X.IsViewable),
            get_geometry=lambda: types.SimpleNamespace(x=0, y=0, width=100, height=100),
            query_tree=lambda: types.SimpleNamespace(parent=types.SimpleNamespace(id=1)),
        )


def fake_input(display, event, code, **_kwargs):
    global drop_key_release, dropped_keyrelease_count
    if event == X.KeyPress:
        display.down.add(code)
    elif event == X.KeyRelease:
        if drop_key_release:
            drop_key_release = False
            dropped_keyrelease_count += 1
        else:
            display.down.discard(code)


def install_xlib():
    xlib = types.ModuleType("Xlib")
    xlib.X = X
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda _key: 1)
    xlib.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                      BadDrawable=type("BadDrawable", (Exception,), {}))
    display = types.ModuleType("Xlib.display")
    display.Display = FakeDisplay
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.display, xlib.ext = display, ext
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                        "Xlib.XK": types.ModuleType("Xlib.XK"),
                        "Xlib.error": types.ModuleType("Xlib.error"),
                        "Xlib.display": display, "Xlib.ext": ext,
                        "Xlib.ext.xtest": xtest})
    xlib.X, xlib.XK = X, types.SimpleNamespace(string_to_keysym=lambda _key: 1)


def sha(path):
    import hashlib
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def install_production_owner(owner_cls):
    # Build the unchanged transition-composed V12 owner with fake-X providers.
    from input_transition_owner_v4 import InputOwner as ProductionTransitionOwner
    owner = ProductionTransitionOwner("FAKE", _owner_cls=owner_cls)
    return owner


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()
        self.intent_token = "v15-loss-probe-a09"
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        pass

    def interruption_snapshot(self):
        return None

    def record_interruption(self, _row):
        pass

    def is_set(self):
        return self.cancel.is_set()

    def wait(self, seconds):
        return self.cancel.wait(seconds)

    def set(self):
        self.cancel.set()

    def wait_interruption(self, _seconds):
        return None


class DummyOwner:
    def __init__(self, _display_name=None):
        pass

    def close(self):
        pass


class ControllerBackend:
    """Test-only action-loop double; production execute/raw methods remain loaded."""
    def __init__(self, session, _out, emit, _signal_readers):
        # Production V2 immediately closes the constructor owner before
        # installing the selected V11/V4 transition owner.
        self.owner = DummyOwner()
        self.lease = Lease()
        self.held = set()
        self.sequence = 0
        self.emit = emit
        self.session = session
        self._input_event_context = None
        self.touched = set()

    def execute(self, step, _cancel, _identifier, _index):
        # Match the production session_v7 pre-input contract that the A07
        # controller double bypassed: bind an observed focus and reject drift.
        if not hasattr(_cancel, "expected_focus"):
            observed = self.session.context().get("focus")
            actual = self.session.d.get_input_focus().focus.id
            if observed in (None, 0, 1) or actual != observed:
                raise ValueError("fake observed-focus admission failed")
            _cancel.expected_focus = observed
        previous_context = self._input_event_context
        self._input_event_context = (_identifier, _index)
        try:
            for key, down in step["actions"]:
                self.raw(key, down)
        finally:
            self._input_event_context = previous_context
        return {"executed": len(step["actions"])}

    def validate(self, _steps):
        return None

    # release_all matches the production owner-RPC seam; V15 overrides it.
    def release_all(self):
        return self.owner.call("release", self.lease)


class Session:
    name = "FAKE"

    def __init__(self):
        self.d = FakeDisplay("FAKE_SESSION")
        self.context = lambda: {"focus": 41, "surface": 42,
                                "geometry": [0, 0, 100, 100]}


def install_production_backend_imports():
    # Isolate the real V2/V15 selected backend from ViZDoom/session setup. The
    # base backend supplies only the action loop above; all selected release
    # composition methods and V4→V3→V12 owner code are imported from source.
    base = types.ModuleType("doom_typed_release_backend_v1")
    base.Backend = ControllerBackend
    base.suite = object()
    sys.modules["doom_typed_release_backend_v1"] = base
    # Replace only the imported Xlib binding used by production owner code.
    import input_owner_v12
    input_owner_v12.X = X
    input_owner_v12.XK = sys.modules["Xlib"].XK
    input_owner_v12.display = types.SimpleNamespace(Display=FakeDisplay)
    input_owner_v12.error = types.SimpleNamespace(
        BadWindow=type("BadWindow", (Exception,), {}),
        BadDrawable=type("BadDrawable", (Exception,), {}))
    input_owner_v12.xtest = types.SimpleNamespace(fake_input=fake_input)
    base.InputOwner = lambda name: install_production_owner(
        input_owner_v12.InputOwner)

    def release_all(self):
        return self.owner.call("release", self.lease)
    ControllerBackend.release_all = release_all


def run_case(drop):
    global drop_key_release, dropped_keyrelease_count
    drop_key_release = drop
    dropped_keyrelease_count = 0
    from doom_owner_thread_release_batch_backend_v1 import Backend

    emitted = []
    backend = Backend(Session(), None, emitted.append, {})
    backend.owner = install_production_owner(
        __import__("input_owner_v12").InputOwner)
    backend.touched = set()
    from executor_v13 import Executor
    engine = Executor(backend, emitted.append)
    try:
        identifier = "lost-up-case-a09" if drop else "normal-case-a09"
        engine.submit(identifier, [{"op": "key_batch", "actions": [("F8", True), ("F8", False)]}],
                      expected_sequence=backend.sequence,
                      valid_until_ns=time.perf_counter_ns() + 10_000_000_000)
        deadline = time.monotonic() + 3
        terminal = None
        while time.monotonic() < deadline:
            terminal = next((row for row in emitted if row.get("event") == "terminal"), None)
            if terminal is not None:
                break
            time.sleep(0.005)
        if terminal is None:
            raise RuntimeError("V13 executor did not publish terminal within 3 seconds")
        engine.close()
        server_down_after_executor_release = sorted(server_down)
        release_rows = [r for r in emitted if r.get("event") == "input_release_transition"]
        batch = release_rows[0] if len(release_rows) == 1 else None
        owner_close_error = None
        try:
            backend.owner.close()
        except Exception as exc:
            owner_close_error = f"{type(exc).__name__}: {exc}"
        resource_observation = {}
        for rel in ("/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/memory.max",
                    "/sys/fs/cgroup/memory.swap.max", "/sys/fs/cgroup/cgroup.controllers"):
            path = pathlib.Path(rel)
            try:
                resource_observation[rel] = path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                resource_observation[rel] = f"unavailable:{type(exc).__name__}"
        return {
            "injected_keyrelease_loss": drop,
            "dropped_keyrelease_count": dropped_keyrelease_count,
            "events": emitted,
            "server_keycodes_down_after_executor_release": server_down_after_executor_release,
            "release_row": batch,
            "executor_terminal": terminal,
            "base_backend_touched_after_batch": sorted(backend.touched),
            "owner_close_error": owner_close_error,
            "owner_close_recovered": not server_down,
            "container_resource_observation": resource_observation,
        }
    finally:
        try:
            if backend.owner is not None:
                backend.owner.close()
        except Exception:
            pass


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["source_sha256"].items():
        if sha(HERE / relative) != expected:
            raise SystemExit("frozen source SHA mismatch: " + relative)
    install_xlib()
    install_production_backend_imports()
    # Import the pinned selected backend after test-only dependencies are set.
    results = run_alias_executor_case()
    out = pathlib.Path(__import__("os").environ["A05_OUT"]) / "A05_RAW.json"
    out.write_text(json.dumps({"schema": "v39-v15-v13-alias-cleanup-a05-raw-v1",
                               "run_id": "a05-current-main-20261007-one-shot",
                               "source_base": "decc1896e3e85ab2fdbb7ec4678f958eb6561d0f",
                               "claims": {"real_x11": False, "gui": False,
                                          "doom": False, "model": False,
                                          "physical_keyboard": False,
                                          "application_effect": False},
                               "case": results}, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"raw": str(out),
                      "server_down_after_executor_cleanup": results["server_keycodes_down_after_executor_cleanup"],
                      "terminal_status": results["executor_terminal"].get("status")}))


def run_alias_executor_case():
    from doom_owner_thread_release_batch_backend_v1 import Backend
    emitted = []
    backend = Backend(Session(), None, emitted.append, {})
    backend.owner = install_production_owner(__import__("input_owner_v12").InputOwner)
    from executor_v13 import Executor
    engine = Executor(backend, emitted.append)
    identifier = "alias-refusal-executor-cleanup-a05"
    step = {"op": "key_batch", "actions": [("a", True), ("A", True),
                                                   ("a", False), ("A", False)]}
    engine.submit(identifier, [step], expected_sequence=backend.sequence,
                  valid_until_ns=time.perf_counter_ns() + 10_000_000_000)
    deadline = time.monotonic() + 3
    terminal = None
    while time.monotonic() < deadline:
        terminal = next((row for row in emitted if row.get("event") == "terminal"), None)
        if terminal is not None:
            break
        time.sleep(0.005)
    if terminal is None:
        raise RuntimeError("V13 executor did not publish terminal within 3 seconds")
    engine.close()
    server_down_after_cleanup = sorted(server_down)
    release_rows = [row for row in emitted if row.get("event") == "input_release_transition"]
    close_error = None
    try:
        backend.owner.close()
    except Exception as exc:
        close_error = f"{type(exc).__name__}: {exc}"
    return {"actions": step["actions"], "resolved_alias_keycodes": {"a": 38, "A": 38},
            "emitted_events": emitted, "release_rows": release_rows,
            "server_keycodes_down_after_executor_cleanup": server_down_after_cleanup,
            "executor_terminal": terminal, "owner_close_error": close_error}


if __name__ == "__main__":
    main()
