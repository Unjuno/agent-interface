"""Inject an accepted-then-raised per-key XTest release during cancellation."""
import json
import argparse
import os
import sys
import threading
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "research" / "live_control"))
SOURCE_OVERRIDE = os.environ.get("INPUT_OWNER_SOURCE_DIR")
if SOURCE_OVERRIDE:
    sys.path.insert(0, SOURCE_OVERRIDE)

from test_input_owner_v12_batch_release_intervals import Lease
if SOURCE_OVERRIDE:
    sys.path.remove(SOURCE_OVERRIDE)
    sys.path.insert(0, SOURCE_OVERRIDE)


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.fail_query_keymap_once = False
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, keysym):
        return keysym

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        if self.fail_query_keymap_once:
            self.fail_query_keymap_once = False
            raise RuntimeError("injected keymap verification failure")
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        pass

    def close(self):
        pass


def run_experiment(failure_phase="request"):
    xlib_names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                  "Xlib.ext", "Xlib.ext.xtest")
    owner_names = ("input_owner_v12", "input_transition_owner_v3",
                   "input_transition_owner_v4")
    saved = {name: sys.modules.get(name) for name in xlib_names + owner_names}
    display_instance = FakeDisplay()
    display_instance.fail_query_keymap_once = failure_phase == "verify"
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonRelease=5, Button1Mask=256,
        AnyPropertyType=0)
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda key: ord(key[0])
    display = types.ModuleType("Xlib.display")
    display.Display = lambda _name: display_instance
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    failed_once = {"value": False}

    def fake_input(_display, event, code):
        if event == xlib.X.KeyPress:
            display_instance.down.add(code)
        elif event == xlib.X.KeyRelease:
            # Model an XTest request accepted by the server before the client
            # call raises, leaving its delivery outcome ambiguous until XSync.
            display_instance.down.discard(code)
            if failure_phase == "request" and code == ord("A") and not failed_once["value"]:
                failed_once["value"] = True
                raise RuntimeError("injected accepted-then-raised XTest release")

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    sys.modules.update({
        "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk,
        "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext,
        "Xlib.ext.xtest": xtest,
    })
    for name in owner_names:
        sys.modules.pop(name, None)

    owner = None
    try:
        from input_owner_v12 import InputOwner
        from executor_v13 import Executor as ExecutorV13
        loaded_source = sys.modules["input_owner_v12"].__file__

        owner = InputOwner(":fake")
        lease = Lease()
        owner.call("down", lease, "W")
        owner.call("down", lease, "A")
        lease.cancel.set()
        # Queue a state read behind cancellation cleanup. Its successful reply
        # establishes that the owner processed the injected failure.
        state = owner.call("input_state")
        lease.interrupted.wait(0.05)
        before_close = {
            "owner_release_records": [row for row in owner.records
                                      if row.get("event") == "owner_release"],
            "interruptions": list(lease.interruptions),
            "owned_keycodes": state["owned_keycodes"],
            "physical_keymap_down": sorted(display_instance.down),
            "cancel_requested": state["cancel_requested"],
        }
        owner.close()
        after_close = [row for row in owner.records
                       if row.get("event") == "owner_release"]
        failed = before_close["owner_release_records"]
        assert len(failed) == 1, (
            "failed cancellation must publish one unverified owner_release; "
            f"loaded_source={loaded_source}")
        assert len(before_close["interruptions"]) == 1, "failed cancellation must wake the release watcher"
        assert failed[0]["reason"] == "cancelled"
        assert failed[0]["verified"] is False
        assert failed[0]["keys_down"] == [ord("A"), ord("W")]
        if failure_phase == "request":
            assert failed_once["value"] is True
            assert failed[0]["release_error"] == "RuntimeError('injected accepted-then-raised XTest release')"
        else:
            assert failed_once["value"] is False
            assert failed[0]["release_error"] == "RuntimeError('injected keymap verification failure')"
        intervals = failed[0].get("key_release_intervals_ns", [])
        if failure_phase == "request":
            assert intervals == [], "no shared sync means no bounded intervals"
        else:
            assert len(intervals) == 2, "successful shared sync must retain both request bounds"
            assert all(row["interval_ns"][0] <= row["interval_ns"][1] for row in intervals)
        assert len(after_close) == 2 and after_close[-1]["verified"] is True
        publisher = object.__new__(ExecutorV13)
        unverified_event = publisher._release_event(
            "run-1", {"intent_token": "intent-1", "record": failed[0]})
        assert unverified_event["event"] == "input_release_unverified"
        assert unverified_event["owner_release"] is failed[0]
        assert unverified_event["grants_input_authority"] is False
        return {
            "failure_phase": failure_phase,
            "loaded_source": loaded_source,
            "injected_request_accepted_then_raised": failed_once["value"],
            "before_close": before_close,
            "after_close_owner_release_records": after_close,
            "v13_unverified_publication": unverified_event,
        }
    finally:
        if owner is not None and not owner.closed:
            owner.close()
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure-phase", choices=("request", "verify"), default="request")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.failure_phase), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
