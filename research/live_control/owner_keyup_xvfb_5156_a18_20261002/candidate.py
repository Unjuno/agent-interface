from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "dependencies"))
from Xlib import X, XK, display
from executor_v3 import Cancelled
from input_owner_v11 import InputOwner as InstrumentedOwner
from input_transition_owner_v3 import InputOwner as TransitionOwner
from lease import Lease

OUT = Path(os.environ.get("OUT_DIR", "/out"))
RAW_PATH = OUT / "raw.json"
ALLOCATION = "MAP01-OWNER-KEYUP-BRACKET-5156-WSLC-20261002-18"


def keycode(dpy, name):
    code = dpy.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise RuntimeError(f"key unavailable: {name}")
    return int(code)


def down_state(dpy, code):
    bitmap = dpy.query_keymap()
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def make_lease(token, deadline_ns, focus):
    lease = Lease(deadline_ns)
    lease.intent_token = token
    lease.expected_focus = int(focus)
    lease.focus_invalid = False
    return lease


def start_xvfb(log_dir):
    log_path = log_dir / "xvfb.log"
    log_file = open(log_path, "wb")
    proc = subprocess.Popen(
        ["Xvfb", ":99", "-screen", "0", "800x600x24", "-nolisten", "tcp", "-ac"],
        stdout=log_file, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 3.0
    last_error = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            log_file.close()
            raise RuntimeError(f"Xvfb exited early: {proc.returncode}; log={log_path.read_text(errors='replace')}")
        try:
            probe = display.Display(":99")
            probe.close()
            os.environ["DISPLAY"] = ":99"
            return proc, log_file, str(log_path)
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(0.02)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)
    log_file.close()
    raise RuntimeError(f"Xvfb readiness timeout: {last_error}; log={log_path.read_text(errors='replace')}")


def snapshot(owner):
    return list(owner.records)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    work = {
        "schema": "owner-keyup-wslc-candidate-v1",
        "allocation_id": ALLOCATION,
        "image_id": os.environ.get("IMAGE_ID"),
        "python": sys.version,
        "platform": sys.platform,
        "display_name": ":99",
        "authority_granted": False,
        "external_effects": 0,
        "model_calls": 0,
        "explicit_calls": [],
        "cases": [],
        "owner_snapshots": [],
        "errors": [],
        "processes_clean": False,
        "owner_thread_stopped": False,
        "candidate_started_ns": time.perf_counter_ns(),
        "source_sha256": {line.split()[1]: line.split()[0] for line in (HERE / "dependencies" / "SOURCE_SHA256.txt").read_text().splitlines()},
    }
    xvfb = None
    xvfb_log = None
    dpy = None
    owner = None
    target = None
    failure = None
    try:
        xvfb, xvfb_log, work["xvfb_log"] = start_xvfb(OUT)
        dpy = display.Display(":99")
        root = dpy.screen().root
        target = root.create_window(10, 10, 120, 80, 0, dpy.screen().root_depth,
                                   X.InputOutput, X.CopyFromParent, background_pixel=0)
        target.map()
        dpy.sync()
        dpy.set_input_focus(target, X.RevertToParent, X.CurrentTime)
        dpy.sync()
        focus_reply = dpy.get_input_focus().focus
        focus_id = int(focus_reply.id if hasattr(focus_reply, "id") else focus_reply)
        if focus_id != int(target.id):
            raise RuntimeError(f"private fixture focus mismatch: {focus_id} != {target.id}")
        owner = TransitionOwner(":99", _owner_cls=InstrumentedOwner)
        work["owner_id"] = owner.owner_id
        work["target_window"] = int(target.id)
        codes = {name: keycode(dpy, name) for name in ("w", "a")}
        work["keycodes"] = codes

        def new_lease(index, token=None):
            return make_lease(token or f"intent-{index}", time.perf_counter_ns() + 10_000_000_000, focus_id)

        def admit(lease, name):
            if down_state(dpy, codes[name]):
                raise RuntimeError(f"{name} unexpectedly down before admission")
            receipt = owner.call("down", lease, name)
            observed = down_state(dpy, codes[name])
            work["cases"].append({"event": "admission", "intent_token": lease.intent_token,
                                  "key": name, "keycode": codes[name], "receipt": receipt,
                                  "key_down_after": observed})
            if not observed:
                raise RuntimeError(f"{name} not down after accepted admission")

        def explicit_up(lease, name, case_name):
            before = down_state(dpy, codes[name])
            before_rows = snapshot(owner)
            receipt = owner.call("up", lease, name)
            after = down_state(dpy, codes[name])
            after_rows = snapshot(owner)
            appended = after_rows[len(before_rows):]
            owner_rows = [row for row in appended if row.get("event") == "owner_explicit_key_up"]
            item = {"case": case_name, "intent_token": lease.intent_token,
                    "key": name, "keycode": codes[name], "key_down_before": before,
                    "caller_receipt": receipt, "owner_rows_appended": owner_rows,
                    "key_down_after": after}
            work["explicit_calls"].append(item)
            if not before or after or len(owner_rows) != 1:
                raise RuntimeError(f"explicit up boundary invalid: {case_name}/{name}")
            return item

        # Case 1: a single explicit key-up.
        lease1 = new_lease(1)
        admit(lease1, "w")
        explicit_up(lease1, "w", "single")
        teardown1_before = snapshot(owner)
        teardown1 = owner.call("release", lease1)
        teardown1_after = snapshot(owner)
        if down_state(dpy, codes["w"]) or teardown1.get("event") != "owner_release" or not teardown1.get("verified"):
            raise RuntimeError("single-case teardown was not verified neutral")
        work["cases"].append({"event": "teardown", "case": "single", "receipt": teardown1,
                              "owner_rows_appended": teardown1_after[len(teardown1_before):],
                              "w_down_after": down_state(dpy, codes["w"]),
                              "a_down_after": down_state(dpy, codes["a"])})

        # Case 2: W+A, foreign stale W-up, then ordered owning releases.
        lease2 = new_lease(2)
        stale = new_lease(99, "intent-stale")
        admit(lease2, "w")
        admit(lease2, "a")
        stale_before_rows = snapshot(owner)
        stale_error = None
        stale_receipt = None
        try:
            stale_receipt = owner.call("up", stale, "w")
        except Exception as exc:
            stale_error = {"type": type(exc).__name__, "message": str(exc)}
        stale_after_rows = snapshot(owner)
        stale_case = {"event": "stale_release", "intent_token": stale.intent_token,
                      "foreign_to": lease2.intent_token, "key": "w", "keycode": codes["w"],
                      "rejected": stale_error is not None, "error": stale_error,
                      "receipt": stale_receipt,
                      "owner_rows_appended": stale_after_rows[len(stale_before_rows):],
                      "w_down_after": down_state(dpy, codes["w"]),
                      "a_down_after": down_state(dpy, codes["a"]) }
        work["cases"].append(stale_case)
        if stale_error is None or stale_receipt is not None or not stale_case["w_down_after"] or not stale_case["a_down_after"]:
            raise RuntimeError("stale foreign-intent release did not fail closed")
        explicit_up(lease2, "w", "two_key_order_1")
        if down_state(dpy, codes["w"]) or not down_state(dpy, codes["a"]):
            raise RuntimeError("W/A sequential release order did not hold")
        explicit_up(lease2, "a", "two_key_order_2")
        teardown2_before = snapshot(owner)
        teardown2 = owner.call("release", lease2)
        teardown2_after = snapshot(owner)
        if down_state(dpy, codes["w"]) or down_state(dpy, codes["a"]) or not teardown2.get("verified"):
            raise RuntimeError("two-key teardown was not verified neutral")
        work["cases"].append({"event": "teardown", "case": "two_key", "receipt": teardown2,
                              "owner_rows_appended": teardown2_after[len(teardown2_before):],
                              "w_down_after": down_state(dpy, codes["w"]),
                              "a_down_after": down_state(dpy, codes["a"])})

        # Case 3: cancellation causes autonomous W cleanup; A is never admitted.
        lease3 = new_lease(3)
        admit(lease3, "w")
        lease3.cancel.set()
        cancel_start_ns = time.perf_counter_ns()
        cancel_error = None
        try:
            owner.call("down", lease3, "a")
        except Exception as exc:
            cancel_error = {"type": type(exc).__name__, "message": str(exc)}
        wait_started_ns = time.perf_counter_ns()
        deadline = time.monotonic() + 0.5
        cancel_snapshot = snapshot(owner)
        while time.monotonic() < deadline:
            cancel_snapshot = snapshot(owner)
            found = any(row.get("event") == "owner_release" and row.get("reason") == "cancelled"
                        and row.get("intent_token") == lease3.intent_token for row in cancel_snapshot)
            if found:
                break
            time.sleep(0.005)
        wait_finished_ns = time.perf_counter_ns()
        cancel_rows = [row for row in cancel_snapshot if row.get("event") == "owner_release"
                       and row.get("reason") == "cancelled" and row.get("intent_token") == lease3.intent_token]
        cancel_case = {"event": "cancel_cleanup", "intent_token": lease3.intent_token,
                       "requested_ns": cancel_start_ns, "cancelled_down_error": cancel_error,
                       "a_down_after": down_state(dpy, codes["a"]),
                       "w_down_after": down_state(dpy, codes["w"]),
                       "receipt_wait_started_ns": wait_started_ns,
                       "receipt_wait_finished_ns": wait_finished_ns,
                       "receipt_wait_cap_ms": 500, "owner_rows": cancel_rows,
                       "owner_snapshot": cancel_snapshot}
        work["cases"].append(cancel_case)
        if cancel_error is None or cancel_error["type"] != "Cancelled":
            raise RuntimeError("cancelled A admission was not rejected")
        if cancel_case["a_down_after"] or cancel_case["w_down_after"] or len(cancel_rows) != 1:
            raise RuntimeError("bounded cancelled owner cleanup was not observed neutral")
        teardown3 = owner.call("release", lease3)
        if not teardown3.get("verified"):
            raise RuntimeError("cancellation teardown receipt not verified")
        work["cases"].append({"event": "teardown", "case": "cancel", "receipt": teardown3,
                              "w_down_after": down_state(dpy, codes["w"]),
                              "a_down_after": down_state(dpy, codes["a"])})

        work["owner_snapshots"] = snapshot(owner)
        work["candidate_completed"] = True
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        work["errors"].append(failure)
        work["candidate_completed"] = False
    finally:
        if owner is not None:
            try:
                owner.close()
            except Exception as exc:
                work["errors"].append({"stage": "owner_close", "type": type(exc).__name__, "message": str(exc)})
            work["owner_thread_stopped"] = bool(owner._inner.stopped.is_set() and not owner._inner.thread.is_alive())
            work["owner_snapshots_final"] = snapshot(owner)
        if target is not None:
            try:
                target.destroy()
                dpy.sync()
            except Exception as exc:
                work["errors"].append({"stage": "window_destroy", "type": type(exc).__name__, "message": str(exc)})
        if dpy is not None:
            try:
                dpy.close()
            except Exception as exc:
                work["errors"].append({"stage": "display_close", "type": type(exc).__name__, "message": str(exc)})
        if xvfb is not None:
            try:
                if xvfb.poll() is None:
                    xvfb.terminate()
                xvfb.wait(timeout=2)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=2)
                work["errors"].append({"stage": "xvfb_shutdown", "type": "TimeoutExpired", "message": "Xvfb did not terminate gracefully"})
            work["processes_clean"] = xvfb.poll() is not None
            work["xvfb_exit_code"] = xvfb.returncode
        if xvfb_log is not None:
            xvfb_log.close()
        work["candidate_finished_ns"] = time.perf_counter_ns()
        work["candidate_status"] = "PASS_CANDIDATE_SHAPE" if work.get("candidate_completed") and not work["errors"] and work["processes_clean"] and work["owner_thread_stopped"] else "STOP_CANDIDATE"
        RAW_PATH.write_text(json.dumps(work, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if work["candidate_status"] == "PASS_CANDIDATE_SHAPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
