"""Fake-Xlib identity probe for the merged V12 cancellation receipt source.

This executes an archived, source-pinned candidate under two synthetic X key
maps. It sends no OS input and does not import python-xlib.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import time
import types


SOURCE_COMMIT = "6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b"
SOURCE_PATH = (
    "research/live_control/batch_fixture_composition_59_4d74_20261004/"
    "source/input_owner_v12.py"
)
EXPECTED_BLOB = "da1a0b496572f3b853a84a94451e6824369a49b0"
SERVER = {"down": set(), "lock": threading.Lock()}
KEYMAP = {}


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)


class FakeDisplay:
    def __init__(self, _name=None):
        self.root = FakeRoot()
        self.events = []

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, symbol):
        return KEYMAP[symbol]

    def query_keymap(self):
        bitmap = bytearray(32)
        with SERVER["lock"]:
            for code in SERVER["down"]:
                bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def sync(self):
        pass

    def close(self):
        pass


def fake_input(display, event, code, **_kwargs):
    display.events.append((event, code))
    with SERVER["lock"]:
        if event == 2:
            SERVER["down"].add(code)
        elif event == 3:
            SERVER["down"].discard(code)
        else:
            raise AssertionError(event)


def load_candidate():
    source = subprocess.check_output(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"]
    )
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"candidate blob mismatch: {blob}")

    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor

    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonRelease=5, ButtonPress=4,
        Button1Mask=1, AnyPropertyType=0, IsViewable=2, MotionNotify=6,
    )
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda name: ord(name[0]))
    xlib.display = types.SimpleNamespace(Display=FakeDisplay)
    xlib.error = types.SimpleNamespace(
        BadWindow=type("BadWindow", (Exception,), {}),
        BadDrawable=type("BadDrawable", (Exception,), {}),
    )
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.ext = ext
    sys.modules.update({
        "Xlib": xlib, "Xlib.X": xlib.X, "Xlib.XK": xlib.XK,
        "Xlib.display": xlib.display, "Xlib.error": xlib.error,
        "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
    })

    module = types.ModuleType("input_owner_v12_probe")
    exec(compile(source, SOURCE_PATH, "exec"), module.__dict__)
    return module.InputOwner


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.intent_token = "probe-intent"
        self.cancel = threading.Event()
        self.expected_focus = 42

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("cancelled")


def run_arm(owner_type, mapping):
    global KEYMAP
    KEYMAP = mapping
    with SERVER["lock"]:
        SERVER["down"].clear()
    owner = owner_type(":fake")
    lease = Lease()
    admissions = []
    try:
        admissions.append(owner.call("down", lease, "W"))
        admissions.append(owner.call("down", lease, "A"))
        lease.cancel.set()
        deadline = time.monotonic() + 1
        while not owner.records and time.monotonic() < deadline:
            time.sleep(0.001)
        if not owner.records:
            raise TimeoutError("owner did not publish cancellation receipt")
        receipt = owner.records[0]
        intervals = receipt.get("key_release_intervals_ns")
        if type(intervals) is not list:
            raise AssertionError("candidate omitted cancellation intervals")
        return {
            "mapping": dict(mapping),
            "admissions": admissions,
            "admission_keycodes": [row.get("keycode") for row in admissions],
            "release_intervals": intervals,
            "release_interval_count": len(intervals),
            "release_keycodes": [row["keycode"] for row in intervals],
            "release_verified": receipt.get("verified"),
            "reason": receipt.get("reason"),
        }
    finally:
        owner.close()


def main():
    owner_type = load_candidate()
    result = {
        "schema": "map01-cancel-keycode-identity-probe-v1",
        "candidate_commit": SOURCE_COMMIT,
        "candidate_path": SOURCE_PATH,
        "candidate_git_blob": EXPECTED_BLOB,
        "environment": "synthetic Xlib with two controlled keysym-to-keycode maps",
        "arms": [
            run_arm(owner_type, {ord("W"): 87, ord("A"): 65}),
            run_arm(owner_type, {ord("W"): 77, ord("A"): 77}),
        ],
        "scope": "construction only; no real X server, physical input, game, model, or live allocation",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
