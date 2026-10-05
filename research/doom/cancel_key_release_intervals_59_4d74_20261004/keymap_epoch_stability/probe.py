"""Test admission-to-cancel keycode identity across synthetic keymap changes."""
import hashlib
import json
import subprocess
import sys
import threading
import time
import types

SOURCE_COMMIT = "1721f7cb2a47f53641bc7c93effe2a2b817013cd"
SOURCE_PATH = "research/live_control/input_owner_v12.py"
SOURCE_BLOB = "50887b03fa2931315caf8396ac99a47628396129"
OLD = (
    b"result = dict(event='input_admission', key=key, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)
NEW = (
    b"result = dict(event='input_admission', key=key, keycode=code, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)
KEYMAP = {}
DOWN = set()


class FakeDisplay:
    def __init__(self, _name=None):
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, keysym):
        return KEYMAP[keysym]

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in DOWN:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def sync(self):
        pass

    def close(self):
        pass


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.interrupted = threading.Event()
        self.interruptions = []

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("cancelled")

    def record_interruption(self, record):
        self.interruptions.append(record)
        self.interrupted.set()


def install_fake_xlib():
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})

    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonRelease=5, ButtonPress=4,
        Button1Mask=256, AnyPropertyType=0, IsViewable=2, MotionNotify=6)
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda name: ord(name[0]))
    xlib.display = types.SimpleNamespace(Display=FakeDisplay)
    xlib.error = types.SimpleNamespace(
        BadWindow=type("BadWindow", (Exception,), {}),
        BadDrawable=type("BadDrawable", (Exception,), {}))
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(_display, event, code, **_kwargs):
        if event == xlib.X.KeyPress:
            DOWN.add(code)
        elif event == xlib.X.KeyRelease:
            DOWN.discard(code)
        else:
            raise AssertionError(event)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.ext = ext
    sys.modules.update({
        "executor_v3": executor, "Xlib": xlib, "Xlib.X": xlib.X,
        "Xlib.XK": xlib.XK, "Xlib.display": xlib.display,
        "Xlib.error": xlib.error, "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
    })


def candidate_source():
    source = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"])
    actual_blob = subprocess.check_output(
        ["git", "rev-parse", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True).strip()
    if actual_blob != SOURCE_BLOB:
        raise RuntimeError(f"source blob mismatch: {actual_blob}")
    if source.count(OLD) != 1:
        raise RuntimeError("expected one frozen admission receipt pattern")
    return source.replace(OLD, NEW, 1)


def load_candidate(source):
    module = types.ModuleType("input_owner_v12_keymap_probe")
    exec(compile(source, SOURCE_PATH, "exec"), module.__dict__)
    return module.InputOwner


def run_arm(owner_type, initial_map, changes):
    KEYMAP.clear()
    KEYMAP.update(initial_map)
    DOWN.clear()
    owner = owner_type(":fake")
    lease = Lease()
    admissions = []
    map_history = [dict(KEYMAP)]
    try:
        admissions.append(owner.call("down", lease, "W"))
        if changes.get("before_second_admission"):
            KEYMAP.update(changes["before_second_admission"])
            map_history.append(dict(KEYMAP))
        admissions.append(owner.call("down", lease, "A"))
        if changes.get("before_cancel"):
            KEYMAP.update(changes["before_cancel"])
            map_history.append(dict(KEYMAP))
        lease.cancel.set()
        if not lease.interrupted.wait(1):
            raise TimeoutError("cancellation receipt not published")
        record = lease.interruptions[0]
        return {
            "initial_map": initial_map,
            "map_history": map_history,
            "admissions": admissions,
            "admission_keycodes": [row["keycode"] for row in admissions],
            "release_keycodes": [row["keycode"] for row in
                                 record["key_release_intervals_ns"]],
            "release_intervals": record["key_release_intervals_ns"],
            "verified": record["verified"],
            "reason": record["reason"],
        }
    finally:
        owner.close()


def run():
    install_fake_xlib()
    source = candidate_source()
    owner_type = load_candidate(source)
    arms = [
        run_arm(owner_type, {ord("W"): 87, ord("A"): 65},
                {"before_cancel": {ord("W"): 77}}),
        run_arm(owner_type, {ord("W"): 87, ord("A"): 65},
                {"before_second_admission": {ord("W"): 77, ord("A"): 77}}),
    ]
    expected = ([87, 65], [87, 77])
    for arm, identities in zip(arms, expected):
        if arm["admission_keycodes"] != list(identities):
            raise AssertionError(f"unexpected admission identity: {arm}")
        if arm["release_keycodes"] != list(identities):
            raise AssertionError(f"keymap change broke release identity: {arm}")
        if arm["verified"] is not True or arm["reason"] != "cancelled":
            raise AssertionError(f"cancellation did not verify: {arm}")
    return {
        "schema": "cancel-key-release-keymap-epoch-probe-v1",
        "source_commit": SOURCE_COMMIT,
        "source_blob": SOURCE_BLOB,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "mutation": "add resolved keycode to input_admission in memory",
        "arms": arms,
        "scope": "fake Xlib; synthetic keysym remaps between admissions/cancel; no OS input",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
