"""One-shot disposable Xvfb experiment for #5156; no user desktop or game."""
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

from Xlib import X, XK, display
from serialize_release import join_explicit_release

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent
sys.path.insert(0, str(LIVE))
V11_DIR = HERE / "dependencies"
sys.path.insert(0, str(V11_DIR))
from input_owner_v11 import InputOwner as V11  # noqa: E402
from input_transition_owner_v3 import InputOwner as TransitionV3  # noqa: E402


class Lease:
    def __init__(self, focus):
        self.expected_focus = focus
        self.deadline = time.perf_counter_ns() + 30_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.intent_token = uuid.uuid4().hex

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("lease cancelled")


def key_down(d, code):
    bits = d.query_keymap()
    return bool(bits[code // 8] & (1 << (code % 8)))


def wait_key_state(d, code, expected, timeout=1.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if key_down(d, code) is expected:
            return True
        time.sleep(0.002)
    return key_down(d, code) is expected


def wait_key_set(d, codes, expected_down, timeout=1.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        bits = d.query_keymap()
        down = {key for key, code in codes.items() if bits[code // 8] & (1 << (code % 8))}
        if down == set(expected_down):
            return bytes(bits)
        time.sleep(0.002)
    bits = d.query_keymap()
    down = {key for key, code in codes.items() if bits[code // 8] & (1 << (code % 8))}
    if down != set(expected_down):
        raise RuntimeError(f"keymap state mismatch: {sorted(down)} != {sorted(expected_down)}")
    return bytes(bits)


def main(out_path):
    raw = []
    expected = json.loads((HERE / "EXPECTED.json").read_text(encoding="utf-8"))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("", encoding="utf-8")

    def emit(record):
        raw.append(record)
        with open(out_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    def snapshot(case, stage, codes, expected_down):
        bitmap = wait_key_set(observer, codes, expected_down)
        emit({"event": "keymap_snapshot", "case": case, "stage": stage,
              "observed_ns": time.perf_counter_ns(), "keycodes": dict(sorted(codes.items())),
              "bitmap_hex": bitmap.hex()})

    observer = display.Display()
    root = observer.screen().root
    window = root.create_window(10, 10, 120, 80, 0, X.CopyFromParent,
                                X.InputOutput, X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
    window.map()
    observer.sync()
    observer.set_input_focus(window, X.RevertToParent, X.CurrentTime)
    observer.sync()
    focus = observer.get_input_focus().focus.id
    if focus != window.id:
        raise RuntimeError(f"fixture focus mismatch: {focus} != {window.id}")

    owner = TransitionV3(os.environ.get("DISPLAY"), _owner_cls=V11)
    leases = {}
    admitted = {}
    explicit_joined = []
    try:
        emit({"event": "fixture", "evidence_mode": "formal-x11", "display": os.environ.get("DISPLAY"),
                    "focus_window": window.id,
                    "allocation": os.environ.get("FORMAL_ALLOCATION", expected["allocation"]),
                    "frozen_main": os.environ.get("FORMAL_FROZEN_MAIN", expected["frozen_main"]),
                    "image_digest": os.environ.get("FORMAL_IMAGE_DIGEST"),
                    "platform": os.environ.get("FORMAL_PLATFORM")})

        def down(case, lease, key):
            code = observer.keysym_to_keycode(XK.string_to_keysym(key))
            receipt = owner.call("down", lease, key)
            if not wait_key_state(observer, code, True):
                raise RuntimeError(f"key {key} not down after admission")
            admitted[(case, key)] = code
            emit({"event": "admission", "case": case, "key": key, "keycode": code,
                        "owner_id": owner.owner_id, "intent_token": lease.intent_token,
                        "receipt": receipt, "down_verified": True,
                        "grants_input_authority": False})

        def explicit_up(case, lease, key):
            before = len([r for r in owner.records if r.get("event") == "owner_key_release_bracket"])
            receipt = owner.call("up", lease, key)
            after_rows = [r for r in owner.records if r.get("event") == "owner_key_release_bracket"]
            new = after_rows[before:]
            if len(new) != 1:
                raise RuntimeError(f"expected one owner bracket for {case}/{key}, got {len(new)}")
            joined = join_explicit_release(new[0], {
                "case": case,
                "caller_started_ns": receipt["release_call_started_ns"],
                "caller_returned_ns": receipt["release_call_returned_ns"],
                "caller_owner_id": receipt["owner_id"],
                "caller_intent_token": receipt["intent_token"],
            })
            explicit_joined.append(joined)

        lease = Lease(focus)
        leases["single_explicit"] = lease
        snapshot("single_explicit", "pre_down", {"a": observer.keysym_to_keycode(XK.string_to_keysym("a"))}, set())
        down("single_explicit", lease, "a")
        snapshot("single_explicit", "post_down", {"a": admitted[("single_explicit", "a")]}, {"a"})
        explicit_up("single_explicit", lease, "a")
        code_a = admitted[("single_explicit", "a")]
        if not wait_key_state(observer, code_a, False):
            raise RuntimeError("single explicit key-up not observed")
        snapshot("single_explicit", "post_release", {"a": code_a}, set())
        emit({"event": "case_terminal", "case": "single_explicit", "all_up_verified": True})

        owner.call("release", lease)
        lease2 = Lease(focus)
        leases["two_key_explicit"] = lease2
        two_codes = {k: observer.keysym_to_keycode(XK.string_to_keysym(k)) for k in ("a", "b")}
        snapshot("two_key_explicit", "pre_down", two_codes, set())
        down("two_key_explicit", lease2, "a")
        down("two_key_explicit", lease2, "b")
        snapshot("two_key_explicit", "post_down", {k: admitted[("two_key_explicit", k)] for k in ("a", "b")}, {"a", "b"})
        # No XQueryKeymap or other owner-state query occurs between these releases.
        explicit_up("two_key_explicit", lease2, "a")
        explicit_up("two_key_explicit", lease2, "b")
        if not all(wait_key_state(observer, admitted[("two_key_explicit", k)], False) for k in ("a", "b")):
            raise RuntimeError("two-key release state not observed")
        snapshot("two_key_explicit", "post_release", {k: admitted[("two_key_explicit", k)] for k in ("a", "b")}, set())
        emit({"event": "case_terminal", "case": "two_key_explicit", "all_up_verified": True})

        owner.call("release", lease2)
        lease3 = Lease(focus)
        leases["partial_cancel"] = lease3
        snapshot("partial_cancel", "pre_down", {"a": observer.keysym_to_keycode(XK.string_to_keysym("a"))}, set())
        down("partial_cancel", lease3, "a")
        snapshot("partial_cancel", "post_down", {"a": admitted[("partial_cancel", "a")]}, {"a"})
        lease3.cancel.set()
        try:
            owner.call("down", lease3, "b")
        except Exception:
            pass
        else:
            raise RuntimeError("cancelled second admission unexpectedly succeeded")
        end = time.monotonic() + 1.0
        while time.monotonic() < end and not any(
                r.get("event") == "owner_release" and r.get("reason") == "cancelled" for r in owner.records):
            time.sleep(0.002)
        cancel_release = next((r for r in owner.records if r.get("event") == "owner_release"
                               and r.get("reason") == "cancelled"), None)
        if not cancel_release or not cancel_release.get("verified"):
            raise RuntimeError("autonomous cancellation cleanup not verified")
        if not wait_key_state(observer, admitted[("partial_cancel", "a")], False):
            raise RuntimeError("cancel cleanup did not release key")
        snapshot("partial_cancel", "post_cleanup", {"a": admitted[("partial_cancel", "a")]}, set())
        emit({"event": "case_terminal", "case": "partial_cancel", "all_up_verified": True,
                    "second_admission_rejected": True})

        for row in explicit_joined:
            emit(row)
        for row in owner.records:
            emit(dict(event="owner_record", record=row))
        owner.close()
        if owner._inner.thread.is_alive() or not owner._inner.stopped.is_set():
            raise RuntimeError("owner process/thread did not stop")
        emit({"event": "process_cleanup", "owner_stopped": True})
        codes = set(admitted.values())
        neutral = all(not key_down(observer, code) for code in codes)
        if not neutral:
            raise RuntimeError("terminal keymap is not neutral")
        emit({"event": "terminal_state", "touched_keycodes": sorted(codes),
                    "neutral": neutral, "grants_input_authority": False})
    finally:
        try:
            owner.close()
        except Exception:
            pass
        window.destroy()
        observer.sync()
        observer.close()
    emit({"event": "runner_complete", "exit_code": 0, "raw_rows": len(raw) + 1})
    print(json.dumps({"status": "RUNNER_EXIT_0", "raw_rows": len(raw), "raw_path": out_path}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_formal_x11.py RAW.jsonl")
    try:
        main(sys.argv[1])
    except BaseException as exc:
        with open(sys.argv[1], "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"event": "runner_failure", "type": type(exc).__name__,
                                "error": str(exc)}, sort_keys=True, separators=(",", ":")) + "\n")
        raise
