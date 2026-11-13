"""One-shot fake-display construction of the selected V39 key method/owner pair."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results" / "candidate-a01"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_sources() -> None:
    for relative, expected in FREEZE["source_sha256"].items():
        if digest(ROOT / relative) != expected:
            raise RuntimeError(f"frozen source mismatch: {relative}")
    for relative, expected in FREEZE["package_sha256"].items():
        if digest(HERE / relative) != expected:
            raise RuntimeError(f"frozen package mismatch: {relative}")


class FakeServer:
    def __init__(self, fail_keymap_on: int | None = None):
        self.physical: set[int] = set()
        self.operations: list[dict] = []
        self.query_count = 0
        self.fail_keymap_on = fail_keymap_on
        self.lock = threading.Lock()

    def note(self, operation: str, **fields) -> None:
        with self.lock:
            self.operations.append({"operation": operation,
                                    "at_ns": time.perf_counter_ns(), **fields})


class FakeDisplay:
    def __init__(self, server: FakeServer, _name: str):
        self.server = server
        self.root = types.SimpleNamespace(query_pointer=self.query_pointer)

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, symbol):
        return {"F8": 74, "space": 65}[symbol]

    def sync(self) -> None:
        self.server.note("sync")

    def query_keymap(self) -> bytes:
        with self.server.lock:
            self.server.query_count += 1
            ordinal = self.server.query_count
            failure = ordinal == self.server.fail_keymap_on
            self.server.operations.append({
                "operation": "keymap-query", "ordinal": ordinal,
                "at_ns": time.perf_counter_ns(),
                "outcome": "injected-unavailable" if failure else "returned",
            })
            if failure:
                raise RuntimeError("injected aggregate keymap query failure")
            bitmap = bytearray(32)
            for code in self.server.physical:
                bitmap[code // 8] |= 1 << (code % 8)
            return bytes(bitmap)

    def query_pointer(self):
        self.server.note("pointer-query")
        return types.SimpleNamespace(mask=0)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def close(self) -> None:
        self.server.note("display-close")


def install_fake_xlib(server: FakeServer):
    x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                              ButtonRelease=5, Button1Mask=1,
                              AnyPropertyType=0, IsViewable=2, MotionNotify=6)
    xk = types.SimpleNamespace(string_to_keysym=lambda value: value)
    display = types.SimpleNamespace(Display=lambda name: FakeDisplay(server, name))
    error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                  BadDrawable=type("BadDrawable", (Exception,), {}))
    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X, xlib.XK, xlib.display, xlib.error = x, xk, display, error
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(display_obj, event_type, code, **_kwargs):
        operation = "key-down" if event_type == x.KeyPress else "key-up"
        display_obj.server.note(operation, keycode=code)
        with display_obj.server.lock:
            if event_type == x.KeyPress:
                display_obj.server.physical.add(code)
            elif event_type == x.KeyRelease:
                display_obj.server.physical.discard(code)
            else:
                raise AssertionError(f"unexpected fake XTest event {event_type}")

    xtest.fake_input = fake_input
    sys.modules.update({"Xlib": xlib, "Xlib.ext": ext,
                        "Xlib.ext.xtest": xtest})
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor


class Lease:
    def __init__(self):
        self.expected_focus = 42
        self.intent_token = "v39-direct-key-a01"
        self.deadline = time.perf_counter_ns() + 30_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self) -> None:
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("fixture lease expired")

    def record_interruption(self, record) -> None:
        self.interruption = dict(record)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_selected_backend_and_owner():
    """Load session_v5's real methods; each case loads the exact V10 owner."""
    parent = types.ModuleType("session_v4")
    parent.Backend = type("SessionV4BackendStub", (), {})
    parent.suite = types.SimpleNamespace()
    sys.modules["session_v4"] = parent
    owner_stub = types.ModuleType("input_owner")
    owner_stub.InputOwner = object
    sys.modules["input_owner"] = owner_stub
    backend_path = ROOT / "research" / "live_control" / "session_v5.py"
    backend_module = load_module(backend_path, "session_v5_selected_methods_a01")
    owner_path = ROOT / "research" / "live_control" / "input_owner_v10.py"
    return backend_module.Backend, owner_path


def run_case(backend_type, owner_path: Path, fail_first_query: bool) -> dict:
    server = FakeServer(fail_keymap_on=1 if fail_first_query else None)
    install_fake_xlib(server)
    owner_module = load_module(
        owner_path, "input_owner_v10_a01_" + ("fault" if fail_first_query else "control"))
    backend = backend_type.__new__(backend_type)
    backend.held = set()
    backend.touched = set()
    backend.lease = Lease()
    events: list[dict] = []
    backend.emit = events.append
    backend.owner = owner_module.InputOwner(":fake")

    for key, down in (("F8", True), ("space", True),
                      ("space", False), ("F8", False)):
        backend.raw(key, down)
    before_release = len(server.operations)
    held_before_release_all = sorted(backend.held)
    release_result = None
    release_error = None
    try:
        release_result = backend.release_all()
    except Exception as exc:
        release_error = type(exc).__name__
    after_release = len(server.operations)
    held_after_release_all = sorted(backend.held)
    physical_after_release_all = sorted(server.physical)
    records_before_close = list(backend.owner.records)

    close_error = None
    try:
        backend.owner.close()
    except Exception as exc:
        close_error = type(exc).__name__
    return {
        "operations": server.operations,
        "release_operation_start": before_release,
        "release_operation_end": after_release,
        "events": events,
        "held_before_release_all": held_before_release_all,
        "held_after_release_all": held_after_release_all,
        "physical_after_release_all": physical_after_release_all,
        "owner_records_before_close": records_before_close,
        "owner_records_after_close": list(backend.owner.records),
        "owner_stopped_after_close": backend.owner.stopped.is_set(),
        "release_result": release_result,
        "release_error_type": release_error,
        "close_error_type": close_error,
        "physical_after_close": sorted(server.physical),
        "held_after_close": sorted(backend.held),
    }


def main() -> int:
    if OUT.exists():
        raise RuntimeError("candidate output already exists; refusing to overwrite")
    verify_frozen_sources()
    backend_type, owner_path = load_selected_backend_and_owner()
    cases = {
        "control": run_case(backend_type, owner_path, fail_first_query=False),
        "aggregate_query_failure": run_case(backend_type, owner_path, fail_first_query=True),
    }
    raw = {
        "schema": "map01-v39-selected-key-owner-raw-v1",
        "run_id": FREEZE["run_id"],
        "base_commit": FREEZE["base_commit"],
        "candidate_invocations": 1,
        "cases": cases,
        "environment": {"fake_xlib": True, "x_server": False,
                         "os_input": False, "vizdoom": False,
                         "model_calls": 0, "container": False},
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                                   encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_RETAINED",
                      "cases": list(cases),
                      "output": str(OUT / "raw.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
