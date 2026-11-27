"""One-shot WSLc test of V10 release evidence against the V39 predicate."""
import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
LEASE_NS = 300_000_000
APP_RESPONSE_NS = 200_000_000
RECOVERY_NS = 1_000_000_000
INTENT = "MAP01-V39-WSLC-V10-A35-20261015-01"


class Lease:
    def __init__(self, focus):
        import threading
        self.deadline = time.perf_counter_ns() + LEASE_NS
        self.expected_focus = focus
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.interruption = None

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("unexpected cancellation")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired before input admission")

    def record_interruption(self, record):
        self.interruption = record


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_message(process, timeout_ns):
    return read_message_until(process, time.perf_counter_ns() + timeout_ns)


def read_message_until(process, deadline):
    while time.perf_counter_ns() < deadline:
        remaining = max(0.0, (deadline - time.perf_counter_ns()) / 1e9)
        readable, _, _ = select.select([process.stdout], [], [], min(remaining, .02))
        if readable:
            line = process.stdout.readline()
            if not line:
                return None
            return json.loads(line)
    return None


def property_value(window, atom, x):
    value = window.get_full_property(atom, x.AnyPropertyType)
    if value is None or len(value.value) != 1:
        return None
    return int(value.value[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":177")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("output already exists; refusing allocation retry")
    args.out.mkdir(parents=True)

    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {
        "schema": "map01-v39-wslc-v10-owner-effect-raw-a35-v1",
        "experiment_id": freeze["experiment_id"],
        "status": "STOP",
        "errors": [],
        "scope": "V10 X11 input-owner integration with a separate synthetic app; no Doom, model, desktop, or physical input",
        "runtime": {"python": sys.version, "uid": os.getuid(),
                    "display": args.display},
        "source_sha256": {},
        "app_messages": [],
        "task_effect": {"initial_counter": None,
                        "after_keypress": None,
                        "independent_counter_after_keypress": None},
        "owner_records": [],
        "cleanup": {},
    }
    dispatched = False
    xvfb = app = owner = target = verifier = None
    try:
        for name, expected in freeze["source_sha256"].items():
            actual = digest(HERE / name)
            raw["source_sha256"][name] = actual
            if actual != expected:
                raise RuntimeError("frozen production source mismatch: " + name)
        for name, expected in freeze["artifact_sha256"].items():
            actual = digest(HERE / name)
            if actual != expected:
                raise RuntimeError("frozen artifact mismatch: " + name)

        from Xlib import X, Xatom, XK, display
        number = args.display.rsplit(":", 1)[-1]
        server_display = ":" + number
        xvfb_argv = ["Xvfb", server_display, "-screen", "0", "640x480x24",
                     "-nolisten", "tcp", "-noreset", "-ac"]
        xvfb = subprocess.Popen(xvfb_argv, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        raw["xvfb"] = {"argv": xvfb_argv, "pid": xvfb.pid,
                       "started_ns": time.perf_counter_ns()}
        connect_until = time.monotonic() + 5.0
        while time.monotonic() < connect_until:
            if xvfb.poll() is not None:
                detail = xvfb.stderr.read().decode("utf-8", "replace")
                raise RuntimeError("Xvfb exited before connect: " + detail)
            try:
                target = display.Display(args.display)
                break
            except Exception:
                time.sleep(.025)
        if target is None:
            raise TimeoutError("Xvfb connection exceeded five seconds")

        exceptions = type(sys)("executor_v3")
        exceptions.Cancelled = type("Cancelled", (Exception,), {})
        exceptions.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = exceptions
        sys.path.insert(0, str(HERE))
        from input_owner_v10 import InputOwner

        app = subprocess.Popen(
            [sys.executable, str(HERE / "app_probe.py"), "--display", args.display],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1)
        ready = read_message(app, 5_000_000_000)
        raw["app_messages"].append(ready)
        if type(ready) is not dict or ready.get("event") != "app_ready":
            detail = "" if app.poll() is None else app.stderr.read()
            raise RuntimeError("separate app failed readiness: " + detail)
        target.sync()
        verifier = display.Display(args.display)
        x = X
        atom = int(ready["counter_atom"])
        window_id = int(ready["window_id"])
        focus = verifier.get_input_focus().focus
        focus_id = focus.id if hasattr(focus, "id") else int(focus)
        if focus_id != window_id or int(ready["focus_id"]) != window_id:
            raise RuntimeError("separate app did not own observed input focus")
        verify_window = verifier.create_resource_object("window", window_id)
        initial = property_value(verify_window, atom, x)
        raw["app"] = {"pid": app.pid, "window_id": window_id,
                      "counter_atom": atom, "focus_id": focus_id,
                      "initial_counter_observed_by_second_connection": initial}
        raw["task_effect"]["initial_counter"] = initial
        if initial != 0:
            raise RuntimeError("task counter was not initially zero")

        owner = InputOwner(args.display)
        raw["owner_id"] = owner.owner_id
        lease = Lease(window_id)
        raw["lease"] = {"intent": INTENT, "duration_ns": LEASE_NS,
                        "deadline_ns": lease.deadline,
                        "app_response_bound_ns": APP_RESPONSE_NS,
                        "recovery_bound_ns": RECOVERY_NS}
        keycode = int(target.keysym_to_keycode(XK.string_to_keysym("a")))
        raw["dispatch"] = {"owner_id": owner.owner_id, "operation": "down",
                           "key": "a", "keycode": keycode,
                           "intent": INTENT, "started_ns": time.perf_counter_ns(),
                           "deadline_ns": lease.deadline}
        dispatched = True
        admission = owner.call("down", lease, "a")
        raw["admission"] = admission
        if (type(admission) is not dict or
                admission.get("event") != "input_admission" or
                admission.get("key") != "a" or
                admission.get("valid_until_ns") != lease.deadline or
                type(admission.get("input_ack_ns")) is not int):
            raise RuntimeError("V10 admission did not match frozen dispatch")
        raw["lease"]["input_ack_ns"] = admission["input_ack_ns"]

        effect = read_message_until(
            app, admission["input_ack_ns"] + APP_RESPONSE_NS)
        if effect is None:
            raise TimeoutError("separate app did not report keypress effect in 200ms")
        raw["app_messages"].append(effect)
        raw["task_effect"]["after_keypress"] = effect.get("counter_after")
        raw["task_effect"]["effect_ns"] = effect.get("effect_ns")
        observe_until = admission["input_ack_ns"] + APP_RESPONSE_NS
        observed = None
        while time.perf_counter_ns() < observe_until:
            observed = property_value(verify_window, atom, x)
            if observed == 1:
                break
            time.sleep(.001)
        raw["task_effect"]["independent_counter_after_keypress"] = observed
        raw["task_effect"]["response_latency_ns"] = (
            int(effect["effect_ns"]) - admission["input_ack_ns"])

        release_until = lease.deadline + RECOVERY_NS
        release_message = None
        while time.perf_counter_ns() < release_until:
            if lease.interruption is not None and release_message is not None:
                break
            message = read_message(app, min(20_000_000,
                                   max(0, release_until - time.perf_counter_ns())))
            if message is not None:
                raw["app_messages"].append(message)
                if message.get("event") == "app_keyrelease":
                    release_message = message
            elif owner.stopped.is_set():
                break
        release_record = lease.interruption
        raw["expiry_release"] = release_record
        raw["app_release"] = release_message
        raw["owner_expiry_overshoot_ns"] = (
            release_record.get("verified_ns") - lease.deadline
            if type(release_record) is dict else None)

        sample_ns = time.perf_counter_ns()
        bitmap = verifier.query_keymap()
        key_up = not bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
        counter_after_release = property_value(verify_window, atom, x)
        raw["server_keymap"] = {"sampled_ns": sample_ns,
                               "source": "independent X11 connection query_keymap",
                               "keycode": keycode, "key_up": key_up}
        raw["task_effect"]["after_release"] = counter_after_release
        terminal = {"event": "terminal", "id": "a35-one-shot",
                    "status": "expired", "release": release_record}
        raw["terminal"] = terminal

        if app.stdin is not None:
            app.stdin.write("STOP\n")
            app.stdin.flush()
            app.stdin.close()
        app.wait(timeout=2)
        app_message = read_message(app, 100_000_000)
        if app_message is not None:
            raw["app_messages"].append(app_message)
        raw["cleanup"]["app_exit"] = app.returncode
        app_stderr = app.stderr.read()
        raw["cleanup"]["app_stderr"] = app_stderr

        owner.close()
        raw["owner_records"] = owner.records
        raw["cleanup"].update({"owner_closed": owner.closed,
                               "owner_stopped": owner.stopped.is_set(),
                               "owner_thread_alive": owner.thread.is_alive(),
                               "owner_error": repr(owner.error) if owner.error else None})
        raw["candidate_complete"] = (
            effect.get("event") == "app_keypress_effect" and
            effect.get("counter_before") == 0 and effect.get("counter_after") == 1 and
            observed == 1 and release_message is not None and
            type(release_record) is dict and release_record.get("reason") == "expired" and
            release_record.get("verified") is True and key_up and
            owner.closed and owner.stopped.is_set() and not owner.thread.is_alive())
        raw["status"] = "CANDIDATE_COMPLETE" if raw["candidate_complete"] else "FAIL"
    except BaseException as exc:
        raw["errors"].append({"type": type(exc).__name__, "message": str(exc)[:500],
                              "dispatch_attempted": dispatched})
        raw["status"] = "FAIL" if dispatched else "STOP"
    finally:
        if owner is not None and not owner.closed:
            try:
                owner.close()
            except BaseException as exc:
                raw["cleanup"]["owner_close_error"] = type(exc).__name__ + ": " + str(exc)
            raw["owner_records"] = owner.records
        if app is not None and app.poll() is None:
            try:
                if app.stdin is not None and not app.stdin.closed:
                    app.stdin.write("STOP\n")
                    app.stdin.flush()
                    app.stdin.close()
                app.wait(timeout=2)
            except BaseException as exc:
                raw["cleanup"]["app_stop_error"] = type(exc).__name__ + ": " + str(exc)
                app.kill()
                app.wait()
        if verifier is not None:
            verifier.close()
        if target is not None:
            target.close()
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as exc:
                raw["cleanup"]["xvfb_error"] = type(exc).__name__ + ": " + str(exc)
                xvfb.kill()
                xvfb.wait()
        raw["finished_ns"] = time.perf_counter_ns()
        (args.out / "RAW.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if raw["status"] == "CANDIDATE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
