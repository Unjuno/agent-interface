"""Run pinned InputOwner through two explicit W cycles on a fake Xlib."""
import hashlib
import importlib.util
import json
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "dependencies" / "input_owner_v11.py"
CASES = HERE / "cases.json"
OUT = HERE / "results" / "t1-01" / "raw.json"


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.events = []
        self.keymap_queries = []

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, symbol):
        return {"W": 25}.get(symbol, 0)

    def sync(self):
        return None

    def screen(self):
        return types.SimpleNamespace(root=types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0)))

    def query_keymap(self):
        bitmap = bytearray(32)
        for keycode in self.down:
            bitmap[keycode // 8] |= 1 << (keycode % 8)
        self.keymap_queries.append({"keys_down": sorted(self.down)})
        return bytes(bitmap)

    def close(self):
        return None


class Lease:
    def __init__(self):
        self.expected_focus = 42
        self.intent_token = "intent-repeat-w"
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("fake lease expired")


def install_fake_xlib(state):
    X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
        ButtonRelease=5, MotionNotify=6, Button1Mask=256, AnyPropertyType=0,
        IsViewable=2)
    XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
    display = types.ModuleType("Xlib.display")
    display.Display = lambda _name: state
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(_display, event, detail, **_kwargs):
        if event == X.KeyPress:
            state.down.add(detail)
        elif event == X.KeyRelease:
            state.down.discard(detail)
        state.events.append({"event": event, "detail": detail,
                             "monotonic_ns": time.perf_counter_ns()})

    xtest.fake_input = fake_input
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = xtest
    xlib = types.ModuleType("Xlib")
    xlib.X, xlib.XK, xlib.display, xlib.error = X, XK, display, error
    sys.modules.update({"Xlib": xlib, "Xlib.display": display,
        "Xlib.error": error, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor


def main():
    case_bytes = CASES.read_bytes()
    bundle = json.loads(case_bytes.decode("utf-8"))
    fake = FakeDisplay()
    install_fake_xlib(fake)
    spec = importlib.util.spec_from_file_location("pinned_input_owner_v11", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    owner = module.InputOwner("fake-display")
    lease = Lease()
    admissions = [owner.call("down", lease, "W")]
    owner.call("up", lease, "W")
    admissions.append(owner.call("down", lease, "W"))
    owner.call("up", lease, "W")
    owner.close()
    names = {2: "KeyPress", 3: "KeyRelease"}
    payload = {
        "schema": "map01-owner-occurrence-binding-raw-v1",
        "allocation_id": bundle["allocation_id"],
        "main_sha": "9ac1024e66b2fe72064e7719a5dec2ba026b32d7",
        "owner_source_commit": bundle["owner_source_commit"],
        "owner_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "candidate_invocations": 1,
        "retries": 0,
        "admissions": admissions,
        "owner_id": owner.owner_id,
        "owner_records": owner.records,
        "fake_server_events": [{**event, "event": names.get(event["event"], "other")}
                                for event in fake.events],
        "fake_keymap_queries": fake.keymap_queries,
        "fake_server_final_keys_down": sorted(fake.down),
        "scope": "unchanged InputOwner Python path with in-process fake Xlib transport",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
