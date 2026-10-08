"""Run one frozen-source fake-Xlib caller/owner-thread construction case."""
import argparse
import hashlib
import json
import sys
import threading
import time
import types
import uuid
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent
REPOSITORY = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
EXPECTED_SOURCES = {
    "input_owner_v10.py": {
        "git_blob": "341b3c01649943ddaad5f28431a792c4889cc36e",
        "sha256": "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
    },
    "input_owner_v11.py": {
        "git_blob": "842071284156d3ccc647f47135ee62a9e512cb56",
        "sha256": "4f6b61026117d4d9be8a973c65d491fe8a9b0ebbc90bd98c0738cd0aac09821c",
    },
}


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def check_sources():
    for name, expected in EXPECTED_SOURCES.items():
        path = LIVE / name
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise RuntimeError(f"frozen source SHA-256 mismatch: {path}")
        if git_blob_sha(data) != expected["git_blob"]:
            raise RuntimeError(f"frozen source Git blob mismatch: {path}")


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0, root_x=0, root_y=0)


class FakeDisplay:
    def __init__(self, display_name, event_sink):
        self.display_name = display_name
        self.event_sink = event_sink
        self.pressed = set()
        self.root = FakeRoot()
        self.closed = False

    def get_input_focus(self):
        return types.SimpleNamespace(focus=types.SimpleNamespace(id=1))

    def keysym_to_keycode(self, symbol):
        return {"a": 38}.get(symbol, 0)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.pressed:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        time.sleep(0.002)
        self.event_sink.append({
            "kind": "sync_return",
            "sync_return_ns": time.perf_counter_ns(),
            "thread_name": threading.current_thread().name,
        })

    def close(self):
        self.closed = True


class FakeXlib:
    def __init__(self):
        self.displays = []
        self.events = []
        self.X = types.SimpleNamespace(
            KeyPress=2, KeyRelease=3, ButtonPress=4, ButtonRelease=5,
            Button1Mask=256, AnyPropertyType=0, IsViewable=2,
            CopyFromParent=0, InputOutput=1, RevertToParent=0, CurrentTime=0,
            MotionNotify=6,
        )
        self.XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
        self.display_module = types.ModuleType("Xlib.display")
        self.display_module.Display = self.open_display
        self.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                           BadDrawable=type("BadDrawable", (Exception,), {}))
        self.xtest = types.ModuleType("Xlib.ext.xtest")
        self.xtest.fake_input = self.fake_input

    def open_display(self, display_name=None):
        instance = FakeDisplay(display_name, self.events)
        self.displays.append(instance)
        return instance

    def fake_input(self, display, event_type, detail=0, **kwargs):
        event_name = {self.X.KeyPress: "KeyPress", self.X.KeyRelease: "KeyRelease",
                      self.X.ButtonPress: "ButtonPress", self.X.ButtonRelease: "ButtonRelease"}.get(
                          event_type, "Other")
        self.events.append({
            "kind": "x_request",
            "event_type": event_name,
            "detail": detail,
            "request_ns": time.perf_counter_ns(),
            "thread_name": threading.current_thread().name,
        })
        if event_type == self.X.KeyPress:
            display.pressed.add(detail)
        elif event_type == self.X.KeyRelease:
            display.pressed.discard(detail)

    def install(self):
        xlib = types.ModuleType("Xlib")
        xlib.X, xlib.XK, xlib.display, xlib.error = self.X, self.XK, self.display_module, self.error
        ext = types.ModuleType("Xlib.ext")
        ext.xtest = self.xtest
        xlib.ext = ext
        sys.modules.update({"Xlib": xlib, "Xlib.display": self.display_module,
                            "Xlib.error": self.error, "Xlib.ext": ext,
                            "Xlib.ext.xtest": self.xtest})
        executor = types.ModuleType("executor_v3")
        executor.Cancelled = type("Cancelled", (Exception,), {})
        executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = executor


class Lease:
    def __init__(self):
        self.expected_focus = 1
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.intent_token = "host-t4-intent-01"

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("synthetic lease expired")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=False)
    check_sources()

    fake = FakeXlib()
    fake.install()
    sys.path.insert(0, str(LIVE))
    from input_owner_v11 import InputOwner  # imported only after fake Xlib is installed

    rows = [{
        "event": "fixture", "evidence_mode": "synthetic-host",
        "allocation": FREEZE["allocation"], "main_commit": FREEZE["main_commit"],
        "python": sys.version.split()[0], "clock": time.get_clock_info("perf_counter").implementation,
        "container": False, "formal_x11": False, "grants_input_authority": False,
    }]
    owner = InputOwner(None)
    display = fake.displays[-1]
    lease = Lease()
    occurrence_id = str(uuid.uuid4())
    try:
        admission = owner.call("down", lease, "a")
        down_before = 38 in display.pressed
        marker = len(fake.events)
        receipt = owner.call("up", lease, "a")
        release_events = fake.events[marker:]
        requests = [r for r in release_events if r.get("kind") == "x_request" and r.get("event_type") == "KeyRelease"]
        request_position = next((i for i, r in enumerate(release_events) if r in requests), None)
        syncs = [r for r in release_events[request_position + 1:] if r.get("kind") == "sync_return"] if request_position is not None else []
        common = {
            "occurrence_id": occurrence_id, "owner_id": owner.owner_id,
            "intent_token": lease.intent_token, "operation": "up", "key": "a", "keycode": 38,
        }
        if len(requests) == 1:
            rows.append({"event": "owner_release_request", **common,
                         "event_type": "KeyRelease", "request_ns": requests[0].get("request_ns"),
                         "thread_name": requests[0].get("thread_name"),
                         "grants_input_authority": False})
        if len(syncs) == 1:
            rows.append({"event": "owner_sync_return", **common,
                         "sync_return_ns": syncs[0].get("sync_return_ns"),
                         "thread_name": syncs[0].get("thread_name"),
                         "grants_input_authority": False})
        rows.append({**receipt, "event": "caller_release_receipt", **common,
                     "occurrence_id": occurrence_id, "keycode": 38,
                     "grants_input_authority": False})
        rows.append({"event": "fake_key_state", "occurrence_id": occurrence_id,
                     "down_before": down_before, "down_after": 38 in display.pressed,
                     "grants_input_authority": False})
    finally:
        owner.close()

    rows.append({"event": "terminal", "owner_stopped": owner.stopped.is_set(),
                 "owner_thread_alive": owner.thread.is_alive(), "formal_x11": False,
                 "container": False, "grants_input_authority": False})
    out.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
                   encoding="utf-8", newline="\n")
    print(json.dumps({"candidate": "SYNTHETIC_HOST_OWNER_BRACKET", "rows": len(rows),
                      "release_requests": len(requests), "sync_returns": len(syncs),
                      "owner_stopped": owner.stopped.is_set(), "raw": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
