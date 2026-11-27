"""Single Xvfb allocation testing core-X11 same-key source attribution."""
import hashlib
import json
import os
import secrets
import select
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LIVE = Path(__file__).resolve().parents[2] / "live_control"
sys.path.insert(0, str(LIVE))
OUT = Path(os.environ["V15_OWNER_OUT"])
RAW = None


def down(bitmap, code):
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def drain(observer, X, keycode):
    rows = []
    while observer.pending_events():
        event = observer.next_event()
        if event.type in (X.KeyPress, X.KeyRelease) and event.detail == keycode:
            rows.append({"type": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                         "keycode": event.detail, "time": getattr(event, "time", None)})
    return rows


def wait_for(observer, X, code, event_type, timeout=1.5):
    deadline = time.monotonic() + timeout
    seen = []
    while time.monotonic() < deadline:
        if select.select([observer], [], [], .02)[0]:
            seen.extend(drain(observer, X, code))
            if any(row["type"] == event_type for row in seen):
                return seen
        else:
            seen.extend(drain(observer, X, code))
            if any(row["type"] == event_type for row in seen):
                return seen
    return seen


def main():
    global RAW
    OUT.mkdir(parents=True, exist_ok=False)
    result = {"schema": "v39-x11-shared-key-source-a34-raw-v1",
              "allocation_id": "V39-X11-SHARED-KEY-SOURCE-A34-20261012-01",
              "candidate_invocations": 1, "retries": 0,
              "physical_input": False, "game_or_model": False,
              "xvfb_tcp_enabled": False}
    RAW = result
    with tempfile.TemporaryDirectory(prefix="x11-source-a34-") as td:
        auth = Path(td) / "Xauthority"
        cookie = secrets.token_hex(16)
        subprocess.run(["xauth", "-f", str(auth), "add", ":77",
                        "MIT-MAGIC-COOKIE-1", cookie], check=True,
                       capture_output=True, text=True)
        os.environ["XAUTHORITY"] = str(auth)
        os.environ["DISPLAY"] = ":77"
        env = dict(os.environ)
        xvfb = subprocess.Popen(
            ["Xvfb", ":77", "-screen", "0", "640x480x24", "-nolisten", "tcp",
             "-auth", str(auth)], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env)
        owner = control = external = observer = None
        try:
            time.sleep(.1)
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited during startup")
            from Xlib import X, Xatom, XK, display
            from Xlib.ext import xtest
            from input_owner_process_v1 import InputOwnerProcess, read_recovery_receipt
            from lease_release_v1 import Lease

            control = display.Display(":77")
            root = control.screen().root
            focus = root.create_window(20, 20, 300, 180, 0, X.CopyFromParent,
                                       X.InputOutput, X.CopyFromParent)
            focus.map()
            focus.set_input_focus(X.RevertToParent, X.CurrentTime)
            root.change_property(control.intern_atom("_NET_ACTIVE_WINDOW"),
                                 Xatom.WINDOW, 32, [focus.id])
            control.sync()
            keycode = control.keysym_to_keycode(XK.string_to_keysym("a"))
            if not keycode:
                raise RuntimeError("keycode for allowlisted key a missing")
            observer = display.Display(":77")
            observer.create_resource_object("window", focus.id).change_attributes(
                event_mask=X.KeyPressMask | X.KeyReleaseMask)
            observer.sync()
            external = display.Display(":77")
            owner = InputOwnerProcess(":77", OUT / "input-owner-process")
            lease = Lease(time.perf_counter_ns() + 8_000_000_000)
            lease.expected_focus = focus.id
            lease.intent_token = "a34-owner-lease"

            initial = down(observer.query_keymap(), keycode)
            owner_down = owner.call("down", lease, "a")
            owner_press_events = wait_for(observer, X, keycode, "KeyPress")
            owner_down_state = down(observer.query_keymap(), keycode)

            # Model a distinct client's logical hold. Core XTest has no
            # per-client down-state reference count; this request uses a
            # different X connection from the process-owned service.
            xtest.fake_input(external, X.KeyPress, keycode)
            external.sync()
            external_client_logical_hold = True
            time.sleep(.05)
            external_press_events = drain(observer, X, keycode)
            after_external_state = down(observer.query_keymap(), keycode)

            owner_up = owner.call("up", lease, "a")
            key_release_events = wait_for(observer, X, keycode, "KeyRelease")
            after_owner_release_state = down(observer.query_keymap(), keycode)
            owner.close()
            owner_receipt_path = OUT / "input-owner-process" / "input-owner-recovery-v1.json"
            owner_receipt = read_recovery_receipt(owner_receipt_path, expected_display=":77")
            result.update({
                "display": ":77", "focus_id": focus.id, "keycode": keycode,
                "initial_keymap_down": initial,
                "owner_down": owner_down,
                "owner_press_events": owner_press_events,
                "keymap_down_after_owner_press": owner_down_state,
                "external_client_keypress_issued": True,
                "external_client_logical_hold_during_owner_release": external_client_logical_hold,
                "external_press_events": external_press_events,
                "keymap_down_after_external_press": after_external_state,
                "owner_up": owner_up,
                "key_release_events_after_owner_up": key_release_events,
                "keymap_down_after_owner_release": after_owner_release_state,
                "owner_return_code": owner.process.returncode,
                "owner_receipt": owner_receipt,
                "owner_receipt_sha256": hashlib.sha256(owner_receipt_path.read_bytes()).hexdigest(),
                "owner_receipt_verified_empty": owner_receipt.get("recovery_verified") is True,
                "external_client_source_state_is_test_side_only": True,
            })
            result["pass"] = bool(
                not initial and owner_down_state and after_external_state and
                external_client_logical_hold and not after_owner_release_state and
                owner_up.get("owner_thread_keyup_verified") is True and
                any(row["type"] == "KeyRelease" for row in key_release_events) and
                owner.process.returncode == 0 and owner_receipt.get("recovery_verified") is True)
            if result["pass"]:
                result["interpretation"] = (
                    "Core X11 keymap and KeyRelease are global for this keycode: the "
                    "process owner verified release while the separate client's test-side "
                    "logical hold flag remained true. The server exposed no independent "
                    "per-client held state in this core-XTest path.")
            else:
                raise RuntimeError("source-attribution decision conjunction failed")
        finally:
            if owner is not None and owner.process.poll() is None:
                # Any failure retains state and avoids a forced display-reuse claim.
                owner.process.kill()
                owner.process.wait(timeout=3)
            for connection in (external, observer, control):
                if connection is not None:
                    connection.close()
            xvfb.terminate()
            try:
                result["xvfb_return_code"] = xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                result["xvfb_return_code"] = xvfb.wait(timeout=3)
            result["xvfb_stderr"] = xvfb.stderr.read()
            if xvfb.stdout:
                xvfb.stdout.close()
            xvfb.stderr.close()
            result["pass"] = bool(result.get("pass") and result["xvfb_return_code"] == 0)
    raw_path = OUT / "RAW.json"
    raw_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"raw": str(raw_path), "pass": result.get("pass")}))
    if not result.get("pass"):
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if RAW is not None:
            RAW["candidate_error"] = {"type": type(exc).__name__, "message": str(exc)[:1000]}
            RAW["pass"] = False
            if OUT.exists():
                (OUT / "RAW.json").write_text(
                    json.dumps(RAW, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
