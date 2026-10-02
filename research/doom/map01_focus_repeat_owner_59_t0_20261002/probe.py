"""One-allocation Xvfb probe for focus-loss cleanup in the current InputOwner.

This is an integration mechanism probe, not gameplay or product-level evidence.
The script refuses an output directory that already exists and never retries.
"""

import argparse
import hashlib
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

from Xlib import X, XK, display
from Xlib.ext import xtest

ALLOCATION = "ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01"
OWNER_ROOT = Path(__file__).resolve().parents[2] / "live_control"
REPO_ROOT = OWNER_ROOT.parents[1]
sys.path.insert(0, str(OWNER_ROOT))
sys.path.insert(0, str(REPO_ROOT))
from research.live_control.input_owner_v10 import InputOwner


KEYSYM = "w"


class KeyLease:
    def __init__(self, expected_focus, deadline_ns):
        self.expected_focus = expected_focus
        self.deadline = deadline_ns
        self.cancel = threading.Event()

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("probe lease expired")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def event_pump(dpy, window, started, stop):
    rows = []
    while not stop.is_set():
        while dpy.pending_events():
            event = dpy.next_event()
            if event.type in (X.KeyPress, X.KeyRelease):
                rows.append({
                    "type": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                    "window": "B" if event.window.id == window else "OTHER",
                    "keycode": int(event.detail),
                    "time_ns": time.perf_counter_ns(),
                })
        stop.wait(.0005)
    return rows


def wait_for(predicate, deadline_ns):
    while time.perf_counter_ns() < deadline_ns:
        value = predicate()
        if value:
            return value
        time.sleep(.001)
    return None


def run(out):
    if out.exists():
        raise FileExistsError(f"output path already exists: {out}")
    out.mkdir(parents=True)
    display_number = 180 + (os.getpid() % 60)
    display_name = f":{display_number}"
    socket_path = Path(f"/tmp/.X11-unix/X{display_number}")
    lock_path = Path(f"/tmp/.X{display_number}-lock")
    if socket_path.exists() or lock_path.exists():
        raise RuntimeError(f"private display {display_name} is already occupied")
    raw = {
        "schema": "issue59-focus-repeat-owner-raw-v1",
        "allocation_id": ALLOCATION,
        "candidate_invocations": 1,
        "retries": 0,
        "xvfb_exit_code": None,
        "xvfb_socket_removed": False,
        "xvfb_lock_removed": False,
        "source_sha256": {
            "input_owner_v10.py": sha256(OWNER_ROOT / "input_owner_v10.py"),
            "executor_v3.py": sha256(OWNER_ROOT / "executor_v3.py"),
            "lease.py": sha256(OWNER_ROOT / "lease.py"),
        },
        "positive_control": {"window": "A", "keycode": None, "repeat_events": [], "verified_release": False},
        "trial": {},
        "claim_boundary": "single Xvfb / python-xlib owner integration mechanism only; no gameplay or MAP01 evidence",
    }
    xvfb = None
    owner = None
    control = None
    app_a = app_b = None
    pump_thread = None
    pump_stop = threading.Event()
    pump_rows = []
    error_text = None
    try:
        xvfb = subprocess.Popen(
            ["Xvfb", display_name, "-screen", "0", "800x600x24", "-nolisten", "tcp", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=(out / "xvfb.stderr").open("wb"),
            env={**os.environ, "DISPLAY": display_name},
        )
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"Xvfb exited early: {xvfb.returncode}")
            if socket_path.exists() and lock_path.exists():
                break
            time.sleep(.01)
        else:
            raise TimeoutError("private Xvfb startup timed out")
        env = {**os.environ, "DISPLAY": display_name, "XAUTHORITY": "/dev/null"}
        control = display.Display(display_name)
        screen = control.screen()
        root = screen.root
        win_a = root.create_window(30, 30, 240, 180, 0, screen.root_depth, X.CopyFromParent,
                                   X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win_b = root.create_window(320, 30, 240, 180, 0, screen.root_depth, X.CopyFromParent,
                                   X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win_a.map(); win_b.map(); control.sync()
        win_a.set_input_focus(X.RevertToParent, X.CurrentTime); control.sync()
        keycode = control.keysym_to_keycode(XK.string_to_keysym(KEYSYM))
        raw["positive_control"]["keycode"] = int(keycode)
        # Establish repeat stimulus without the owner, on the isolated private display.
        positive_started = time.perf_counter_ns()
        xtest.fake_input(control, X.KeyPress, keycode); control.sync()
        event_deadline = time.perf_counter() + .16
        while time.perf_counter() < event_deadline:
            if control.pending_events():
                event = control.next_event()
                if event.type == X.KeyPress:
                    raw["positive_control"]["repeat_events"].append({
                        "type": "KeyPress", "window": "A", "keycode": int(event.detail),
                        "time_ns": time.perf_counter_ns(),
                    })
            else:
                time.sleep(.001)
        xtest.fake_input(control, X.KeyRelease, keycode); control.sync()
        keymap = control.query_keymap()
        raw["positive_control"]["verified_release"] = not bool(
            keymap[keycode // 8] & (1 << (keycode % 8)))
        if len(raw["positive_control"]["repeat_events"]) < 2:
            raise RuntimeError("STOP_REPEAT_STIMULUS_NOT_ESTABLISHED")

        d_b = display.Display(display_name)
        b_id = win_b.id
        win_b.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
        pump_started = time.perf_counter_ns()
        pump_deadline = pump_started + 5_000_000_000
        pump_thread = threading.Thread(target=lambda: pump_rows.extend(
            event_pump(d_b, b_id, pump_started, pump_stop)), daemon=True)
        pump_thread.start()
        owner = InputOwner(display_name)
        owner_display = display.Display(display_name)
        current_focus = owner_display.get_input_focus().focus
        expected_a = current_focus.id if hasattr(current_focus, "id") else current_focus
        lease = KeyLease(expected_a, time.perf_counter_ns() + 2_000_000_000)
        key_name = XK.keysym_to_string(control.keycode_to_keysym(keycode, 0))
        admission = owner.call("down", lease, key_name)
        raw["trial"]["owner_admission"] = {
            "window": "A", "keycode": int(keycode),
            "admitted_ns": int(admission["admitted_ns"]), "ack_ns": int(admission["input_ack_ns"]),
        }
        changer = display.Display(display_name)
        before = time.perf_counter_ns()
        win_b.set_input_focus(X.RevertToParent, X.CurrentTime); changer.sync()
        focus_sync = time.perf_counter_ns()
        focus_b = changer.get_input_focus().focus
        observed_focus_b = focus_b.id if hasattr(focus_b, "id") else focus_b
        focus_observed_ns = time.perf_counter_ns()
        raw["trial"]["focus_change"] = {
            "from": "A", "to": "B", "request_ns": before, "sync_returned_ns": focus_sync,
            "observed_focus": "B" if observed_focus_b == b_id else str(observed_focus_b),
            "observed_ns": focus_observed_ns,
        }
        # The owner performs focus checks on a <=2ms queue wait. Wait for its verified release.
        release_record = wait_for(
            lambda: next((row for row in reversed(owner.records)
                          if row.get("event") == "owner_release" and row.get("reason") == "focus_changed"), None),
            time.perf_counter_ns() + 2_000_000_000,
        )
        if release_record is None:
            raise TimeoutError("owner did not record focus_changed release")
        # Sample the actual owner connection's focus checks as a bounded evidence trace.
        samples = []
        sample_d = display.Display(display_name)
        sample_deadline = time.perf_counter_ns() + 300_000_000
        while time.perf_counter_ns() < sample_deadline:
            started = time.perf_counter_ns()
            focus = sample_d.get_input_focus().focus
            finished = time.perf_counter_ns()
            samples.append({"focus": int(focus.id if hasattr(focus, "id") else focus),
                            "started_ns": started, "finished_ns": finished})
            if release_record.get("verified_ns") is not None and finished >= release_record["verified_ns"]:
                break
            time.sleep(.001)
        raw["trial"]["owner_focus_samples"] = [
            {**s, "focus": "A" if s["focus"] == expected_a else ("B" if s["focus"] == b_id else str(s["focus"]))}
            for s in samples
        ]
        release_request_ns = int(release_record.get("release_requested_ns", focus_observed_ns))
        raw["trial"]["owner_release"] = {
            "reason": "focus_changed", "keycode": int(keycode),
            "request_ns": release_request_ns,
            "sync_returned_ns": int(release_record["verified_ns"]),
            "verified_ns": int(release_record["verified_ns"]),
            "verified_empty": bool(release_record.get("verified") is True and not release_record.get("keys_down")),
            "keys_down": list(release_record.get("keys_down", [])),
        }
        time.sleep(.10)
        pump_stop.set(); pump_thread.join(timeout=1)
        pump_stopped = time.perf_counter_ns()
        raw["trial"]["new_focus_event_pump"] = {
            "window": "B", "started_ns": int(pump_started), "stopped_ns": int(pump_stopped),
            "complete": not pump_thread.is_alive(), "events": pump_rows,
        }
        changer.close(); sample_d.close(); owner_display.close(); d_b.close()
        owner.close(); owner = None
    except BaseException:
        error_text = traceback.format_exc()
        raw["error"] = error_text
    finally:
        pump_stop.set()
        if pump_thread is not None and pump_thread.is_alive():
            pump_thread.join(timeout=1)
        if owner is not None:
            try:
                owner.close()
                raw["owner_close_verified"] = True
            except BaseException as exc:
                raw["owner_close_error"] = repr(exc)
        if control is not None:
            try:
                control.close()
            except BaseException:
                pass
        if xvfb is not None:
            xvfb.terminate()
            try:
                raw["xvfb_exit_code"] = int(xvfb.wait(timeout=2))
            except subprocess.TimeoutExpired:
                xvfb.kill(); raw["xvfb_exit_code"] = int(xvfb.wait())
        raw["xvfb_socket_removed"] = not socket_path.exists()
        raw["xvfb_lock_removed"] = not lock_path.exists()
        (out / "raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        spec = importlib.util.spec_from_file_location("focus_repeat_audit", Path(__file__).with_name("audit.py"))
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        (out / "classification.json").write_text(
            json.dumps(audit.classify(raw), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if error_text:
            (out / "error.txt").write_text(error_text, encoding="utf-8")
    return 1 if error_text else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.out.resolve()))


if __name__ == "__main__":
    main()
