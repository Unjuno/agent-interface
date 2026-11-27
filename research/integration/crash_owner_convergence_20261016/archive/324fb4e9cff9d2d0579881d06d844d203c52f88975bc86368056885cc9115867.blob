"""Single Xvfb allocation testing core-X11 same-key source attribution."""
import hashlib
import json
import os
import secrets
import select
import signal
import subprocess
import struct
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


def decode_raw(event, xinput, keycode, byte_order):
    if event.type != 35 or event.evtype not in (xinput.RawKeyPress, xinput.RawKeyRelease):
        return None
    data = event.data
    if not isinstance(data, (bytes, bytearray)) or len(data) < 18:
        return {"decode_error": "short_or_nonbyte_generic_event", "length": len(data)}
    endian = "<" if byte_order == 0 else ">"
    deviceid, time_ms, detail, sourceid, flags, mask_len, _pad = struct.unpack_from(
        endian + "HIIHHHH", data, 0)
    if detail != keycode:
        return None
    return {"type": "RawKeyPress" if event.evtype == xinput.RawKeyPress else "RawKeyRelease",
            "deviceid": deviceid, "sourceid": sourceid, "detail": detail,
            "time": time_ms, "flags": flags, "valuators_mask_len": mask_len}


def drain_raw(observer, xinput, keycode):
    rows = []
    order = observer.display.info.image_byte_order
    while observer.pending_events():
        event = observer.next_event()
        row = decode_raw(event, xinput, keycode, order)
        if row is not None:
            rows.append(row)
    return rows


def wait_raw(observer, xinput, keycode, phase, timeout=1.0):
    expected = xinput.RawKeyPress if phase == "press" else xinput.RawKeyRelease
    deadline = time.monotonic() + timeout
    rows = []
    order = observer.display.info.image_byte_order
    while time.monotonic() < deadline:
        if select.select([observer], [], [], .02)[0]:
            while observer.pending_events():
                event = observer.next_event()
                row = decode_raw(event, xinput, keycode, order)
                if row is not None:
                    rows.append(row)
            if any(row.get("type") == ("RawKeyPress" if expected == xinput.RawKeyPress else "RawKeyRelease") for row in rows):
                return rows
    return rows


def main():
    global RAW
    OUT.mkdir(parents=True, exist_ok=False)
    result = {"schema": "v39-x11-shared-key-source-a36-raw-v1",
              "allocation_id": "V39-X11-SHARED-KEY-SOURCE-A36-20261012-01",
              "candidate_invocations": 1, "retries": 0,
              "physical_input": False, "game_or_model": False,
              "xvfb_tcp_enabled": False}
    RAW = result
    with tempfile.TemporaryDirectory(prefix="x11-source-a36-") as td:
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
            from Xlib.ext import xtest, xinput
            from input_owner_process_v1 import InputOwnerProcess, read_recovery_receipt
            from lease_release_v1 import Lease

            control = display.Display(":77")
            root = control.screen().root
            focus = root.create_window(20, 20, 300, 180, 0, X.CopyFromParent,
                                       X.InputOutput, X.CopyFromParent,
                                       event_mask=X.KeyPressMask | X.KeyReleaseMask)
            focus.map()
            focus.set_input_focus(X.RevertToParent, X.CurrentTime)
            root.change_property(control.intern_atom("_NET_ACTIVE_WINDOW"),
                                 Xatom.WINDOW, 32, [focus.id])
            control.sync()
            keycode = control.keysym_to_keycode(XK.string_to_keysym("a"))
            if not keycode:
                raise RuntimeError("keycode for allowlisted key a missing")
            # The focus window owner selects events on its own X connection.
            # This avoids relying on a second client's event selection.
            observer = display.Display(":77")
            xi_version = observer.xinput_query_version()
            if xi_version.major_version < 2:
                raise RuntimeError("XI2 version 2 is unavailable")
            observer_root = observer.screen().root
            raw_mask = xinput.RawKeyPressMask | xinput.RawKeyReleaseMask
            observer_root.xinput_select_events([(xinput.AllDevices, raw_mask)])
            observer.sync()
            xi_devices = [
                {"deviceid": int(d.deviceid), "name": str(d.name),
                 "use": int(d.use), "attachment": int(d.attachment),
                 "enabled": bool(d.enabled)}
                for d in observer.xinput_query_device(xinput.AllDevices).devices
            ]
            external = display.Display(":77")
            owner = InputOwnerProcess(":77", OUT / "input-owner-process")
            lease = Lease(time.perf_counter_ns() + 8_000_000_000)
            lease.expected_focus = focus.id
            lease.intent_token = "a36-owner-lease"

            initial = down(observer.query_keymap(), keycode)
            owner_down = owner.call("down", lease, "a")
            owner_raw_press_events = drain_raw(observer, xinput, keycode)
            owner_down_state = down(observer.query_keymap(), keycode)

            # A distinct X connection injects the same key while the owner's
            # hold is still active. The observer records XI2 Raw device IDs.
            xtest.fake_input(external, X.KeyPress, keycode)
            external.sync()
            external_client_logical_hold = True
            external_raw_press_events = wait_raw(observer, xinput, keycode, "press")
            after_external_state = down(observer.query_keymap(), keycode)

            owner_up = owner.call("up", lease, "a")
            key_release_events = wait_for(control, X, keycode, "KeyRelease")
            owner_raw_release_events = wait_raw(observer, xinput, keycode, "release")
            after_owner_release_state = down(control.query_keymap(), keycode)
            owner.close()
            owner_receipt_path = OUT / "input-owner-process" / "input-owner-recovery-v1.json"
            owner_receipt = read_recovery_receipt(owner_receipt_path, expected_display=":77")
            result.update({
                "display": ":77", "focus_id": focus.id, "keycode": keycode,
                "initial_keymap_down": initial,
                "owner_down": owner_down,
                "xi2_version": {"major": xi_version.major_version,
                                "minor": xi_version.minor_version},
                "xi2_devices": xi_devices,
                "owner_raw_press_events": owner_raw_press_events,
                "keymap_down_after_owner_press": owner_down_state,
                "external_client_keypress_issued": True,
                "external_client_logical_hold_during_owner_release": external_client_logical_hold,
                "external_raw_press_events": external_raw_press_events,
                "keymap_down_after_external_press": after_external_state,
                "owner_up": owner_up,
                "key_release_events_after_owner_up": key_release_events,
                "owner_raw_release_events": owner_raw_release_events,
                "keymap_down_after_owner_release": after_owner_release_state,
                "owner_return_code": owner.process.returncode,
                "owner_receipt": owner_receipt,
                "owner_receipt_sha256": hashlib.sha256(owner_receipt_path.read_bytes()).hexdigest(),
                "owner_receipt_verified_empty": owner_receipt.get("recovery_verified") is True,
                "external_client_source_state_is_test_side_only": True,
            })
            owner_sources = {row["sourceid"] for row in owner_raw_press_events}
            external_sources = {row["sourceid"] for row in external_raw_press_events}
            release_sources = {row["sourceid"] for row in owner_raw_release_events}
            result["raw_source_ids_by_phase"] = {
                "owner_press": sorted(owner_sources),
                "external_press": sorted(external_sources),
                "owner_release": sorted(release_sources),
            }
            result["same_xi2_source_for_both_clients"] = bool(
                owner_sources and external_sources and owner_sources == external_sources)
            result["pass"] = bool(
                not initial and owner_down_state and after_external_state and
                owner_raw_press_events and external_raw_press_events and owner_raw_release_events and
                external_client_logical_hold and not after_owner_release_state and
                owner_up.get("owner_thread_keyup_verified") is True and
                any(row["type"] == "KeyRelease" for row in key_release_events) and
                owner.process.returncode == 0 and owner_receipt.get("recovery_verified") is True)
            if result["pass"]:
                result["interpretation"] = (
                    "XI2 Raw events expose source-device IDs for both separate client "
                    "connections; the recorded source-ID comparison determines whether this "
                    "Xvfb/XTest path distinguishes those clients. Device IDs are not client IDs.")
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
