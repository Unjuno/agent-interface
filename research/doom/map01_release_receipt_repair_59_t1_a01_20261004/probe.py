"""Compare frozen V10/V11 receipt semantics with a minimal in-memory repair.

The probe uses the adjacent cancellation package's controlled FakeDisplay;
it never opens a real X display or sends OS input.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import types
import difflib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURE_PATH = "research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/probe.py"
FIXTURE_COMMIT = "69b2a53a251f91c4b76955d26bcb7888083cfd08"
FIXTURE_BLOB = "3b917891c88096b79a46ebcffeb581fa1e174186"
COMMIT = "6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b"
V10_PATH = "research/live_control/input_owner_v10.py"
V11_PATH = "research/live_control/input_owner_v11.py"
V10_BLOB = "341b3c01649943ddaad5f28431a792c4889cc36e"
V11_BLOB = "842071284156d3ccc647f47135ee62a9e512cb56"


def pinned(path, expected):
    raw = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT)
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if actual != expected:
        raise AssertionError((path, actual, expected))
    return raw.decode("utf-8").replace("\r\n", "\n")


def candidate_sources(v10, v11):
    old_doc = '''"""Telemetry-only wrapper for InputOwner v10 ordinary release RPCs.

The v10 owner performs X11 KeyRelease/ButtonRelease followed by ``d.sync()`` for
ordinary ``up`` / ``button_up`` operations, but returns ``None``.  This version
keeps v10's owner thread and authority semantics unchanged and brackets those
existing calls on the caller's ``perf_counter_ns`` clock.

The resulting receipt proves only that the v10 owner call containing X11 release
and sync completed somewhere inside ``[call_started_ns, call_returned_ns]``.  It
is not a hardware-state timestamp and does not prove application consumption.
"""'''
    new_doc = '''"""Telemetry wrapper for InputOwner v10 ordinary release RPCs.

Legacy v10 ``up`` and ``button_up`` calls return ``None`` and can be no-ops
when the owner has no matching held input. This version uses the additive
receipt call path so the owner thread reports resolved key identity and
whether it issued a release request followed by ``d.sync()``. The caller still
brackets that call with ``perf_counter_ns``. Applied releases carry a censored
transition interval; no-op receipts carry only the caller interval and do not
claim a transition. Neither form proves hardware state or application
consumption.
"""'''
    if v11.count(old_doc) != 1:
        raise AssertionError("V11 documentation patch anchor mismatch")
    v11 = v11.replace(old_doc, new_doc)
    old_call_end = """        if not ok: raise result
        return result

    def close(self):"""
    new_call_end = """        if not ok: raise result
        return result

    def call_release_with_receipt(self, operation, lease=None, key=None):
        variants = {"up": "up_with_receipt", "button_up": "button_up_with_receipt"}
        if operation not in variants:
            raise ValueError("release receipt is available only for up operations")
        return self.call(variants[operation], lease, key)

    def close(self):"""
    if v10.count(old_call_end) != 1:
        raise AssertionError("V10 call API patch anchor mismatch")
    v10 = v10.replace(old_call_end, new_call_end)
    for old, new, label in (
        ("if op in ('move','button_down','button_up','wheel','down','up'):revision += 1",
         "if op in ('move','button_down','button_up','button_up_with_receipt','wheel','down','up','up_with_receipt'):revision += 1",
         "revision"),
        ("elif op in ('move', 'button_down', 'button_up', 'wheel'):",
         "elif op in ('move', 'button_down', 'button_up', 'button_up_with_receipt', 'wheel'):",
         "button dispatch"),
        ("elif op in ('down', 'up'):",
         "elif op in ('down', 'up', 'up_with_receipt'):",
         "key dispatch"),
    ):
        if v10.count(old) != 1:
            raise AssertionError(f"V10 {label} patch anchor mismatch")
        v10 = v10.replace(old, new)
    old_button_op = "if op == 'button_up':"
    new_button_op = "if op in ('button_up', 'button_up_with_receipt'):"
    if v10.count(old_button_op) != 1:
        raise AssertionError("V10 button operation patch anchor mismatch")
    v10 = v10.replace(old_button_op, new_button_op)
    old_admission = "result = dict(event='input_admission', key=key, admitted_ns=admitted,\n                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
    new_admission = "result = dict(event='input_admission', key=key, keycode=code, admitted_ns=admitted,\n                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
    if v10.count(old_admission) != 1:
        raise AssertionError("admission patch anchor mismatch")
    v10 = v10.replace(old_admission, new_admission)

    old_key_up = """                            if code in held:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                            result = None"""
    new_key_up = """                            release_applied = code in held
                            if release_applied:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                            if op == 'up_with_receipt':
                                result = dict(event='input_release_result', operation='up',
                                              keycode=code, release_applied=release_applied,
                                              x11_release_request_issued=release_applied,
                                              x11_sync_completed=release_applied)
                            else:
                                result = None"""
    if v10.count(old_key_up) != 1:
        raise AssertionError("key-up patch anchor mismatch")
    v10 = v10.replace(old_key_up, new_key_up)

    old_button_up = """                            if key in buttons:
                                xtest.fake_input(d, X.ButtonRelease, key)
                                d.sync()
                                del buttons[key]
                            result = None"""
    new_button_up = """                            release_applied = key in buttons
                            if release_applied:
                                xtest.fake_input(d, X.ButtonRelease, key)
                                d.sync()
                                del buttons[key]
                            if op == 'button_up_with_receipt':
                                result = dict(event='input_release_result', operation='button_up',
                                              button=key, release_applied=release_applied,
                                              x11_release_request_issued=release_applied,
                                              x11_sync_completed=release_applied)
                            else:
                                result = None"""
    if v10.count(old_button_up) != 1:
        raise AssertionError("button-up patch anchor mismatch")
    v10 = v10.replace(old_button_up, new_button_up)

    old_v11 = """        if result is not None:
            raise RuntimeError("v10 ordinary release unexpectedly returned a payload")
        if call_returned_ns < call_started_ns:
            raise RuntimeError("release telemetry clock moved backwards")

        return {"""
    new_v11 = """        if (type(result) is not dict or result.get("event") != "input_release_result"
                or result.get("operation") != operation
                or type(result.get("release_applied")) is not bool
                or type(result.get("x11_release_request_issued")) is not bool
                or type(result.get("x11_sync_completed")) is not bool
                or result["release_applied"] != result["x11_release_request_issued"]
                or result["release_applied"] != result["x11_sync_completed"]):
            raise RuntimeError("v10 ordinary release result was malformed")
        if operation == "up" and type(result.get("keycode")) is not int:
            raise RuntimeError("v10 key release omitted resolved keycode")
        if operation == "button_up" and result.get("button") != key:
            raise RuntimeError("v10 button release identity mismatch")
        if call_returned_ns < call_started_ns:
            raise RuntimeError("release telemetry clock moved backwards")

        return {"""
    if v11.count(old_v11) != 1:
        raise AssertionError("V11 patch anchor mismatch")
    v11 = v11.replace(old_v11, new_v11)
    old_claim = '"x11_release_and_sync_completed_before_return": True,'
    new_claim = ('"release_applied": result["release_applied"],\n'
                 '            "keycode": result.get("keycode"),\n'
                 '            "button": result.get("button"),\n'
                 '            "x11_release_request_issued": result["x11_release_request_issued"],\n'
                 '            "x11_sync_completed_before_return": result["x11_sync_completed"],\n'
                 '            "x11_release_and_sync_completed_before_return": result["release_applied"],')
    if v11.count(old_claim) != 1:
        raise AssertionError("V11 receipt patch anchor mismatch")
    v11 = v11.replace(old_claim, new_claim)
    old_interval = '"release_transition_interval_ns": [call_started_ns, call_returned_ns],\n            "interval_width_ns": call_returned_ns - call_started_ns,'
    new_interval = ('"call_interval_ns": [call_started_ns, call_returned_ns],\n'
                    '            "call_interval_width_ns": call_returned_ns - call_started_ns,\n'
                    '            "release_transition_interval_ns": ([call_started_ns, call_returned_ns]\n'
                    '                                             if result["release_applied"] else None),\n'
                    '            "interval_width_ns": (call_returned_ns - call_started_ns\n'
                    '                                  if result["release_applied"] else None),')
    if v11.count(old_interval) != 1:
        raise AssertionError("V11 interval patch anchor mismatch")
    v11 = v11.replace(old_interval, new_interval)
    old_call = "result = super().call(operation, lease, key)"
    new_call = "result = super().call_release_with_receipt(operation, lease, key)"
    if v11.count(old_call) != 1:
        raise AssertionError("V11 owner call patch anchor mismatch")
    v11 = v11.replace(old_call, new_call)
    return v10, v11


def load_fixture():
    raw = subprocess.check_output(["git", "show", f"{FIXTURE_COMMIT}:{FIXTURE_PATH}"], cwd=ROOT)
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != FIXTURE_BLOB:
        raise AssertionError((FIXTURE_PATH, blob, FIXTURE_BLOB))
    fixture = types.ModuleType("cancel_keycode_fixture")
    sys.modules[fixture.__name__] = fixture
    exec(compile(raw.decode("utf-8"), FIXTURE_PATH, "exec"), fixture.__dict__)
    fixture.load_candidate()
    return fixture


def load_owners(v10_source, v11_source):
    for name in ("input_owner_v10", "input_owner_v11"):
        sys.modules.pop(name, None)
    for name, source in (("input_owner_v10", v10_source), ("input_owner_v11", v11_source)):
        module = types.ModuleType(name)
        exec(compile(source, name + ".py", "exec"), module.__dict__)
        sys.modules[name] = module
    return sys.modules["input_owner_v11"].InputOwner


def run_arm(fixture, owner_type, mapping, symbols):
    import time
    fixture.KEYMAP = {ord(k): v for k, v in mapping.items()}
    fixture.SERVER["down"].clear()
    counts = {"key_release_requests": 0, "button_release_requests": 0, "sync_calls": 0}
    xlib = sys.modules["Xlib"]
    xtest = sys.modules["Xlib.ext.xtest"]
    fake_input = xtest.fake_input
    original_sync = fixture.FakeDisplay.sync

    def counted_input(display, event, code, **kwargs):
        if event == xlib.X.KeyRelease:
            counts["key_release_requests"] += 1
        if event == xlib.X.ButtonRelease:
            counts["button_release_requests"] += 1
        return fake_input(display, event, code, **kwargs)

    def counted_sync(display):
        counts["sync_calls"] += 1
        return original_sync(display)

    xtest.fake_input = counted_input
    fixture.FakeDisplay.sync = counted_sync
    owner = owner_type(":fake")
    lease = fixture.Lease()
    try:
        admissions = [owner.call("down", lease, symbol) for symbol in symbols]
        after_down = dict(counts)
        releases = [owner.call("up", lease, symbol) for symbol in symbols]
        after_up = dict(counts)
        repeated = owner.call("up", lease, symbols[-1])
        after_repeated = dict(counts)
        button_noop = owner.call("button_up", lease, 1)
        after_button_noop = dict(counts)
        return {
            "mapping": mapping,
            "admissions": admissions,
            "release_receipts": releases,
            "repeated_up_receipt": repeated,
            "button_noop_receipt": button_noop,
            "counts_after_down": after_down,
            "counts_after_releases": after_up,
            "counts_after_repeated_up": after_repeated,
            "counts_after_button_noop": after_button_noop,
        }
    finally:
        owner.close()
        xtest.fake_input = fake_input
        fixture.FakeDisplay.sync = original_sync


def run_legacy_compatibility(fixture):
    fixture.KEYMAP = {ord("W"): 87}
    fixture.SERVER["down"].clear()
    owner_type = sys.modules["input_owner_v10"].InputOwner
    owner = owner_type(":fake")
    lease = fixture.Lease()
    try:
        admission = owner.call("down", lease, "W")
        key_up = owner.call("up", lease, "W")
        button_up = owner.call("button_up", lease, 1)
        return {"admission": admission, "key_up_return": key_up,
                "button_up_return": button_up}
    finally:
        owner.close()


def main():
    v10 = pinned(V10_PATH, V10_BLOB)
    v11 = pinned(V11_PATH, V11_BLOB)
    fixture = load_fixture()
    baseline_owner = load_owners(v10, v11)
    baseline = run_arm(fixture, baseline_owner, {"W": 77, "A": 77}, ["W", "A"])
    fixed10, fixed11 = candidate_sources(v10, v11)
    patch = "".join(difflib.unified_diff(
        v10.splitlines(keepends=True), fixed10.splitlines(keepends=True),
        fromfile="a/" + V10_PATH, tofile="b/" + V10_PATH, n=0))
    patch += "".join(difflib.unified_diff(
        v11.splitlines(keepends=True), fixed11.splitlines(keepends=True),
        fromfile="a/" + V11_PATH, tofile="b/" + V11_PATH, n=0))
    (HERE / "CANDIDATE.patch").write_bytes(patch.replace("\r\n", "\n").encode("utf-8"))
    checked_out_v10 = (ROOT / V10_PATH).read_text(encoding="utf-8").replace("\r\n", "\n")
    checked_out_v11 = (ROOT / V11_PATH).read_text(encoding="utf-8").replace("\r\n", "\n")
    if checked_out_v10 != fixed10 or checked_out_v11 != fixed11:
        raise AssertionError("checked-out candidate differs from generated source mutation")
    candidate_owner = load_owners(checked_out_v10, checked_out_v11)
    legacy_compatibility = run_legacy_compatibility(fixture)
    injective = run_arm(fixture, candidate_owner, {"W": 87, "A": 65}, ["W", "A"])
    aliased = run_arm(fixture, candidate_owner, {"W": 77, "A": 77}, ["W", "A"])
    return {
        "schema": "map01-v11-release-receipt-repair-probe-v1",
        "source_commit": COMMIT,
        "sources": {V10_PATH: V10_BLOB, V11_PATH: V11_BLOB},
        "fixture": {"commit": FIXTURE_COMMIT, "path": FIXTURE_PATH, "blob": FIXTURE_BLOB},
        "candidate_patch_sha256": hashlib.sha256((fixed10 + "\0" + fixed11).encode()).hexdigest(),
        "candidate_worktree_sha256": {
            V10_PATH: hashlib.sha256((ROOT / V10_PATH).read_bytes()).hexdigest(),
            V11_PATH: hashlib.sha256((ROOT / V11_PATH).read_bytes()).hexdigest(),
        },
        "legacy_v10_compatibility": legacy_compatibility,
        "baseline_aliased": baseline,
        "candidate_injective": injective,
        "candidate_aliased": aliased,
        "scope": "frozen V10/V11 source plus in-memory candidate edits under FakeDisplay; no real X server, OS input, game, model, or live allocation",
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
