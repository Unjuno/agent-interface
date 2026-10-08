"""One-shot construction candidate for the isolated instrumented owner copy."""
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
OUT = HERE / "results" / "t2-01" / "raw.json"


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
        data = bytes(bitmap)
        self.keymap_queries.append({"bitmap_hex": data.hex(),
                                    "keys_down": sorted(self.down)})
        return data

    def close(self):
        return None


class Lease:
    expected_focus = 42
    intent_token = "t2-repeat-w"

    def __init__(self):
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
    cases = json.loads(case_bytes.decode("utf-8"))
    fake = FakeDisplay()
    install_fake_xlib(fake)
    spec = importlib.util.spec_from_file_location("isolated_instrumented_owner", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    owner = module.InputOwner("fake-display")
    lease = Lease()
    admissions = [owner.call("down", lease, "W")]
    owner.call("up", lease, "W")
    admissions.append(owner.call("down", lease, "W"))
    owner.call("up", lease, "W")
    owner.close()
    raw = {
        "schema": "map01-owner-instrumentation-raw-v1",
        "allocation_id": cases["allocation_id"],
        "main_sha": "3adec9cdc2cff5ef68f19acd55c5823fcaad26df",
        "upstream_owner_commit": cases["upstream_owner_commit"],
        "upstream_owner_blob_sha1": cases["upstream_owner_blob_sha1"],
        "patched_owner_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "candidate_invocations": 1,
        "retries": 0,
        "owner_id": owner.owner_id,
        "admissions": admissions,
        "owner_records": owner.records,
        "fake_server_events": fake.events,
        "fake_keymap_queries": fake.keymap_queries,
        "fake_server_final_keys_down": sorted(fake.down),
        "scope": "isolated patched InputOwner prototype on in-process fake Xlib",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    main()
