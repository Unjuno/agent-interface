from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from Xlib import X, XK, display
from Xlib.ext import xtest
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError

OUT = Path(os.environ["OUT"])
FORMULA = "=B2*A2"
UNSUPPORTED = FORMULA + "€"
CASES = [("de-00", True), ("de-01", True), ("de-02", True), ("us-control", False)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_xev(text: str) -> list[dict]:
    rows = []
    for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
        kind = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not kind:
            continue
        key = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        state = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        payload = ""
        if lookup and lookup.group(1).strip():
            try:
                payload = bytes.fromhex(lookup.group(1)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                payload = "<non-ascii>"
        rows.append({"type": kind.group(1), "keycode": int(key.group(1)) if key else None,
                     "keysym": key.group(2).strip() if key else None,
                     "state": int(state.group(1), 16) if state else None, "lookup_ascii": payload})
    return rows


def core_map_snapshot(d) -> dict:
    info = d.display.info
    rows = [list(map(int, row)) for row in d.get_keyboard_mapping(info.min_keycode, info.max_keycode - info.min_keycode + 1)]
    return {"rows": rows, "sha256": hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()}


def run_case(case_id: str, german: bool) -> dict:
    number = 99 + CASES.index((case_id, german))
    name = f":{number}"
    env = dict(os.environ, DISPLAY=name)
    xvfb = subprocess.Popen(["Xvfb", name, "-screen", "0", "1280x800x24", "-nolisten", "tcp", "-noreset"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    receiver = backend = xev = None
    case_dir = OUT / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=False)
    row = {"case": case_id, "layout_expected": "de" if german else "us", "xvfb_noreset": True,
           "receiver_kind": "InputOnly", "control": None, "unsupported": None, "candidate": None,
           "events": [], "emissions": None, "held_keycodes_after": None}
    try:
        for _ in range(100):
            try:
                receiver = display.Display(name)
                break
            except Exception:
                time.sleep(0.05)
        if receiver is None:
            raise RuntimeError("Xvfb did not become ready")
        screen = receiver.screen()
        win = screen.root.create_window(8, 8, 1, 1, 0, X.CopyFromParent, X.InputOnly,
                                        X.CopyFromParent, event_mask=0)
        win.map(); receiver.sync()
        win.set_input_focus(X.RevertToParent, X.CurrentTime); receiver.sync()
        focus = receiver.get_input_focus().focus
        row["receiver_xid"] = int(win.id)
        row["receiver_class"] = int(win.get_attributes()._data["win_class"])
        row["focus_xid"] = int(focus.id) if hasattr(focus, "id") else int(focus)
        row["focus_asserted"] = row["focus_xid"] == int(win.id)
        xev_path = case_dir / "xev.log"
        xev_log = xev_path.open("wb")
        xev = subprocess.Popen(["stdbuf", "-oL", "xev", "-id", hex(int(win.id)), "-event", "keyboard"],
                               env=env, stdin=subprocess.DEVNULL, stdout=xev_log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if xev.poll() is not None:
                raise RuntimeError(f"xev receiver exited {xev.returncode}")
            if xev_path.stat().st_size > 0:
                break
            time.sleep(0.05)
        baseline_query = subprocess.run(["setxkbmap", "-display", name, "-query"], capture_output=True, text=True, timeout=10)
        row["baseline_query"] = baseline_query.stdout
        row["baseline_query_rc"] = baseline_query.returncode
        row["baseline_core_map"] = core_map_snapshot(receiver)
        baseline_dump = subprocess.run(["xkbcomp", "-xkb", name, "-"], capture_output=True, text=True, timeout=10)
        row["baseline_server_xkb_dump"] = baseline_dump.stdout
        row["baseline_server_xkb_dump_rc"] = baseline_dump.returncode
        row["baseline_server_xkb_dump_sha256"] = hashlib.sha256(baseline_dump.stdout.encode()).hexdigest()
        row["baseline_server_xkb_dump_stderr"] = baseline_dump.stderr
        if baseline_query.returncode or "layout:     us" not in baseline_query.stdout:
            row["status"] = "STOP_BASELINE_NOT_US"
            return row
        if baseline_dump.returncode or not baseline_dump.stdout:
            row["status"] = "STOP_BASELINE_DUMP"
            return row

        # Receiver-only XTEST control: must arrive before any candidate text.
        key_a = receiver.keysym_to_keycode(XK.string_to_keysym("a"))
        control_start = xev_path.stat().st_size
        xtest.fake_input(receiver, X.KeyPress, key_a); xtest.fake_input(receiver, X.KeyRelease, key_a); receiver.sync()
        time.sleep(0.15)
        control = parse_xev(xev_path.read_text(errors="replace")[control_start:])
        row["control"] = {"key": "a", "keycode": int(key_a), "events": control,
                           "pass": [e.get("lookup_ascii") for e in control if e.get("type") == "KeyPress"] == ["a"]
                           and [e.get("type") for e in control] == ["KeyPress", "KeyRelease"]}
        if not row["control"]["pass"]:
            row["status"] = "STOP_RECEIVER_CONTROL"
            return row

        if german:
            proc = subprocess.run(["setxkbmap", "-display", name, "-layout", "de"], capture_output=True, text=True, timeout=10)
            row["setxkbmap"] = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
            if proc.returncode:
                row["status"] = "STOP_SETXKBMAP"
                return row
            receiver.sync()
            time.sleep(0.25)
            receiver_events = []
            while receiver.pending_events():
                event = receiver.next_event()
                if event.type == X.MappingNotify:
                    receiver.refresh_keyboard_mapping(event)
                    receiver_events.append("MappingNotify")
            row["receiver_mapping_events"] = receiver_events
            row["after_core_map"] = core_map_snapshot(receiver)
            row["client_core_map_changed"] = row["baseline_core_map"]["sha256"] != row["after_core_map"]["sha256"]
            query = subprocess.run(["setxkbmap", "-display", name, "-query"], capture_output=True, text=True, timeout=10)
            dump = subprocess.run(["xkbcomp", "-xkb", name, "-"], capture_output=True, text=True, timeout=10)
            row["server_query"] = query.stdout
            row["server_query_rc"] = query.returncode
            row["server_xkb_dump"] = dump.stdout
            row["server_xkb_dump_rc"] = dump.returncode
            row["server_xkb_dump_stderr"] = dump.stderr
            row["server_xkb_dump_sha256"] = hashlib.sha256(dump.stdout.encode()).hexdigest()
            row["server_xkb_dump_changed"] = row["baseline_server_xkb_dump"] != dump.stdout
            if query.returncode or "layout:     de" not in query.stdout or dump.returncode or not row["client_core_map_changed"] or not row["server_xkb_dump_changed"]:
                row["status"] = "STOP_LAYOUT_NOT_VERIFIED"
                return row
        else:
            query = subprocess.run(["setxkbmap", "-display", name, "-query"], capture_output=True, text=True, timeout=10)
            dump = subprocess.run(["xkbcomp", "-xkb", name, "-"], capture_output=True, text=True, timeout=10)
            row["server_query"] = query.stdout
            row["server_query_rc"] = query.returncode
            row["server_xkb_dump"] = dump.stdout
            row["server_xkb_dump_rc"] = dump.returncode
            row["server_xkb_dump_stderr"] = dump.stderr
            row["server_xkb_dump_sha256"] = hashlib.sha256(dump.stdout.encode()).hexdigest()
            row["after_core_map"] = row["baseline_core_map"]
            row["client_core_map_changed"] = False
            row["server_xkb_dump_changed"] = row["baseline_server_xkb_dump"] != dump.stdout
            if query.returncode or "layout:     us" not in query.stdout or dump.returncode:
                row["status"] = "STOP_LAYOUT_NOT_VERIFIED"
                return row

        row["xev_events_before_candidate"] = parse_xev(xev_path.read_text(errors="replace"))
        backend = X11Backend(name, {"explicit-receiver": int(win.id)})
        backend.focus("explicit-receiver")
        row["focus_after_backend"] = int(receiver.get_input_focus().focus.id)
        before = backend.emissions
        preflight_size = xev_path.stat().st_size
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "explicit-receiver"}, {"op": "text", "text": UNSUPPORTED}]})
            row["unsupported"] = {"refused": False}
        except X11BackendError as e:
            time.sleep(0.1)
            after_log = xev_path.stat().st_size
            row["unsupported"] = {"refused": True, "error": str(e), "emissions_before_after": [before, backend.emissions],
                                  "receiver_log_bytes_before_after": [preflight_size, after_log]}
        if not row["unsupported"]["refused"] or backend.emissions != before or row["unsupported"].get("receiver_log_bytes_before_after", [1, 0])[0] != row["unsupported"].get("receiver_log_bytes_before_after", [1, 0])[1]:
            row["status"] = "FAIL_UNSUPPORTED_PREFLIGHT"
            return row
        # Drain any layout notifications before capturing the one candidate delivery.
        time.sleep(0.05)
        existing = parse_xev(xev_path.read_text(errors="replace"))
        backend.preflight({"ops": [{"op": "focus", "target": "explicit-receiver"}, {"op": "text", "text": FORMULA}]})
        plan = backend._text_plan(FORMULA)
        plan_keycodes = [[int(backend._keycode(key)) for key in chord] for chord in plan]
        row["candidate_preflight_emissions"] = backend.emissions
        start = xev_path.stat().st_size
        backend.text(FORMULA)
        backend.d.sync()
        time.sleep(0.5)
        delivered = parse_xev(xev_path.read_text(errors="replace")[start:])
        row["events"] = delivered
        row["planned_keys"] = plan
        row["planned_keycodes"] = plan_keycodes
        row["candidate"] = "".join(e["lookup_ascii"] for e in delivered if e["type"] == "KeyPress")
        row["emissions"] = backend.emissions
        row["held_keycodes_after"] = dict(backend.held_keycodes)
        row["status"] = "PASS" if row["candidate"] == FORMULA and len(delivered) == 2 * sum(map(len, plan)) else "FAIL_DELIVERY"
        row["xev_log_sha256"] = hashlib.sha256(xev_path.read_bytes()).hexdigest()
        return row
    except Exception as e:
        row["status"] = "STOP_EXCEPTION"
        row["error"] = f"{type(e).__name__}: {e}"
        return row
    finally:
        if backend:
            backend.close()
        if xev and xev.poll() is None:
            xev.terminate()
            try: xev.wait(timeout=3)
            except subprocess.TimeoutExpired: xev.kill(); xev.wait()
        if 'xev_log' in locals() and not xev_log.closed:
            xev_log.close()
        if receiver:
            receiver.close()
        xvfb.terminate()
        try: xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill(); xvfb.wait()
        row["xvfb_cleanup"] = {"returncode": xvfb.returncode, "reaped": xvfb.poll() is not None}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    freeze_path = Path("research/issue_3784_focused_receiver_v1/ALLOCATION_FREEZE.json")
    freeze = json.loads(freeze_path.read_text())
    freeze_integrity = {p: sha(Path(p)) == expected for p, expected in freeze["files"].items()}
    manifest_path = Path("research/issue_3784_focused_receiver_v1/source_manifest.json")
    manifest = json.loads(manifest_path.read_text())
    integrity = {p: sha(Path(p)) == expected for p, expected in manifest["files"].items()}
    if not all(freeze_integrity.values()) or not all(integrity.values()):
        result = {"allocation": manifest["allocation"], "base_commit": manifest["base_commit"],
                  "container_image": manifest["container_image"], "source_integrity": integrity,
                  "freeze_integrity": freeze_integrity, "rows": [], "decision": "STOP_SOURCE_FREEZE_MISMATCH"}
        write(OUT / "formal_raw.json", result)
        return 0
    rows = [run_case(case, german) for case, german in CASES]
    result = {"allocation": manifest["allocation"], "base_commit": manifest["base_commit"],
              "container_image": manifest["container_image"], "source_integrity": integrity,
              "freeze_integrity": freeze_integrity,
              "rows": rows, "decision": "PASS_FOCUSED_RECEIVER_XKB_DELIVERY_SCOPED" if all(r.get("status") == "PASS" for r in rows) else
              ("STOP_INFRASTRUCTURE" if any(str(r.get("status", "")).startswith("STOP") for r in rows) else "FAIL_XKB_DELIVERY")}
    write(OUT / "formal_raw.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
