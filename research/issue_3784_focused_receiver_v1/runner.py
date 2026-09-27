"""Frozen one-shot receiver and German XKB delivery allocation for Issue #3792."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

ALLOCATION = "issue-3794-german-xkb-receiver-release-audit-formal-01"
BASE = "1355ff9c0e89e04887e7dd3a08aaa93c7b650df0"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "source_manifest.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def fingerprint(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def read_map(disp):
    info = disp.display.info
    rows = disp.get_keyboard_mapping(info.min_keycode, info.max_keycode - info.min_keycode + 1)
    return {"min_keycode": int(info.min_keycode), "max_keycode": int(info.max_keycode),
            "rows": [[int(v) for v in row] for row in rows]}


class XKeyEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong),
                ("send_event", ctypes.c_int), ("display", ctypes.c_void_p),
                ("window", ctypes.c_ulong), ("root", ctypes.c_ulong),
                ("subwindow", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("x", ctypes.c_int), ("y", ctypes.c_int),
                ("x_root", ctypes.c_int), ("y_root", ctypes.c_int),
                ("state", ctypes.c_uint), ("keycode", ctypes.c_uint),
                ("same_screen", ctypes.c_int)]


class Lookup:
    def __init__(self):
        self.lib = ctypes.CDLL("libX11.so.6")
        self.lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.lib.XOpenDisplay.restype = ctypes.c_void_p
        self.lib.XLookupString.argtypes = [ctypes.POINTER(XKeyEvent), ctypes.c_char_p,
                                           ctypes.c_int, ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p]
        self.lib.XLookupString.restype = ctypes.c_int
        self.ptr = self.lib.XOpenDisplay(os.environ["DISPLAY"].encode())
        if not self.ptr:
            raise RuntimeError("STOP_LOOKUP_DISPLAY_OPEN")

    def decode(self, event):
        row = XKeyEvent(event.type, 0, 0, self.ptr, event.window.id, 0, 0, event.time,
                        0, 0, 0, 0, event.state, event.detail, 1)
        buf = ctypes.create_string_buffer(64)
        keysym = ctypes.c_ulong()
        n = self.lib.XLookupString(ctypes.byref(row), buf, len(buf), ctypes.byref(keysym), None)
        return {"keysym": int(keysym.value), "lookup_hex": buf.raw[:n].hex(),
                "lookup_text": buf.raw[:n].decode("ascii", "replace")}

    def close(self):
        self.lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.lib.XCloseDisplay(self.ptr)
        self.ptr = None


def drain(receiver, lookup, timeout=0.25, quiet=0.1):
    events, start, last = [], time.monotonic(), None
    while time.monotonic() - start < timeout:
        receiver.sync()
        while receiver.pending_events():
            event = receiver.next_event()
            if event.type in (X.KeyPress, X.KeyRelease):
                events.append({"type": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                               "keycode": int(event.detail), "state": int(event.state),
                               **lookup.decode(event)})
                last = time.monotonic()
        now = time.monotonic()
        if last is not None and now - last >= quiet:
            break
        if last is None and now - start >= min(quiet, 0.1):
            break
        time.sleep(0.01)
    return events


def command(argv, env, timeout=10):
    p = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    return {"argv": argv, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def capture_state(env, expected_layout):
    query = command(["setxkbmap", "-query"], env)
    dump = command(["xkbcomp", "-xkb", env["DISPLAY"], "-"], env)
    fresh = display.Display(env["DISPLAY"])
    try:
        mapping = read_map(fresh)
    finally:
        fresh.close()
    layout_ok = any(re.fullmatch(r"layout:\s*" + re.escape(expected_layout), line.strip())
                    for line in query["stdout"].splitlines())
    return {"query": query, "dump_returncode": dump["returncode"], "dump": dump["stdout"],
            "dump_sha256": sha(dump["stdout"].encode()), "map": mapping,
            "map_sha256": fingerprint(mapping), "layout_ok": layout_ok}


def process_ticks(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        return None


def stop_process(proc, log):
    pid, ticks = proc.pid, process_ticks(proc.pid)
    if proc.poll() is None:
        proc.terminate()
    try:
        rc = proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait(timeout=4)
    log.flush()
    log.close()
    return {"pid": pid, "start_ticks": ticks, "returncode": rc, "reaped": proc.poll() is not None}


def planned_trace(keycodes):
    result = []
    for chord in keycodes:
        result.extend(("KeyPress", code) for code in chord)
        result.extend(("KeyRelease", code) for code in reversed(chord))
    return result


def run_row(case_id, layout, source, out):
    case = out / "cases" / case_id
    case.mkdir(parents=True, exist_ok=False)
    case_number = len(list((out / "cases").iterdir()))
    env = dict(os.environ)
    env["DISPLAY"] = f":{230 + case_number}"
    os.environ["DISPLAY"] = env["DISPLAY"]
    env["PYTHONPATH"] = str(source)
    xvfb_argv = ["/usr/bin/Xvfb", env["DISPLAY"], "-screen", "0", "800x600x24",
                 "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST", "-noreset"]
    xvfb_log = (case / "xvfb.log").open("wb")
    try:
        xvfb = subprocess.Popen(xvfb_argv, env=env, stdin=subprocess.DEVNULL,
                                stdout=xvfb_log, stderr=subprocess.STDOUT)
    except Exception:
        xvfb_log.close()
        raise
    row = {"case_id": case_id, "layout": layout, "phase": "xvfb_started",
           "xvfb_argv": xvfb_argv, "xvfb_pid": xvfb.pid, "xvfb_start_ticks": process_ticks(xvfb.pid),
           "status": "STOP_SETUP_EXCEPTION"}
    receiver = emitter = backend = None
    lookup = None
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"STOP_XVFB_EXITED:{xvfb.returncode}")
            try:
                receiver = display.Display(env["DISPLAY"])
                break
            except Exception:
                time.sleep(0.05)
        if receiver is None:
            row["status"] = "STOP_XVFB_CONNECT_TIMEOUT"
            return row
        row["extensions"] = {"XKEYBOARD": bool(receiver.query_extension("XKEYBOARD").present),
                              "XTEST": bool(receiver.has_extension("XTEST"))}
        if not all(row["extensions"].values()):
            row["phase"], row["status"] = "server_connected", "STOP_X11_EXTENSION_MISSING"
            return row

        win = receiver.screen().root.create_window(0, 0, 1, 1, 0, X.CopyFromParent,
            X.InputOnly, X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win.map()
        receiver.sync()
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        receiver.sync()
        focused = receiver.get_input_focus().focus
        row["receiver"] = {"window_id": int(win.id), "class": "InputOnly", "mapped": True,
                           "event_mask": X.KeyPressMask | X.KeyReleaseMask,
                           "focus_window_id": int(getattr(focused, "id", 0))}
        row["focus_verified"] = getattr(focused, "id", None) == win.id
        row["phase"] = "receiver_focused"
        if not row["focus_verified"]:
            row["status"] = "STOP_FOCUS_NOT_RECEIVER"
            return row

        lookup = Lookup()
        emitter = display.Display(env["DISPLAY"])
        keycode = int(emitter.keysym_to_keycode(XK.string_to_keysym("a")))
        xtest.fake_input(emitter, X.KeyPress, keycode)
        emitter.sync()
        xtest.fake_input(emitter, X.KeyRelease, keycode)
        emitter.sync()
        control = drain(receiver, lookup, timeout=1.0, quiet=0.1)
        row["receiver_control"] = control
        row["receiver_control_keycode"] = keycode
        row["receiver_control_ok"] = (len(control) == 2
            and (control[0]["type"], control[0]["keycode"], control[0]["lookup_text"])
                == ("KeyPress", keycode, "a")
            and (control[1]["type"], control[1]["keycode"]) == ("KeyRelease", keycode))
        row["phase"] = "receiver_control"
        if not row["receiver_control_ok"]:
            row["status"] = "STOP_RECEIVER_CONTROL"
            return row

        baseline = capture_state(env, "us")
        row["baseline"] = baseline
        (case / "baseline.xkb").write_text(baseline["dump"], encoding="utf-8")
        (case / "baseline.map.json").write_text(json.dumps(baseline["map"], sort_keys=True) + "\n")
        row["phase"] = "baseline_captured"
        if baseline["query"]["returncode"] != 0 or baseline["dump_returncode"] != 0 or not baseline["layout_ok"]:
            row["status"] = "STOP_BASELINE_NOT_US"
            return row

        if layout == "de":
            apply = command(["setxkbmap", "-layout", "de"], env)
        else:
            apply = {"argv": None, "returncode": 0, "stdout": "US control; no layout mutation", "stderr": ""}
        row["apply"] = apply
        row["phase"] = "layout_applied"
        if apply["returncode"] != 0:
            row["status"] = "STOP_LAYOUT_APPLY"
            return row
        time.sleep(0.15)
        after = capture_state(env, layout)
        row["after"] = after
        (case / "after.xkb").write_text(after["dump"], encoding="utf-8")
        (case / "after.map.json").write_text(json.dumps(after["map"], sort_keys=True) + "\n")
        row["map_gate"] = {"layout_ok": after["layout_ok"],
                           "dump_changed": baseline["dump_sha256"] != after["dump_sha256"],
                           "fresh_map_changed": baseline["map_sha256"] != after["map_sha256"]}
        expected_change = layout == "de"
        row["phase"] = "map_captured"
        if (after["query"]["returncode"] != 0 or after["dump_returncode"] != 0 or not after["layout_ok"]
                or row["map_gate"]["dump_changed"] != expected_change
                or row["map_gate"]["fresh_map_changed"] != expected_change):
            row["status"] = "STOP_ACTIVE_MAP_UNCONFIRMED"
            return row

        # Reopen the independent XLookupString display after MappingNotify/map replacement.
        lookup.close()
        lookup = Lookup()
        from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
        backend = X11Backend(env["DISPLAY"], {"receiver": int(win.id)})
        before_unsupported = drain(receiver, lookup, timeout=0.25, quiet=0.1)
        emissions_before = backend.emissions
        unsupported_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"},
                                        {"op": "text", "text": UNSUPPORTED}]})
        except X11BackendError as exc:
            unsupported_error = str(exc)
        after_unsupported = drain(receiver, lookup, timeout=0.25, quiet=0.1)
        row["unsupported_preflight"] = {"error": unsupported_error, "events_before": before_unsupported,
            "events_after": after_unsupported, "emissions_before": emissions_before,
            "emissions_after": backend.emissions,
            "refused_zero_event": bool(unsupported_error and "U+20AC" in unsupported_error
                and not before_unsupported and not after_unsupported and backend.emissions == emissions_before)}
        row["phase"] = "unsupported_preflight"
        if not row["unsupported_preflight"]["refused_zero_event"]:
            row["status"] = "FAIL_UNSUPPORTED_PREFLIGHT"
            return row

        valid_preflight_before = drain(receiver, lookup, timeout=0.25, quiet=0.1)
        emissions_valid_before = backend.emissions
        valid_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"},
                                        {"op": "text", "text": FORMULA}]})
        except X11BackendError as exc:
            valid_error = str(exc)
        valid_preflight_after = drain(receiver, lookup, timeout=0.25, quiet=0.1)
        row["valid_preflight"] = {"error": valid_error, "events_before": valid_preflight_before,
            "events_after": valid_preflight_after, "emissions_before": emissions_valid_before,
            "emissions_after": backend.emissions,
            "zero_emission": valid_error is None and not valid_preflight_before and not valid_preflight_after
                and backend.emissions == emissions_valid_before}
        row["phase"] = "valid_preflight"
        if not row["valid_preflight"]["zero_emission"]:
            row["status"] = "FAIL_VALID_PREFLIGHT"
            return row

        plan = backend._text_plan(FORMULA)
        keycodes = [[int(backend._keycode(key)) for key in chord] for chord in plan]
        row["plan"] = plan
        row["plan_keycodes"] = keycodes
        backend.focus("receiver")
        focus_after_backend = backend.d.get_input_focus().focus
        row["backend_focus_verified"] = getattr(focus_after_backend, "id", None) == win.id
        if not row["backend_focus_verified"]:
            row["status"] = "STOP_BACKEND_FOCUS"
            return row
        before_text = drain(receiver, lookup, timeout=0.25, quiet=0.1)
        if before_text:
            row["unexpected_events_before_text"] = before_text
            row["status"] = "FAIL_PRETEXT_EVENT"
            return row
        emissions_before_text = backend.emissions
        row["phase"] = "candidate_emitted"
        backend.text(FORMULA)
        row["emissions_after_text"] = backend.emissions
        received = drain(receiver, lookup, timeout=3.0, quiet=0.15)
        row["events"] = received
        row["typed"] = "".join(e["lookup_text"] for e in received if e["type"] == "KeyPress")
        row["actual_trace"] = [(e["type"], e["keycode"]) for e in received]
        row["planned_trace"] = planned_trace(keycodes)
        row["emissions_before_text"] = emissions_before_text
        row["release"] = backend.release_all()
        expected_emissions = len(row["planned_trace"])
        row["phase"] = "candidate_complete"
        row["status"] = "PASS_ROW" if (row["typed"] == FORMULA
            and row["actual_trace"] == row["planned_trace"]
            and len(received) == expected_emissions
            and backend.emissions - emissions_before_text == expected_emissions
            and row["release"].get("verified") is True
            and row["release"].get("keys_down") == []
            and row["release"].get("buttons_down") == []) else "FAIL_FORMULA_TRACE_OR_RELEASE"
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}:{exc}"
        row["status"] = "STOP_RUNNER_EXCEPTION"
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception as exc:
                row["backend_close_error"] = repr(exc)
        if lookup is not None:
            try:
                lookup.close()
            except Exception:
                pass
        if emitter is not None:
            try:
                emitter.close()
            except Exception:
                pass
        if receiver is not None:
            try:
                receiver.close()
            except Exception:
                pass
        row["xvfb_process"] = stop_process(xvfb, xvfb_log)
        row["xvfb_log_sha256"] = sha((case / "xvfb.log").read_bytes())
        (case / "row.json").write_text(json.dumps(row, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    return row


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py SOURCE OUTPUT")
    source, out = (Path(value).resolve() for value in sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("base_commit") != BASE or manifest.get("candidate_blob") != "9cae101a219348077668c8fc086acf8e13154afe":
        raise SystemExit("STOP_SOURCE_IDENTITY")
    for relative, expected in manifest["files"].items():
        data = (source / relative).read_bytes()
        if sha(data) != expected["sha256"] or blob(data) != expected["git_blob_sha1"]:
            raise SystemExit(f"STOP_SOURCE_HASH:{relative}")

    rows = []
    for index, (case_id, layout) in enumerate((("de-01", "de"), ("de-02", "de"),
                                                ("de-03", "de"), ("us-control", "us"))):
        try:
            row = run_row(case_id, layout, source, out)
        except Exception as exc:
            case = out / "cases" / case_id
            case.mkdir(parents=True, exist_ok=True)
            row = {"case_id": case_id, "layout": layout, "phase": "xvfb_started",
                   "status": "STOP_RUNNER_SETUP_EXCEPTION", "error": f"{type(exc).__name__}:{exc}",
                   "xvfb_argv": [], "xvfb_process": {"launched": False, "reaped": True,
                                                        "start_ticks": "not_started"}}
            (case / "row.json").write_text(json.dumps(row, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
        rows.append(row)
        if row.get("status", "").startswith("STOP_"):
            break
    disposition = ("STOP_GERMAN_FORMULA_DELIVERY" if any(r["status"].startswith("STOP_") for r in rows)
        else "FAIL_GERMAN_FORMULA_DELIVERY" if any(r["status"].startswith("FAIL_") for r in rows)
        else "PASS_GERMAN_FORMULA_DELIVERY" if len(rows) == 4 and all(r["status"] == "PASS_ROW" for r in rows)
        else "STOP_GERMAN_FORMULA_DELIVERY")
    artifacts = {p.relative_to(out).as_posix(): sha(p.read_bytes())
                 for p in sorted(out.rglob("*")) if p.is_file() and p.name != "raw.json"}
    raw = {"schema": "agent-interface/issue3794-raw-v1", "allocation": ALLOCATION,
        "source_base": BASE, "candidate_blob": manifest["candidate_blob"], "image": IMAGE,
        "platform": "linux/arm64", "container_network": "none", "xvfb_reset_mode": "-noreset",
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "source_manifest_sha256": sha(manifest_bytes), "rows": rows,
        "artifact_sha256": artifacts, "disposition": disposition}
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"disposition": disposition,
        "rows": [{"case_id": r["case_id"], "status": r["status"], "phase": r.get("phase"),
                  "typed": r.get("typed"), "control_ok": r.get("receiver_control_ok")} for r in rows]},
        ensure_ascii=False, sort_keys=True))
    return 0 if disposition == "PASS_GERMAN_FORMULA_DELIVERY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
