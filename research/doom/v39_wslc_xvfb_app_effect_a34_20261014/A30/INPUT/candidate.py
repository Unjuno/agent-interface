"""One-shot V4 owner-to-X11 application-effect and lease-expiry experiment."""
import argparse
import ast
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY_NAME = "a"
LEASE_NS = 300_000_000
APP_RESPONSE_BOUND_NS = 200_000_000
RECOVERY_BOUND_NS = 1_000_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Lease:
    def __init__(self, expected_focus):
        import threading
        self.deadline = None
        self.expected_focus = expected_focus
        self.intent_token = "MAP01-V39-WSLC-A30-20261014-01"
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.interruption = None

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("unexpected cancellation")
        if self.deadline is not None and time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired before admission")

    def record_interruption(self, row):
        self.interruption = row


def next_x_event(connection, until_ns):
    while time.perf_counter_ns() < until_ns:
        if connection.pending_events():
            return connection.next_event()
        remaining = max(0.0, (until_ns - time.perf_counter_ns()) / 1e9)
        ready, _, _ = select.select([connection.fileno()], [], [], min(remaining, 0.02))
        if ready:
            return connection.next_event()
    return None


def property_value(window, atom, x):
    value = window.get_full_property(atom, x.AnyPropertyType)
    if value is None or len(value.value) != 1:
        return None
    return int(value.value[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default="127.0.0.1:143")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; preserving one-shot first outcome")
    args.out.mkdir(parents=True)

    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {
        "schema": "map01-v39-wslc-xvfb-app-effect-raw-a30-v1",
        "experiment_id": freeze["experiment_id"],
        "status": "STOP",
        "errors": [],
        "scope": "synthetic X11 app; no game, model, physical input, or desktop control",
        "runtime": {"python": sys.version, "uid": int(os.environ.get("WSLC_UID", "0")), "display": args.display},
        "source_sha256": {},
        "key_events": [],
        "task_effect": {"initial_counter": None, "after_keypress": None,
                         "after_release": None},
        "cleanup": {},
        "owner_records": [],
    }
    xvfb = target = verifier = owner = None
    try:
        for name, expected in freeze["source_sha256"].items():
            actual = sha(HERE / name)
            raw["source_sha256"][name] = actual
            if actual != expected:
                raise RuntimeError("frozen source hash mismatch: " + name)
        if sha(HERE / "candidate.py") != freeze["candidate_sha256"]:
            raise RuntimeError("candidate hash mismatch")
        if sha(HERE / "auditor.py") != freeze["auditor_sha256"]:
            raise RuntimeError("auditor hash mismatch")
        if sha(HERE / "run-a30.sh") != freeze["runner_sha256"]:
            raise RuntimeError("runner hash mismatch")

        from Xlib import X, Xatom, XK, display
        server_display = ":" + args.display.rsplit(":", 1)[-1]
        xvfb_argv = ["Xvfb", server_display, "-screen", "0", "640x480x24",
                     "-listen", "tcp", "-nolisten", "unix", "-noreset", "-ac"]
        xvfb_started_ns = time.perf_counter_ns()
        xvfb = subprocess.Popen(xvfb_argv, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        raw["xvfb"] = {"argv": xvfb_argv, "pid": xvfb.pid,
                       "started_ns": xvfb_started_ns}
        connect_deadline = time.monotonic() + 5.0
        while time.monotonic() < connect_deadline:
            if xvfb.poll() is not None:
                detail = xvfb.stderr.read().decode("utf-8", "replace")
                raise RuntimeError("Xvfb exited before connect: " + detail)
            try:
                target = display.Display(args.display)
                break
            except Exception:
                time.sleep(0.025)
        if target is None:
            raise TimeoutError("target X11 app connection exceeded 5 seconds")

        screen = target.screen()
        root = screen.root
        window = root.create_window(20, 20, 320, 200, 0, screen.root_depth,
                                    X.InputOutput, X.CopyFromParent,
                                    event_mask=X.KeyPressMask | X.KeyReleaseMask)
        window.map()
        counter_atom = target.intern_atom("_A30_TASK_COUNTER")
        window.change_property(counter_atom, Xatom.CARDINAL, 32, [0])
        target.sync()
        target.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        target.sync()
        verifier = display.Display(args.display)
        verified_focus = verifier.get_input_focus().focus
        focus_id = verified_focus.id if hasattr(verified_focus, "id") else verified_focus
        if focus_id != window.id:
            raise RuntimeError("target app did not acquire X11 input focus")
        verifier_window = verifier.create_resource_object("window", window.id)
        initial_counter = property_value(verifier_window, counter_atom, X)
        raw["target_app"] = {"window_id": int(window.id),
                             "counter_property": "_A30_TASK_COUNTER",
                             "initial_counter_verified_by_second_connection": initial_counter,
                             "focus_id": int(focus_id)}
        raw["task_effect"]["initial_counter"] = initial_counter

        # Match the production composition: V4 joins V3 transitions to V12 owner receipts.
        exception_module = type(sys)("executor_v3")
        exception_module.Cancelled = type("Cancelled", (Exception,), {})
        exception_module.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = exception_module
        sys.path.insert(0, str(HERE))
        from input_transition_owner_v4 import InputOwner
        owner = InputOwner(args.display)
        raw["owner_id"] = owner.owner_id
        raw["image_identity"] = freeze["image"]
        lease = Lease(int(window.id))
        raw["lease"] = {"deadline_ns": None,
                        "duration_ns": LEASE_NS,
                        "recovery_bound_ns": RECOVERY_BOUND_NS,
                        "app_response_bound_ns": APP_RESPONSE_BOUND_NS,
                        "intent_token": lease.intent_token,
                        "cancel_requested_before_expiry": False}

        raw["input_dispatch_attempted"] = True
        admission = owner.call("down", lease, KEY_NAME)
        raw["admission"] = admission
        if type(admission) is not dict or admission.get("event") != "input_admission":
            raise RuntimeError("V4 did not return an input-admission receipt")
        expected_code = int(target.keysym_to_keycode(XK.string_to_keysym(KEY_NAME)))
        if admission.get("key") != KEY_NAME or admission.get("owner_id") != owner.owner_id:
            raise RuntimeError("admission identity did not match owner/key")
        if admission.get("intent_token") != lease.intent_token:
            raise RuntimeError("admission intent did not match lease")
        if type(admission.get("input_ack_ns")) is not int:
            raise RuntimeError("admission lacked monotonic input acknowledgement")
        lease.deadline = admission["input_ack_ns"] + LEASE_NS
        raw["lease"]["deadline_ns"] = lease.deadline
        raw["lease"]["input_ack_ns"] = admission["input_ack_ns"]
        raw["keycode"] = expected_code

        press_deadline = min(lease.deadline, admission["input_ack_ns"] + APP_RESPONSE_BOUND_NS)
        press = None
        while time.perf_counter_ns() < press_deadline:
            event = next_x_event(target, press_deadline)
            if event is None:
                break
            if event.type not in (X.KeyPress, X.KeyRelease):
                continue
            event_row = {"type": int(event.type), "keycode": int(event.detail),
                         "window_id": int(event.window.id),
                         "observed_ns": time.perf_counter_ns()}
            raw["key_events"].append(event_row)
            if (event.type == X.KeyPress and event.detail == expected_code
                    and event.window.id == window.id):
                press = event_row
                count_before = property_value(verifier_window, counter_atom, X)
                if count_before != 0:
                    raise RuntimeError("task counter changed before target keypress")
                # The X11 application handles one matching keypress as its task action.
                window.change_property(counter_atom, Xatom.CARDINAL, 32, [1])
                target.sync()
                app_update_ns = time.perf_counter_ns()
                count_after = property_value(verifier_window, counter_atom, X)
                observed_ns = time.perf_counter_ns()
                raw["task_effect"].update({
                    "counter_before_action": count_before,
                    "app_property_write_ns": app_update_ns,
                    "after_keypress": count_after,
                    "server_observed_ns": observed_ns,
                })
                raw["task_effect"]["response_latency_ns"] = (
                    observed_ns - admission["input_ack_ns"])
                break
        if press is None:
            raise TimeoutError("target app did not receive matching KeyPress within 200ms")

        release_deadline = lease.deadline + RECOVERY_BOUND_NS
        release_event = None
        while time.perf_counter_ns() < release_deadline:
            event = next_x_event(target, release_deadline)
            if event is None:
                break
            if event.type not in (X.KeyPress, X.KeyRelease):
                continue
            event_row = {"type": int(event.type), "keycode": int(event.detail),
                         "window_id": int(event.window.id),
                         "observed_ns": time.perf_counter_ns()}
            raw["key_events"].append(event_row)
            if (event.type == X.KeyRelease and event.detail == expected_code
                    and event.window.id == window.id):
                release_event = event_row
                break
        if release_event is None:
            raise TimeoutError("target app did not receive expiry KeyRelease within 1s")
        raw["release_event"] = release_event
        raw["release_event_overshoot_ns"] = release_event["observed_ns"] - lease.deadline
        keymap_sample_ns = time.perf_counter_ns()
        bitmap = verifier.query_keymap()
        key_up = not bool(bitmap[expected_code // 8] & (1 << (expected_code % 8)))
        raw["server_keymap"] = {"source": "XQueryKeymap on second X11 connection",
                                "sampled_ns": keymap_sample_ns,
                                "key_up": key_up}
        raw["task_effect"]["after_release"] = property_value(
            verifier_window, counter_atom, X)

        receipt_deadline = lease.deadline + RECOVERY_BOUND_NS
        expiry_receipt = None
        while time.perf_counter_ns() < receipt_deadline:
            expiry_receipt = next((row for row in reversed(owner.records)
                                   if type(row) is dict and row.get("event") == "owner_release"
                                   and row.get("reason") == "expired"), None)
            if expiry_receipt is not None:
                break
            time.sleep(0.002)
        if expiry_receipt is None:
            raise TimeoutError("V12 owner did not record expiry release within 1s")
        raw["expiry_release"] = expiry_receipt
        raw["expiry_terminal"] = {
            "event": "terminal", "status": "expired", "release": expiry_receipt,
        }
        raw["expiry_verified_overshoot_ns"] = expiry_receipt.get("verified_ns", 0) - lease.deadline
        raw["owner_records_before_close"] = owner.records
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["errors"].append(type(exc).__name__ + ": " + str(exc))
    finally:
        if owner is not None:
            try:
                owner.close()
                raw["owner_records"] = owner.records
                raw["cleanup"].update({
                    "owner_closed": owner._inner.closed,
                    "owner_stopped": owner._inner.stopped.is_set(),
                    "owner_thread_alive": owner._inner.thread.is_alive(),
                    "owner_error": (None if owner._inner.error is None
                                    else repr(owner._inner.error)),
                })
            except BaseException as exc:
                raw["cleanup"]["owner_close_error"] = type(exc).__name__ + ": " + str(exc)
        if verifier is not None:
            try:
                verifier.close()
            except BaseException as exc:
                raw["cleanup"]["verifier_close_error"] = type(exc).__name__ + ": " + str(exc)
        if target is not None:
            try:
                target.close()
            except BaseException as exc:
                raw["cleanup"]["target_close_error"] = type(exc).__name__ + ": " + str(exc)
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as exc:
                raw["cleanup"]["xvfb_error"] = type(exc).__name__ + ": " + str(exc)
                xvfb.kill()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
        raw["cleanup"]["finished_ns"] = time.perf_counter_ns()
        raw["cleanup"]["xvfb_runtime_ns"] = (
            raw["cleanup"]["finished_ns"] - raw.get("xvfb", {}).get("started_ns", 0))
        (args.out / "RAW.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": raw["status"], "errors": raw["errors"],
                      "cleanup": raw["cleanup"]}, sort_keys=True))
    return 0 if raw["status"] == "CANDIDATE_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())