"""One-task local Edge/OCR/compiled-GUI/caller integration smoke on Windows."""

import hashlib
import json
import math
import os
import platform
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import unittest
from unittest.mock import patch

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT,
    compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)
from research.live_control.windows_ocr_observer_v1 import (
    WindowsOcrObserver,
    exact_token_state,
)
from runtime.core_v1.compiled_gui import validate


HERE = Path(__file__).resolve().parent
NODE_CDP = r'''const fs=require('fs');const [pageWs,op,arg]=process.argv.slice(1);let seq=0;const pending=new Map();const ws=new WebSocket(pageWs);function rpc(method,params={}){const id=++seq;return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result||{});}});ws.addEventListener('open',async()=>{try{await rpc('Page.enable');if(op==='capture'){const s=await rpc('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(arg,Buffer.from(s.data,'base64'));}else if(op==='click'){let done;const loaded=new Promise(r=>done=r);const f=e=>{if(JSON.parse(e.data).method==='Page.loadEventFired'){ws.removeEventListener('message',f);done();}};ws.addEventListener('message',f);const [x,y]=arg.split(',').map(Number);await rpc('Input.dispatchMouseEvent',{type:'mouseMoved',x,y,button:'none'});await rpc('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',buttons:1,clickCount:1});await rpc('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',buttons:0,clickCount:1});await Promise.race([loaded,new Promise(r=>setTimeout(r,3000))]);}else if(op!=='noop'){throw Error('unsupported CDP operation');}ws.close();process.exit(0);}catch(e){console.error(String(e));process.exit(2);}});'''
BROWSER_CLOSE = r'''const w=new WebSocket(process.argv[1]);let done=false;w.addEventListener('open',()=>w.send(JSON.stringify({id:1,method:'Browser.close'})));w.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id===1){done=true;process.exit(m.error?1:0);}});w.addEventListener('close',()=>process.exit(0));w.addEventListener('error',()=>process.exit(done?0:1));setTimeout(()=>process.exit(2),5000);'''


def _cleanup_edge_test_profile(path, *, attempts=16, delay_seconds=0.25):
    """Remove only this test's temporary Edge profile, retrying transient locks."""
    if type(attempts) is not int or attempts < 1:
        raise ValueError("positive cleanup attempt limit required")
    if (type(delay_seconds) not in (int, float) or delay_seconds < 0 or
            not math.isfinite(delay_seconds)):
        raise ValueError("finite nonnegative cleanup delay required")
    candidate = Path(path)
    if not candidate.exists():
        return
    if candidate.is_symlink():
        raise ValueError("cleanup target cannot be a symlink")
    root = candidate.resolve(strict=True)
    if (root.parent != HERE.resolve(strict=True) or
            not root.name.startswith("interface-edge-submit-") or
            not root.is_dir() or root.is_symlink()):
        raise ValueError("cleanup target is not a test-owned Edge directory")

    last_error = None
    for attempt in range(attempts):
        try:
            shutil.rmtree(root)
            return
        except FileNotFoundError:
            if not root.exists():
                return
            last_error = PermissionError("Edge profile changed during cleanup")
        except PermissionError as error:
            last_error = error
        if attempt + 1 < attempts:
            time.sleep(delay_seconds)
    raise PermissionError(
        f"Edge profile remained locked after {attempts} cleanup attempts: {root}") from last_error


@unittest.skipUnless(os.name == "nt", "local Edge integration requires Windows")
class CompiledGuiEdgeIntegrationTests(unittest.TestCase):
    def test_profile_cleanup_retries_transient_lock_and_rejects_other_roots(self):
        root = Path(tempfile.mkdtemp(
            prefix="interface-edge-submit-cleanup-test-", dir=str(HERE)))
        (root / "fixture.txt").write_text("test-owned", encoding="utf-8")
        real_rmtree = shutil.rmtree
        calls = []

        def fail_once_then_remove(path):
            calls.append(path)
            if len(calls) == 1:
                raise PermissionError("synthetic transient lock")
            return real_rmtree(path)

        with patch.object(shutil, "rmtree", side_effect=fail_once_then_remove), \
                patch("research.live_control.test_windows_compiled_gui_edge_live_v1.time.sleep"):
            _cleanup_edge_test_profile(root)
        self.assertEqual(len(calls), 2)
        self.assertFalse(root.exists())
        with self.assertRaisesRegex(ValueError, "not a test-owned"):
            _cleanup_edge_test_profile(HERE)

    def test_exact_ocr_gates_submit_and_caller_verifies_server_effect(self):
        edge = Path(os.environ.get("ProgramFiles(x86)",
                                   r"C:\Program Files (x86)")) / "Microsoft" / \
            "Edge" / "Application" / "msedge.exe"
        node = shutil.which("node.exe") or shutil.which("node")
        if not edge.is_file() or node is None:
            self.skipTest("Edge and Node.js are required for this integration test")

        token = "t991025-2"
        records = []
        record_lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):
                body = ("<!doctype html><meta charset='utf-8'>"
                        "<style>body{margin:0;font:16px Arial}"
                        "input{position:absolute;left:150px;top:100px;"
                        "width:220px;height:30px;font:16px Arial}"
                        "button{position:absolute;left:400px;top:100px;"
                        "width:70px;height:30px}</style>"
                        f"<form method='post' action='/submit'>"
                        f"<label>Value <input name='value' value='{token}'></label>"
                        "<button type='submit'>Save</button></form>").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length)
                submitted = urllib.parse.parse_qs(raw_body.decode("utf-8", "replace"),
                                                   keep_blank_values=True)
                row = {"submitted_values": submitted.get("value", []),
                       "exact": submitted == {"value": [token]},
                       "raw_body_utf8": raw_body.decode("utf-8", "strict"),
                       "received_ns": time.perf_counter_ns(),
                       "path": self.path}
                with record_lock:
                    records.append(row)
                body = (b"<!doctype html><h1>AI INTEGRATED SAVED</h1>"
                        if row["exact"] else b"<!doctype html><h1>REJECTED</h1>")
                self.send_response(200 if row["exact"] else 422)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        packet_root = HERE.parents[1] / "research/integration/issue57_chromium_v3_edge_r04"
        evidence_root = packet_root / "raw"
        worktree_status_before_capture = subprocess.run(
            ["git", "status", "--porcelain"], cwd=HERE.parents[1],
            capture_output=True, text=True, check=True).stdout.strip()
        if worktree_status_before_capture:
            raise RuntimeError("frozen experiment requires a clean worktree")
        evidence_sources = [
            Path(__file__).resolve(),
            HERE / "adaptive_acquisition_caller_v3.py",
            HERE / "integrated_efficiency_compiled_execution_v2.py",
            HERE / "integrated_efficiency_compiled_adapter_v2.py",
            HERE / "windows_ocr_observer_v1.py",
            HERE / "windows_ocr_worker_v1.ps1",
            Path(__file__).resolve().parents[2] / "runtime/core_v1/compiled_gui.py",
            packet_root / "PROTOCOL.md",
            packet_root / "audit_saved_run.py",
        ]
        missing_sources = [str(path) for path in evidence_sources if not path.is_file()]
        if missing_sources:
            raise FileNotFoundError("frozen evidence sources missing: " +
                                    ", ".join(missing_sources))
        source_hashes = {str(path.relative_to(HERE.parents[1])):
                         hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in evidence_sources}
        repository_head = subprocess.run(["git", "rev-parse", "HEAD"],
            cwd=HERE.parents[1], capture_output=True, text=True,
            check=True).stdout.strip()
        evidence_root.mkdir(parents=True, exist_ok=False)
        evidence_conditions = {"scope": "one local headless Edge form submission",
            "task_token": "t991025-1", "initial_field_state": "prepopulated",
            "caller": "adaptive_acquisition_caller_v3",
            "compiled_core": "runtime.core_v1.compiled_gui",
            "provider": "offline-test-double; no network model call",
            "independent_scorer": "local HTTP server exact POST body",
            "headless": True, "task_family": "private localhost HTML form",
            "target_generation_mutation": "not tested",
            "two_action_entry_and_submit": "not tested; token prepopulated",
            "repository_head": repository_head,
            "repository_clean_before_run": not worktree_status_before_capture,
            "worktree_status_before_capture": worktree_status_before_capture,
            "source_hashes_sha256": source_hashes,
            "python": platform.python_version(), "platform": platform.platform()}
        (evidence_root / "conditions.json").write_text(
            json.dumps(evidence_conditions, indent=2) + "\n", encoding="utf-8")

        interface = compile_form_method(
            interface_id="edge-ocr-submit-v1",
            session_scope="edge-ocr-session-v1", surface="form",
            field_handle="field", submit_handle="submit",
            method_contract=EXPECTED_METHOD_CONTRACT)
        interface["method"]["initial_state"] = "verify_value"
        interface = validate(interface)
        observation_rows = []
        server = None
        server_thread = None

        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            origin = f"http://127.0.0.1:{server.server_port}/form"
            with tempfile.TemporaryDirectory(
                    prefix="interface-edge-submit-",
                    dir=str(Path(__file__).resolve().parent),
                    ignore_cleanup_errors=True) as directory:
                root = Path(directory)
                profile = root / "profile"
                image = root / "frame.png"
                launcher = subprocess.Popen([
                    str(edge), "--headless=new", "--disable-gpu", "--no-first-run",
                    "--no-default-browser-check", "--remote-debugging-address=127.0.0.1",
                    "--remote-debugging-port=0", "--remote-allow-origins=*",
                    f"--user-data-dir={profile}", "about:blank"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    port_file = profile / "DevToolsActivePort"
                    deadline = time.monotonic() + 12
                    version = None
                    while time.monotonic() < deadline:
                        if port_file.exists():
                            try:
                                port = int(port_file.read_text(
                                    encoding="ascii").splitlines()[0])
                                version = json.load(urllib.request.urlopen(
                                    f"http://127.0.0.1:{port}/json/version",
                                    timeout=1))
                                break
                            except (OSError, ValueError, json.JSONDecodeError):
                                pass
                        time.sleep(0.1)
                    self.assertIsNotNone(version, "isolated Edge did not expose DevTools")
                    targets = json.load(urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/json/list", timeout=2))
                    page_ws = next(row["webSocketDebuggerUrl"] for row in targets
                                   if row.get("type") == "page")

                    setup = r'''const [pageWs,browserWs,url]=process.argv.slice(1);let id=0;const w=new WebSocket(pageWs);const pending=new Map();function rpc(method,params={}){const n=++id;return new Promise((resolve,reject)=>{pending.set(n,{resolve,reject});w.send(JSON.stringify({id:n,method,params}));});}w.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result||{});}});w.addEventListener('open',async()=>{try{await rpc('Page.enable');await rpc('Emulation.setDeviceMetricsOverride',{width:756,height:488,deviceScaleFactor:1,mobile:false});let done;const loaded=new Promise(r=>done=r);const f=e=>{if(JSON.parse(e.data).method==='Page.loadEventFired'){w.removeEventListener('message',f);done();}};w.addEventListener('message',f);await rpc('Page.navigate',{url});await Promise.race([loaded,new Promise(r=>setTimeout(r,5000))]);w.close();process.exit(0);}catch(e){console.error(String(e));process.exit(2);}});'''
                    loaded = subprocess.run([
                        node, "-e", setup, page_ws, version["webSocketDebuggerUrl"],
                        origin], capture_output=True, text=True, timeout=10)
                    self.assertEqual(loaded.returncode, 0, loaded.stderr)

                    with WindowsOcrObserver(timeout_seconds=12) as observer:
                        previous_frame = None
                        sequence = 0
                        dispatched = []
                        receipts = []
                        ocr_elapsed_ns = []
                        observed_value_states = []

                        def cdp(operation, argument=""):
                            reply = subprocess.run([
                                node, "-e", NODE_CDP, page_ws, operation, argument],
                                capture_output=True, text=True, timeout=8)
                            if reply.returncode != 0:
                                raise RuntimeError("Edge CDP operation failed: " +
                                                   reply.stderr[-300:])

                        def observe(_payload):
                            nonlocal previous_frame, sequence
                            sequence += 1
                            cdp("capture", str(image))
                            raw = image.read_bytes()
                            digest = hashlib.sha256(raw).hexdigest()
                            capture_path = evidence_root / f"frame-{sequence}.png"
                            capture_path.write_bytes(raw)
                            ocr = observer.recognize(
                                image, region=(125, 80, 355, 70), scale=2)
                            ocr_elapsed_ns.append(ocr["elapsed_ns"])
                            value_state = exact_token_state(ocr["text"], token)
                            observed_value_states.append(value_state)
                            observation_rows.append({
                                "sequence": sequence,
                                "runtime_state": _payload["state"],
                                "state": value_state,
                                "predicates": {
                                    "field_pixels_changed": changed,
                                    "field_value_matches_task": value_state,
                                    "field_target_present": True,
                                    "submit_target_present": True,
                                    "submission_pixels_changed": changed,
                                },
                                "capture_file": capture_path.name,
                                "capture_sha256": digest,
                                "ocr_text": ocr["text"],
                                "ocr_elapsed_ns": ocr["elapsed_ns"]})
                            changed = previous_frame is not None and digest != previous_frame
                            previous_frame = digest
                            return {"sequence": sequence,
                                    "captured_ns": time.perf_counter_ns(),
                                    "surface": "form",
                                    "predicates": {
                                        "field_pixels_changed": changed,
                                        "field_value_matches_task": value_state,
                                        "field_target_present": True,
                                        "submit_target_present": True,
                                        "submission_pixels_changed": changed,
                                    },
                                    "evidence_ref": f"edge-frame-{sequence}",
                                    "evidence_digest": digest}

                        def admit(payload):
                            return {"eligible": True, "status": "revalidated",
                                    "authorization": "one-use-edge-submit",
                                    "expected_sequence": payload["observation"]["sequence"],
                                    "valid_until_ns": time.perf_counter_ns() +
                                                      2_000_000_000}

                        def execute(payload):
                            if payload["operation"] != "activate_submit":
                                raise RuntimeError("unexpected compiled operation")
                            cdp("click", "435,115")
                            dispatched.append(payload["operation"])
                            return {"status": "completed", "action_id": "edge-submit-1",
                                    "effect_ref": "local-post-1",
                                    "release": {"verified": True, "keys_down": [],
                                                "buttons_down": []}}

                        def verify_effect(_payload):
                            with record_lock:
                                exact = (len(records) == 1 and
                                         records[0]["exact"] is True)
                            return {"status": "succeeded" if exact else "failed",
                                    "evidence_ref": "independent-http-post-1"}

                        caller_adapters = {
                            "observe_source": lambda _payload: {"source": "edge-frame-1"},
                            "acquire_anchor": lambda _payload: {"source": "edge-frame-1"},
                            "anchor_model": lambda _payload: {
                                "call_id": "offline-target-contract",
                                "output": {"status": "target_reference",
                                           "target": {"interface": interface}},
                                "usage": {"input_tokens": 0, "output_tokens": 0,
                                          "cached_input_tokens": 0,
                                          "cache_write_input_tokens": 0,
                                          "reasoning_output_tokens": 0},
                                "requested_model": "offline-test-double",
                                "requested_effort": "medium", "cost": None,
                                "visible_images_submitted": 1, "wait_ns": 0},
                            "final_revalidate": lambda _payload: {
                                "status": "revalidated"},
                            "verify_effect": verify_effect,
                        }
                        spec = {"target": "submit exact visible form token",
                                "route": "cold", "coarse_origin": "caller_provided",
                                "provided_coarse": {"source": "edge-frame-1"},
                                "cached_target": None, "repair_on": [],
                                "local_repair_on": [],
                                "session_id": "edge-ocr-session-v1"}
                        result = run_compiled_interface_in_caller(
                            spec, caller_adapters,
                            lambda payload: payload["target"]["interface"],
                            {"observe": observe, "admit": admit, "execute": execute,
                             "verify_effect": lambda payload: {
                                 "status": "succeeded",
                                 "evidence_ref": payload["observation"]["evidence_ref"]},
                             "cancelled": lambda: False},
                            on_receipt=receipts.append,
                            id_factory=lambda: "offline-target-contract")

                    self.assertEqual(result["outcome"], "TASK_SUCCEEDED", result)
                    self.assertEqual(result["task_effect"], "succeeded")
                    self.assertEqual(result["delivery"], "confirmed")
                    self.assertEqual(result["input_authority"],
                                     "consumed_by_recorded_execute_stage")
                    self.assertEqual(dispatched, ["activate_submit"])
                    self.assertTrue(observed_value_states[0])
                    self.assertTrue(all(value > 0 for value in ocr_elapsed_ns))
                    self.assertEqual(len(records), 1)
                    self.assertTrue(records[0]["exact"])
                    self.assertEqual(receipts[0]["outcome"], "TASK_SUCCEEDED")
                    self.assertEqual(receipts[0]["completed_transitions"], 1)
                    self.assertTrue(receipts[0]["transitions"][0]["release_verified"])
                    self.assertEqual(receipts[0]["frontier_model_resumptions"], 0)
                    (evidence_root / "run.json").write_text(json.dumps({
                        "outcome": result["outcome"],
                        "task_effect": result["task_effect"],
                        "delivery": result["delivery"],
                        "accounting": result["accounting"],
                        "attempt_ledger": result["attempt_ledger"],
                        "model_call_ledger": result["model_call_ledger"],
                        "execution_progress": result["execution_progress"],
                        "effect_receipt": result["effect_receipt"],
                        "compiled_execution_receipt":
                            result["compiled_execution_receipt"],
                        "ocr_observations": observation_rows,
                        "ocr_elapsed_ns": ocr_elapsed_ns,
                        "value_states": observed_value_states,
                        "dispatched_operations": dispatched,
                        "server_posts": records,
                        "edge_version": version,
                        "python": platform.python_version(),
                    }, indent=2) + "\n", encoding="utf-8")
                finally:
                    close = subprocess.run([
                        node, "-e", BROWSER_CLOSE,
                        version["webSocketDebuggerUrl"] if version else ""],
                        capture_output=True, text=True, timeout=4)
                    if version is not None:
                        shutdown_deadline = time.monotonic() + 5
                        while time.monotonic() < shutdown_deadline:
                            try:
                                urllib.request.urlopen(
                                    f"http://127.0.0.1:{port}/json/version",
                                    timeout=0.25).close()
                            except OSError:
                                break
                            time.sleep(0.1)
                        time.sleep(0.5)
                    if launcher.poll() is None:
                        taskkill = shutil.which("taskkill.exe")
                        if taskkill is not None:
                            try:
                                subprocess.run([taskkill, "/PID", str(launcher.pid),
                                                "/T", "/F"],
                                    capture_output=True, text=True, timeout=5)
                            except (OSError, subprocess.TimeoutExpired):
                                pass
                        if launcher.poll() is None:
                            launcher.terminate()
                    try:
                        launcher.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        launcher.kill()
                        launcher.wait()
                    _cleanup_edge_test_profile(root)
                    (evidence_root / "cleanup.json").write_text(json.dumps({
                        "browser_close_returncode": close.returncode,
                        "launcher_pid": launcher.pid,
                        "launcher_returncode": launcher.returncode,
                        "profile_exists_after_cleanup": profile.exists(),
                        "owned_temp_root_exists_after_cleanup": root.exists(),
                    }, indent=2) + "\n", encoding="utf-8")
                    self.assertEqual(close.returncode, 0, close.stderr)
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if server_thread is not None:
                server_thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
