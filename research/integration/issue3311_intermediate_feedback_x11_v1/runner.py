"""One-shot live X11/Chromium compiled-continuation mechanics allocation."""
from __future__ import annotations

import hashlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time
import urllib.parse

from compiled_gui_interface_v1 import run
from Xlib import X, display as xdisplay


ROOT = Path("/out")
ART = ROOT / "observations"
TOKEN = "AI-3311-UNIT-01"
ALLOCATION_ID = os.environ.get(
    "ISSUE3311_ALLOCATION_ID",
    "ISSUE3311-LOCAL-X11-INTERMEDIATE-FEEDBACK-20260928-01")
DISPLAY = ":97"
PORT = 8765
SURFACE = "issue3311-chromium-unit-v1"
events = []
submissions = []
lock = threading.Lock()


PAGE = b"""<!doctype html><meta charset=utf-8><title>EDITING</title>
<style>body{font:32px sans-serif;background:#eef}button{position:fixed;left:100px;top:100px;width:240px;height:80px;font-size:28px}</style>
<h1>One-step integration fixture</h1>
<button id=save>Save</button><button id=confirm hidden>Confirm</button>
<script>
const saveButton=document.getElementById('save'),confirmButton=document.getElementById('confirm');
const post=async(path,obj)=>{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});if(!r.ok)throw Error('fixture POST failed')};
saveButton.onclick=async()=>{await post('/stage',{stage:'CONFIRMING'});document.title='CONFIRMING';saveButton.hidden=true;confirmButton.hidden=false};
confirmButton.onclick=async()=>{await post('/submit',{token:'AI-3311-UNIT-01'});document.title='SAVED';confirmButton.hidden=true;document.body.insertAdjacentHTML('beforeend','<p id=done>Saved</p>')};
</script>"""


def server_snapshot():
    with lock:
        return {"events": json.loads(json.dumps(events)),
                "submissions": json.loads(json.dumps(submissions))}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/":
            body, kind = PAGE, "text/html; charset=utf-8"
        elif self.path == "/oracle":
            body = json.dumps(server_snapshot(), sort_keys=True,
                              separators=(",", ":")).encode()
            kind = "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n)
        try:
            value = json.loads(raw)
        except Exception:
            self.send_error(400)
            return
        with lock:
            if self.path == "/stage" and value == {"stage": "CONFIRMING"}:
                events.append({"event": "stage", "stage": "CONFIRMING", "raw": raw.decode()})
            elif self.path == "/submit" and value == {"token": TOKEN}:
                submissions.append({"token": value["token"], "raw": raw.decode()})
                events.append({"event": "stage", "stage": "SAVED"})
            else:
                self.send_error(400)
                return
        self.send_response(204)
        self.end_headers()


def xdotool(*args, check=True):
    return subprocess.run(["xdotool", *map(str, args)], check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def window_title(window):
    return xdotool("getwindowname", window).stdout.strip()


def oracle():
    import urllib.request
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/oracle", timeout=2) as response:
        return json.loads(response.read())


def wait_title(window, expected, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if window_title(window).split(" - Chromium")[0] == expected:
            return True
        time.sleep(0.02)
    return False


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(exist_ok=True)
    os.environ["DISPLAY"] = DISPLAY
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x800x24",
                             "-nolisten", "tcp"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    chrome = None
    audit_log = []
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not Path("/tmp/.X11-unix/X97").exists():
            if xvfb.poll() is not None:
                raise RuntimeError("XVFB_EXITED_BEFORE_READY")
            time.sleep(0.02)
        if not Path("/tmp/.X11-unix/X97").exists():
            raise RuntimeError("XVFB_READY_TIMEOUT")
        chrome = subprocess.Popen([
            "chromium", "--no-sandbox", "--disable-dev-shm-usage", "--no-first-run",
            "--no-default-browser-check", "--disable-background-networking",
            "--disable-extensions", "--disable-gpu", "--kiosk", "--window-size=1280,800",
            "--user-data-dir=/tmp/issue3311-chrome", f"http://127.0.0.1:{PORT}/"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 20
        window = None
        while time.monotonic() < deadline:
            ids = xdotool("search", "--onlyvisible", "--class", "chromium", check=False).stdout.split()
            if ids:
                window = int(ids[-1])
                xdotool("windowfocus", "--sync", window, check=False)
                if wait_title(window, "EDITING", timeout=0.1):
                    break
            time.sleep(0.05)
        if window is None or not wait_title(window, "EDITING", timeout=1):
            raise RuntimeError("CHROMIUM_EDITING_WINDOW_NOT_READY")
        wid = xdotool("getwindowpid", window).stdout.strip()

        interface = {
            "format": "compiled-gui-interface-v1", "interface_id": "issue3311-unit-v1",
            "session_scope": "single-local-x11-fixture", "surface": SURFACE,
            "predicates": ["page_state", "save_target_present", "confirm_target_present"],
            "symbols": {
                "save": {"kind": "target_reference", "target_reference": f"window:{window}/#save",
                         "identity_predicate": "save_target_present",
                         "dependencies": ["page_state", "save_target_present"]},
                "confirm": {"kind": "target_reference", "target_reference": f"window:{window}/#confirm",
                             "identity_predicate": "confirm_target_present",
                             "dependencies": ["page_state", "confirm_target_present"]}},
            "actions": {
                "request_save": {"target_symbol": "save", "operation": "click_save",
                                 "expected_effect": {"page_state": "CONFIRMING"}},
                "confirm_save": {"target_symbol": "confirm", "operation": "click_confirm",
                                 "expected_effect": {"page_state": "SAVED"}}},
            "method": {"name": "save_confirm_once", "version": "1",
                       "initial_state": "editing", "max_transitions": 2,
                       "max_runtime_ms": 15000,
                       "states": {
                           "editing": {"branches": [{"when": {"page_state": "EDITING",
                               "save_target_present": True}, "outcome": "action",
                               "action": "request_save", "next_state": "confirming", "reason": None}]},
                           "confirming": {"branches": [{"when": {"page_state": "CONFIRMING",
                               "confirm_target_present": True}, "outcome": "action",
                               "action": "confirm_save", "next_state": "done", "reason": None}]},
                           "done": {"branches": [{"when": {"page_state": "SAVED"},
                               "outcome": "complete", "action": None, "next_state": None,
                               "reason": None}]}}}}

        seq = 0
        admits = []
        terminals = []
        effects = []

        def observe(_payload):
            nonlocal seq
            seq += 1
            title = window_title(window).split(" - Chromium")[0]
            if title not in {"EDITING", "CONFIRMING", "SAVED"}:
                state = "unknown"
            else:
                state = title
            screenshot = ART / f"observation-{seq:02d}.png"
            subprocess.run(["import", "-window", str(window), str(screenshot)], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
            row = {"sequence": seq, "captured_ns": time.monotonic_ns(), "surface": SURFACE,
                   "predicates": {"page_state": state,
                       "save_target_present": state == "EDITING",
                       "confirm_target_present": state == "CONFIRMING"},
                   "evidence_ref": screenshot.name, "evidence_digest": digest}
            audit_log.append({"event": "observation", "window_id": window, "window_pid": wid,
                              "window_title": title, "observation": row})
            return row

        def admit(payload):
            title = window_title(window).split(" - Chromium")[0]
            active = xdotool("getactivewindow", check=False).stdout.strip()
            action = payload["action"]
            required_state = "EDITING" if action == "request_save" else "CONFIRMING"
            symbol = payload["symbol"]["target_reference"]
            eligible = (active == str(window) and title == required_state and
                        symbol == f"window:{window}/#" + ("save" if action == "request_save" else "confirm"))
            row = {"eligible": eligible, "status": "revalidated" if eligible else "stale",
                   "authorization": f"local-expiring-{seq}" if eligible else None,
                   "expected_sequence": payload["observation"]["sequence"],
                   "valid_until_ns": time.monotonic_ns() + 2_000_000_000 if eligible else 0}
            admits.append({"action": action, "title": title, "active_window": active,
                           "symbol": symbol, "result": row})
            return row

        def execute(payload):
            action = payload["action"]
            before = window_title(window).split(" - Chromium")[0]
            target = "save" if action == "request_save" else "confirm"
            click = subprocess.run(["xdotool", "mousemove", "160", "140", "click", "--clearmodifiers", "1"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            release = subprocess.run(["xdotool", "mouseup", "1"], check=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            pointer_mask = xdisplay.Display().screen().root.query_pointer().mask
            button_up = not bool(pointer_mask & X.Button1Mask)
            expected = "CONFIRMING" if action == "request_save" else "SAVED"
            observed = wait_title(window, expected, timeout=4)
            row = {"status": "completed" if click.returncode == 0 and observed else "execution_failed",
                   "action_id": f"x11-click-{len(terminals)+1}",
                   "effect_ref": f"fixture-oracle-{len(terminals)+1}",
                   "release": {"verified": click.returncode == 0 and release.returncode == 0 and button_up,
                               "keys_down": [], "buttons_down": []}}
            terminals.append({"action": action, "target": target, "before_title": before,
                              "click_exit": click.returncode, "mouseup_exit": release.returncode,
                              "x11_button1_mask": bool(pointer_mask & X.Button1Mask),
                              "expected_title": expected, "title_observed": observed, "terminal": row})
            return row

        def verify_effect(payload):
            snapshot = oracle()
            expected = payload["expected_effect"]["page_state"]
            actual = snapshot["events"][-1].get("stage") if snapshot["events"] else None
            if expected == "SAVED" and snapshot["submissions"]:
                actual = "SAVED"
            passed = actual == expected
            row = {"status": "succeeded" if passed else "failed",
                   "evidence_ref": f"server-oracle-stage-{len(effects)+1}"}
            effects.append({"expected": expected, "oracle": snapshot, "result": row})
            return row

        def journal(event):
            audit_log.append(event)

        result = run(interface, {"observe": observe, "admit": admit, "execute": execute,
                     "verify_effect": verify_effect, "cancelled": lambda: False,
                     "journal": journal})
        final_oracle = oracle()
        out = {"schema": "issue3311_intermediate_feedback_x11_v1", "allocation_id": ALLOCATION_ID,
               "container_image_id": "sha256:dff1c7b56201b4c299883655d98aee3b3f8d7c0c6dd1e4ad6320b942fb5d17fb",
               "runtime_source_sha256": hashlib.sha256(Path("/src/research/live_control/compiled_gui_interface_v1.py").read_bytes()).hexdigest(),
               "page_sha256": hashlib.sha256(PAGE).hexdigest(), "window_id": window, "window_pid": int(wid),
               "runtime_receipt": result, "observations": [x for x in audit_log if x.get("event") == "observation"],
               "admissions": admits, "terminals": terminals, "independent_effect_checks": effects,
               "server_oracle": final_oracle, "runner_exit": 0}
        (ROOT / "RUNNER_RESULT.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
        (ROOT / "RUNTIME_JOURNAL.jsonl").write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in audit_log))
        return 0
    except Exception as error:
        out = {"schema": "issue3311_intermediate_feedback_x11_v1", "allocation_id": ALLOCATION_ID,
               "runner_exit": 1, "error": repr(error), "events": audit_log,
               "server_oracle": server_snapshot()}
        (ROOT / "RUNNER_RESULT.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
        return 1
    finally:
        if chrome is not None and chrome.poll() is None:
            chrome.send_signal(signal.SIGTERM)
            try:
                chrome.wait(timeout=3)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait()
        server.shutdown()
        server.server_close()
        xvfb.terminate()
        try:
            xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            xvfb.wait()


if __name__ == "__main__":
    raise SystemExit(main())
