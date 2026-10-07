#!/usr/bin/env python3
"""One-shot guarded alias refusal followed by real V4/V3/V12 owner cleanup on Xvfb."""
import argparse
import hashlib
import json
import select
import subprocess
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Lease:
    def __init__(self, focus):
        import threading
        self.deadline = time.perf_counter_ns() + 20_000_000_000
        self.expected_focus = focus
        self.intent_token = "alias-cleanup-a01"
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")

    def record_interruption(self, row):
        self.interruption = row


def key_down(observer, code):
    bitmap = observer.query_keymap()
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def next_key_event(observer, deadline):
    while time.monotonic() < deadline:
        if observer.pending_events():
            event = observer.next_event()
        else:
            ready, _, _ = select.select(
                [observer.fileno()], [], [], max(0, deadline - time.monotonic())
            )
            if not ready:
                return None
            event = observer.next_event()
        if event.type in (2, 3):
            return {
                "type": int(event.type),
                "keycode": int(event.detail),
                "window": int(event.window.id),
                "observed_ns": time.perf_counter_ns(),
            }
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":131")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing to overwrite first outcome")
    args.out.mkdir(parents=True)

    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["source_sha256"].items():
        if sha(HERE / relative) != expected:
            raise SystemExit("frozen source SHA mismatch: " + relative)

    raw = {
        "schema": "release-batch-alias-owner-cleanup-a01-raw-v1",
        "status": "STOP",
        "errors": [],
        "scope": "one synthetic alias refusal and owner-close cleanup on private Xvfb; no game/model/physical input",
        "display": args.display,
        "owner_records_before_close": [],
        "owner_records_after_close": [],
        "observations": {},
        "cleanup": {},
    }
    xvfb = observer = owner = None
    original_query = None
    owner_thread = None
    try:
        from Xlib import X, Xatom, XK, display
        original_query = display.Display.query_keymap
        owner_id = [None]

        def traced_query(connection):
            started = time.perf_counter_ns()
            bitmap = original_query(connection)
            returned = time.perf_counter_ns()
            raw.setdefault("query_keymap_calls", []).append({
                "role": "owner" if id(connection) == owner_id[0] else "observer_or_other",
                "started_ns": started,
                "returned_ns": returned,
            })
            return bitmap

        display.Display.query_keymap = traced_query
        xvfb = subprocess.Popen(
            ["Xvfb", args.display, "-screen", "0", "640x480x24", "-nolisten", "tcp", "-noreset", "-ac"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        raw["xvfb_pid"] = xvfb.pid
        connect_deadline = time.monotonic() + 5
        while time.monotonic() < connect_deadline:
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited before observer connection: " + xvfb.stderr.read().decode("utf-8", "replace"))
            try:
                observer = display.Display(args.display)
                break
            except Exception:
                time.sleep(0.05)
        if observer is None:
            raise TimeoutError("Xvfb observer connection timed out")

        screen = observer.screen()
        root = screen.root
        window = root.create_window(
            20, 20, 320, 200, 0, screen.root_depth, X.InputOutput,
            X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        window.map()
        root.change_property(observer.intern_atom("_NET_ACTIVE_WINDOW"), Xatom.WINDOW, 32, [window.id])
        observer.sync()
        observer.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        observer.sync()
        for _ in range(100):
            focus = observer.get_input_focus().focus
            if getattr(focus, "id", focus) == window.id:
                break
            time.sleep(0.01)
        else:
            raise RuntimeError("test client focus not established")
        while observer.pending_events():
            observer.next_event()

        lower = int(observer.keysym_to_keycode(XK.string_to_keysym("a")))
        upper = int(observer.keysym_to_keycode(XK.string_to_keysym("A")))
        if not lower or lower != upper:
            raise RuntimeError(f"Xvfb alias precondition failed: a={lower}, A={upper}")
        raw["keycodes"] = {"a": lower, "A": upper}

        executor_stub = types.ModuleType("executor_v3")
        executor_stub.Cancelled = type("Cancelled", (Exception,), {})
        executor_stub.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = executor_stub
        sys.path.insert(0, str(HERE / "source" / "guarded"))
        from input_transition_owner_v4 import InputOwner

        owner = InputOwner(args.display)
        owner_thread = owner._inner._inner
        raw["owner_id"] = owner.owner_id
        raw["owner_thread_started"] = owner_thread.ready.is_set() and owner_thread.thread.is_alive()
        lease = Lease(int(window.id))

        admission = owner.call("down", lease, "a")
        raw["admission"] = admission
        press = next_key_event(observer, time.monotonic() + 2)
        raw["observations"]["press_event"] = press
        raw["observations"]["server_down_before_alias"] = key_down(observer, lower)
        if not press or press["type"] != X.KeyPress or press["keycode"] != lower or press["window"] != window.id:
            raise RuntimeError("admitted key-down event did not match focused test window")
        if raw["observations"]["server_down_before_alias"] is not True:
            raise RuntimeError("key was not held before alias refusal")

        refusal = {"raised": False, "type": None, "message": None}
        try:
            owner.call("up_batch", lease, ["a", "A"])
        except Exception as exc:
            refusal = {"raised": True, "type": type(exc).__name__, "message": str(exc)}
        raw["refusal"] = refusal
        raw["observations"]["server_down_after_refusal"] = key_down(observer, lower)
        raw["observations"]["key_event_after_refusal"] = next_key_event(observer, time.monotonic() + 0.15)
        raw["owner_records_before_close"] = list(owner_thread.records)
        raw["observations"]["close_needed_after_refusal"] = owner_thread.thread.is_alive()
        if not refusal["raised"]:
            raise RuntimeError("duplicate resolved-keycode batch was not refused")
        if raw["observations"]["server_down_after_refusal"] is not True:
            raise RuntimeError("refusal unexpectedly released held key before caller cleanup")
        if raw["observations"]["key_event_after_refusal"] is not None:
            raise RuntimeError("an X key event was delivered during refusal")

        owner.close()
        raw["close_returned"] = True
        release_event = next_key_event(observer, time.monotonic() + 2)
        raw["observations"]["release_event_after_close"] = release_event
        raw["observations"]["server_down_after_close"] = key_down(observer, lower)
        raw["owner_records_after_close"] = list(owner_thread.records)
        terminal = next((row for row in reversed(owner_thread.records) if row.get("event") == "owner_release"), None)
        raw["cleanup"].update({
            "owner_closed": owner_thread.closed,
            "owner_stopped": owner_thread.stopped.is_set(),
            "owner_thread_alive": owner_thread.thread.is_alive(),
            "terminal_release": terminal,
        })
        if not release_event or release_event["type"] != X.KeyRelease or release_event["keycode"] != lower or release_event["window"] != window.id:
            raise RuntimeError("owner close did not deliver matching KeyRelease")
        if raw["observations"]["server_down_after_close"] is not False:
            raise RuntimeError("Xvfb keymap remains down after owner close")
        if not terminal or terminal.get("event") != "owner_release" or terminal.get("verified") is not True or terminal.get("keys_down") != []:
            raise RuntimeError("owner close did not record verified empty terminal release")
        if terminal.get("reason") != "close":
            raise RuntimeError("terminal release reason was not close")
        if owner_thread.thread.is_alive() or not owner_thread.closed or not owner_thread.stopped.is_set():
            raise RuntimeError("owner thread did not stop cleanly")
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if owner is not None:
            try:
                owner.close()
                if owner_thread is not None:
                    raw["owner_records_after_close"] = list(owner_thread.records)
                    raw["cleanup"].update({
                        "owner_closed": owner_thread.closed,
                        "owner_stopped": owner_thread.stopped.is_set(),
                        "owner_thread_alive": owner_thread.thread.is_alive(),
                        "terminal_release": next((row for row in reversed(owner_thread.records) if row.get("event") == "owner_release"), None),
                    })
            except BaseException as exc:
                raw["cleanup"]["owner_close_error"] = f"{type(exc).__name__}: {exc}"
        if observer is not None:
            try:
                observer.close()
            except BaseException as exc:
                raw["cleanup"]["observer_close_error"] = f"{type(exc).__name__}: {exc}"
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as exc:
                raw["cleanup"]["xvfb_error"] = f"{type(exc).__name__}: {exc}"
                xvfb.kill()
                xvfb.wait(timeout=5)
        if original_query is not None:
            from Xlib import display
            display.Display.query_keymap = original_query
        (args.out / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": raw["status"], "errors": raw["errors"], "refusal": raw.get("refusal"), "observations": raw.get("observations"), "cleanup": raw["cleanup"]}, sort_keys=True))


if __name__ == "__main__":
    main()
