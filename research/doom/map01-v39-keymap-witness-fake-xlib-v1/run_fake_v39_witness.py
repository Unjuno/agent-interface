"""Construction-only repeated key witness against exact v39 owner lineage."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
import types

HERE = Path(__file__).resolve().parent
SERVER = {"down": set(), "lock": threading.Lock()}


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)


class FakeDisplay:
    def __init__(self, _name):
        self.screen_root = FakeRoot()

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, _keysym):
        return 25

    def sync(self):
        return None

    def query_keymap(self):
        bitmap = bytearray(32)
        with SERVER["lock"]:
            for code in SERVER["down"]:
                bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return types.SimpleNamespace(root=self.screen_root)

    def close(self):
        return None


def fake_input(_display, event_type, code, **_kwargs):
    with SERVER["lock"]:
        if event_type == 2:  # X.KeyPress
            SERVER["down"].add(code)
        elif event_type == 3:  # X.KeyRelease
            SERVER["down"].discard(code)
        else:
            raise AssertionError(f"unexpected fake XTest event {event_type}")


def install_fake_xlib():
    x = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonRelease=5, ButtonPress=4,
        Button1Mask=1, AnyPropertyType=0, IsViewable=2,
        MotionNotify=6,
    )
    xk = types.SimpleNamespace(string_to_keysym=lambda value: ord(value[0]))
    display = types.SimpleNamespace(Display=FakeDisplay)
    error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                  BadDrawable=type("BadDrawable", (Exception,), {}))
    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X, xlib.XK, xlib.display, xlib.error = x, xk, display, error
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    sys.modules.update({"Xlib": xlib, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor


class Lease:
    def __init__(self):
        self.expected_focus = 42
        self.intent_token = "v39-witness-token"
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("fixture lease expired")


def load(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bit_is_down(bitmap, code):
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def main():
    install_fake_xlib()
    owner_source = HERE / "dependencies" / "input_owner_v10.py"
    wrapper_source = HERE / "dependencies" / "input_transition_owner_v3.py"
    owner = load(owner_source, "input_owner_v10")
    sys.modules["input_owner_v10"] = owner
    wrapper = load(wrapper_source, "input_transition_owner_v3")
    subject = wrapper.InputOwner(":fixture")
    lease = Lease()
    rows = []
    for occurrence in range(2):
        occurrence_id = f"v39-W-{occurrence + 1:02d}"
        pre_ns = time.perf_counter_ns()
        before = FakeDisplay(":observer").query_keymap()
        admission = subject.call("down", lease, "W")
        down_ns = time.perf_counter_ns()
        after_down = FakeDisplay(":observer").query_keymap()
        receipt = subject.call("up", lease, "W")
        up_ns = time.perf_counter_ns()
        after_up = FakeDisplay(":observer").query_keymap()
        rows.append({
            "occurrence_id": occurrence_id,
            "key": "W",
            "keycode": 25,
            "pre_down_sample_ns": pre_ns,
            "pre_down_keymap_hex": before.hex(),
            "pre_down": bit_is_down(before, 25),
            "admission_event": admission.get("event"),
            "intent_token": admission.get("intent_token"),
            "owner_down_ack_ns": admission.get("input_ack_ns"),
            "post_down_sample_ns": down_ns,
            "post_down_keymap_hex": after_down.hex(),
            "post_down": bit_is_down(after_down, 25),
            "up_event": receipt.get("event"),
            "up_transition_schema": receipt.get("transition_schema"),
            "up_started_ns": receipt.get("release_call_started_ns"),
            "up_returned_ns": receipt.get("release_call_returned_ns"),
            "up_bracket_ns": receipt.get("release_call_bracket_ns"),
            "ordinary_release_candidate": receipt.get("ordinary_release_candidate"),
            "owner_release_history_complete": receipt.get("owner_release_history_complete"),
            "post_up_sample_ns": up_ns,
            "post_up_keymap_hex": after_up.hex(),
            "post_up": bit_is_down(after_up, 25),
            "witness_authority": False,
        })
    subject.close()
    assert [r["pre_down"] for r in rows] == [False, False]
    assert [r["post_down"] for r in rows] == [True, True]
    assert [r["post_up"] for r in rows] == [False, False]
    assert all(r["admission_event"] == "input_admission" for r in rows)
    assert all(r["up_event"] == "input_release_transition" for r in rows)
    assert all(r["ordinary_release_candidate"] is True for r in rows)
    assert all(r["owner_release_history_complete"] is True for r in rows)
    assert len({r["occurrence_id"] for r in rows}) == 2
    result = {
        "schema": "v39-v10-fake-xlib-keymap-witness-construction-v1",
        "main_sha": "13bab54ea6d91978247ecc1b70e5060db752367a",
        "owner_git_blob": "341b3c01649943ddaad5f28431a792c4889cc36e",
        "wrapper_commit": "0f112dcae1e3b108ae2eecddebd95b829b8fbffa",
        "wrapper_git_blob": "e2e69b7f73d823b03e6a295e670f00189bb26778",
        "owner_sha256": hashlib.sha256(owner_source.read_bytes()).hexdigest(),
        "wrapper_sha256": hashlib.sha256(wrapper_source.read_bytes()).hexdigest(),
        "occurrences": rows,
        "owner_final_records": subject.records,
        "scope": "fake Xlib/XTest queue construction; not Xvfb, physical X11, or application effect",
    }
    output = HERE / "result.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(f"saved {output}")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
