"""One-shot explicit X11 receiver experiment for Issue #3784."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

ALLOCATION = "issue3784-explicit-x11-receiver-formal-01"
BASE = "492279afebf6a0bafc31fb1e1558c53805761c0d"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "source_manifest.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def map_data(disp):
    info = disp.display.info
    rows = disp.get_keyboard_mapping(info.min_keycode, info.max_keycode-info.min_keycode+1)
    return {"min_keycode": int(info.min_keycode), "max_keycode": int(info.max_keycode),
            "rows": [[int(v) for v in row] for row in rows]}


def fp(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


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
                                           ctypes.c_int, ctypes.POINTER(ctypes.c_ulong),
                                           ctypes.c_void_p]
        self.lib.XLookupString.restype = ctypes.c_int
        self.ptr = self.lib.XOpenDisplay(os.environ["DISPLAY"].encode())
        if not self.ptr:
            raise RuntimeError("STOP_XLOOKUP_DISPLAY_OPEN")

    def lookup(self, event):
        row = XKeyEvent(event.type, 0, 0, self.ptr, event.window.id, 0, 0,
                        event.time, 0, 0, 0, 0, event.state, event.detail, 1)
        out = ctypes.create_string_buffer(64)
        keysym = ctypes.c_ulong()
        n = self.lib.XLookupString(ctypes.byref(row), out, len(out), ctypes.byref(keysym), None)
        return {"keysym": int(keysym.value), "lookup_hex": out.raw[:n].hex(),
                "lookup_text": out.raw[:n].decode("ascii", "replace")}

    def close(self):
        self.lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.lib.XCloseDisplay(self.ptr)


def drain(receiver, lookup, quiet=0.2, timeout=3.0):
    events, deadline = [], time.monotonic() + timeout
    last = time.monotonic()
    while time.monotonic() < deadline:
        receiver.sync()
        while receiver.pending_events():
            event = receiver.next_event()
            if event.type in (X.KeyPress, X.KeyRelease):
                item = {"type": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                        "keycode": int(event.detail), "state": int(event.state), **lookup.lookup(event)}
                events.append(item)
                last = time.monotonic()
        if events and time.monotonic() - last >= quiet:
            break
        time.sleep(0.01)
    return events


def capture(display_name, layout):
    query = subprocess.run(["setxkbmap", "-query", "-display", os.environ["DISPLAY"]],
                           capture_output=True, text=True)
    dump = subprocess.run(["xkbcomp", "-xkb", os.environ["DISPLAY"], "-"],
                          capture_output=True, text=True)
    fresh = display.Display(display_name)
    try:
        mapping = map_data(fresh)
    finally:
        fresh.close()
    return {"query": {"argv": ["setxkbmap", "-query", "-display", os.environ["DISPLAY"]],
                      "exit": query.returncode, "stdout": query.stdout, "stderr": query.stderr},
            "dump_exit": dump.returncode, "dump": dump.stdout, "dump_sha256": sha(dump.stdout.encode()),
            "map": mapping, "map_sha256": fp(mapping),
            "layout_ok": any(line.strip() == f"layout: {layout}" for line in query.stdout.splitlines())}


def proc_ticks(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        return None


def run_row(case_id, layout, number, source, out):
    global BACKEND_SOURCE
    os.environ["DISPLAY"] = f":{201+number}"
    os.environ["PYTHONPATH"] = str(source)
    case = out / "cases" / case_id
    case.mkdir(parents=True)
    xvfb_log = (case / "xvfb.log").open("wb")
    argv = ["/usr/bin/Xvfb", os.environ["DISPLAY"], "-screen", "0", "800x600x24",
            "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST", "-noreset"]
    xvfb = subprocess.Popen(argv, stdout=xvfb_log, stderr=subprocess.STDOUT)
    row = {"case_id": case_id, "layout": layout, "xvfb_argv": argv, "xvfb_pid": xvfb.pid,
           "xvfb_start_ticks": proc_ticks(xvfb.pid), "status": "STOP_SETUP"}
    receiver = backend = None
    lookup = None
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"STOP_XVFB_EXIT:{xvfb.returncode}")
            try:
                receiver = display.Display(os.environ["DISPLAY"])
                break
            except Exception:
                time.sleep(0.05)
        if receiver is None:
            row["status"] = "STOP_XVFB_CONNECT_TIMEOUT"
            return row
        root = receiver.screen().root
        win = root.create_window(0, 0, 1, 1, 0, X.CopyFromParent, X.InputOnly,
                                 X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win.map(); receiver.sync()
        win.set_input_focus(X.RevertToParent, X.CurrentTime); receiver.sync()
        focus = receiver.get_input_focus().focus
        row["receiver"] = {"window_id": int(win.id), "class": "InputOnly", "mapped": True,
                           "event_mask": X.KeyPressMask | X.KeyReleaseMask,
                           "focus_window_id": int(getattr(focus, "id", 0))}
        row["focus_verified"] = getattr(focus, "id", None) == win.id
        if not row["focus_verified"]:
            row["status"] = "STOP_FOCUS_NOT_RECEIVER"
            return row
        lookup = Lookup()
        keycode = receiver.keysym_to_keycode(XK.string_to_keysym("a"))
        xtest.fake_input(receiver, X.KeyPress, keycode); receiver.sync()
        xtest.fake_input(receiver, X.KeyRelease, keycode); receiver.sync()
        control = drain(receiver, lookup)
        row["receiver_control"] = control
        row["receiver_control_ok"] = [(e["type"], e["keycode"], e["lookup_text"]) for e in control] == [
            ("KeyPress", keycode, "a"), ("KeyRelease", keycode, "")]
        if not row["receiver_control_ok"]:
            row["status"] = "STOP_RECEIVER_CONTROL"
            return row

        before = capture(os.environ["DISPLAY"], "us")
        if not before["layout_ok"] or before["dump_exit"] != 0:
            row["status"] = "STOP_BASELINE"
            row["baseline"] = before
            return row
        if layout == "de":
            apply = subprocess.run(["setxkbmap", "-layout", "de"], capture_output=True, text=True)
            row["apply"] = {"argv": ["setxkbmap", "-layout", "de"], "exit": apply.returncode,
                            "stdout": apply.stdout, "stderr": apply.stderr}
        else:
            row["apply"] = {"argv": None, "exit": 0, "stdout": "US control", "stderr": ""}
        time.sleep(0.2)
        row["baseline"] = before
        row["after"] = capture(os.environ["DISPLAY"], layout)
        row["map_gate"] = {"query_layout": row["after"]["layout_ok"],
                           "dump_changed": before["dump_sha256"] != row["after"]["dump_sha256"],
                           "fresh_map_changed": before["map_sha256"] != row["after"]["map_sha256"]}
        expected_change = layout == "de"
        if (row["after"]["dump_exit"] != 0 or not row["map_gate"]["query_layout"]
                or row["map_gate"]["dump_changed"] != expected_change
                or row["map_gate"]["fresh_map_changed"] != expected_change
                or row["apply"]["exit"] != 0):
            row["status"] = "STOP_ACTIVE_MAP_UNCONFIRMED"
            return row

        # Re-read after MappingNotify through a distinct Xlib connection.
        refreshed_lookup = Lookup()
        lookup.close()
        lookup = refreshed_lookup
        backend_module = __import__("runtime.backends.x11_v1.backend", fromlist=["X11Backend"])
        Backend = backend_module.X11Backend
        backend = Backend(os.environ["DISPLAY"], {"receiver": int(win.id)})
        unsupported_before = drain(receiver, lookup, quiet=0.1, timeout=0.3)
        unsupported_error = None
        try:
            backend._text_plan(UNSUPPORTED)
        except Exception as error:
            unsupported_error = str(error)
        unsupported_after = drain(receiver, lookup, quiet=0.1, timeout=0.3)
        row["unsupported"] = {"error": unsupported_error, "before_events": unsupported_before,
                              "after_events": unsupported_after, "emissions": backend.emissions,
                              "refused_zero_event": unsupported_error is not None and not unsupported_before
                                  and not unsupported_after and backend.emissions == 0}
        if not row["unsupported"]["refused_zero_event"]:
            row["status"] = "FAIL_UNSUPPORTED_NOT_FAIL_CLOSED"
            return row
        plan = backend._text_plan(FORMULA)
        row["plan"] = plan
        row["plan_keycodes"] = [[backend._keycode(key) for key in chord] for chord in plan]
        backend.focus("receiver")
        backend.text(FORMULA)
        receiver.sync(); events = drain(receiver, lookup)
        row["events"] = events
        row["typed"] = "".join(e["lookup_text"] for e in events if e["type"] == "KeyPress")
        row["emissions"] = backend.emissions
        row["release"] = backend.release_all()
        expected_count = sum(2*len(chord) for chord in row["plan_keycodes"])
        row["status"] = "PASS_ROW" if row["typed"] == FORMULA and len(events) == expected_count else "FAIL_DELIVERY"
        return row
    except Exception as error:
        row["status"] = "STOP_EXCEPTION"
        row["error"] = repr(error)
        return row
    finally:
        if backend is not None:
            try: backend.close()
            except Exception: pass
        if lookup is not None:
            try: lookup.close()
            except Exception: pass
        if receiver is not None:
            try: receiver.close()
            except Exception: pass
        if xvfb.poll() is None:
            xvfb.terminate()
        try: rc = xvfb.wait(timeout=4)
        except subprocess.TimeoutExpired:
            xvfb.kill(); rc = xvfb.wait(timeout=4)
        row["xvfb_cleanup"] = {"returncode": rc, "reaped": xvfb.poll() is not None}
        xvfb_log.close()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py SOURCE OUTPUT")
    source, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("base_commit") != BASE:
        raise SystemExit("STOP_SOURCE_BASE_MISMATCH")
    for path, expected in manifest["files"].items():
        data = (source / path).read_bytes()
        if sha(data) != expected["sha256"] or blob(data) != expected["git_blob_sha1"]:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH:{path}")
    rows = [run_row("de-01", "de", 0, source, out), run_row("de-02", "de", 1, source, out),
            run_row("de-03", "de", 2, source, out), run_row("us-control", "us", 3, source, out)]
    for row in rows:
        case = out / "cases" / row["case_id"]
        case.mkdir(parents=True, exist_ok=True)
        (case / "row.json").write_text(json.dumps(row, sort_keys=True, indent=2, ensure_ascii=False)+"\n")
        for phase in ("baseline", "after"):
            state = row.get(phase)
            if state:
                (case / f"{phase}.xkb").write_text(state["dump"])
                (case / f"{phase}.map.json").write_text(json.dumps(state["map"], sort_keys=True)+"\n")
    artifacts = {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in sorted(out.rglob("*"))
                 if p.is_file() and p.name != "raw.json"}
    disposition = ("PASS_GERMAN_FORMULA_DELIVERY" if all(r["status"] == "PASS_ROW" for r in rows)
                   else "FAIL_GERMAN_FORMULA_DELIVERY" if any(r["status"].startswith("FAIL_") for r in rows)
                   else "STOP_GERMAN_FORMULA_DELIVERY")
    raw = {"schema": "agent-interface/issue3784-raw-v1", "allocation": ALLOCATION,
           "base_commit": BASE, "image": IMAGE, "runner_sha256": sha(Path(__file__).read_bytes()),
           "source_manifest_sha256": sha(manifest_bytes), "artifact_sha256": artifacts,
           "rows": rows, "disposition": disposition}
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"disposition": disposition, "rows": [(r["case_id"], r["status"], r.get("typed"),
          len(r.get("events", [])), r.get("receiver_control_ok")) for r in rows]}, ensure_ascii=False))
    return 0 if disposition.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
