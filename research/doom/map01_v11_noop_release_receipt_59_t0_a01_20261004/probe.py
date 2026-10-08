"""Fake-Xlib check of V11 receipts when an aliased key is already up."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMIT = "6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b"
V10_PATH = "research/live_control/input_owner_v10.py"
V11_PATH = "research/live_control/input_owner_v11.py"
V10_BLOB = "341b3c01649943ddaad5f28431a792c4889cc36e"
V11_BLOB = "842071284156d3ccc647f47135ee62a9e512cb56"


class Lease:
    def __init__(self):
        import threading
        import time
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.intent_token = "noop-probe"
        self.cancel = threading.Event()
        self.expected_focus = 42

    def check(self):
        import time
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("cancelled")


def source(path, expected_blob):
    data = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT)
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if blob != expected_blob:
        raise RuntimeError(f"source blob mismatch for {path}: {blob}")
    return data


def load_v11():
    # Reuse the frozen fake Xlib setup from the adjacent cancellation probe.
    fixture_path = HERE.parent / "map01_cancel_keycode_identity_59_t0_a01_20261004" / "probe.py"
    spec = importlib.util.spec_from_file_location("cancel_keycode_fixture", fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = fixture
    spec.loader.exec_module(fixture)
    fixture.load_candidate()
    fixture.KEYMAP = {ord("W"): 77, ord("A"): 77}

    xlib = sys.modules["Xlib"]
    xtest = sys.modules["Xlib.ext.xtest"]
    counts = {"key_release_requests": 0, "sync_calls": 0}
    original_fake_input = xtest.fake_input
    original_sync = fixture.FakeDisplay.sync

    def counted_fake_input(display, event, code, **kwargs):
        if event == xlib.X.KeyRelease:
            counts["key_release_requests"] += 1
        return original_fake_input(display, event, code, **kwargs)

    def counted_sync(display):
        counts["sync_calls"] += 1
        return original_sync(display)

    xtest.fake_input = counted_fake_input
    fixture.FakeDisplay.sync = counted_sync

    for name in ("input_owner_v10", "input_owner_v11"):
        sys.modules.pop(name, None)
    for name, path, expected in (("input_owner_v10", V10_PATH, V10_BLOB),
                                 ("input_owner_v11", V11_PATH, V11_BLOB)):
        module = types.ModuleType(name)
        exec(compile(source(path, expected), path, "exec"), module.__dict__)
        sys.modules[name] = module
    return sys.modules["input_owner_v11"].InputOwner, counts


def run():
    import time
    owner_type, counts = load_v11()
    owner, lease = owner_type(":fake"), Lease()
    try:
        down = [owner.call("down", lease, key) for key in ("W", "A")]
        first = owner.call("up", lease, "W")
        after_first = dict(counts)
        second = owner.call("up", lease, "A")
        after_second = dict(counts)
        return {
            "schema": "map01-v11-noop-release-receipt-t0-v1",
            "candidate_commit": COMMIT,
            "sources": {V10_PATH: V10_BLOB, V11_PATH: V11_BLOB},
            "synthetic_keysym_map": {"W": 77, "A": 77},
            "admissions": down,
            "first_up_receipt": first,
            "second_up_receipt": second,
            "calls_after_first_up": after_first,
            "calls_after_second_up": after_second,
            "second_receipt_claims_xsync": second.get("x11_release_and_sync_completed_before_return"),
            "second_call_added_key_release_request": after_second["key_release_requests"] - after_first["key_release_requests"],
            "second_call_added_sync": after_second["sync_calls"] - after_first["sync_calls"],
            "scope": "fake Xlib only; no physical input, game, model, or live allocation",
        }
    finally:
        owner.close()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
