"""Live local Edge surface composition of V5 handles, caller v3 and compiled GUI.

The browser is real, but launched headless and driven through CDP. The model
target point is a fixture constant. This is not OS-level input or provider
evidence.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse
import urllib.request
import unittest

from PIL import Image

from research.live_control.model_point_target_v1 import OPERATION
from research.live_control.test_chromium_v5_generation_mint_guard_v1 import (
    PointMintBackend,
)
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    EXPECTED_METHOD_CONTRACT,
    compile_form_method,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)
from research.live_control.test_windows_compiled_gui_edge_live_v1 import (
    _cleanup_edge_test_profile,
)
from research.live_control.windows_ocr_observer_v1 import (
    WindowsOcrObserver,
    exact_token_state,
)
from runtime.core_v1.compiled_gui import validate
from runtime.guarded_x11_v1.handles import TargetHandleStore


LIVE = Path(__file__).resolve().parent
REPO = LIVE.parents[1]
if str(LIVE) not in sys.path:
    sys.path.insert(0, str(LIVE))
TOKEN = "t9910254"
SCOPE = "edge-v5-caller-v3-local-session"
FIELD_POINT = [190, 121]
SUBMIT_POINT = [545, 121]
FIELD_SIZE = [64, 28]
SUBMIT_SIZE = [48, 28]

CDP = r'''const fs=require('fs');const [ws,op,arg,arg2]=process.argv.slice(1);let seq=0;const pending=new Map();const sock=new WebSocket(ws);function rpc(method,params={}){const id=++seq;return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});sock.send(JSON.stringify({id,method,params}));});}function event(name,ms=5000){return new Promise(resolve=>{const timer=setTimeout(()=>{sock.removeEventListener('message',f);resolve(false);},ms);function f(e){const m=JSON.parse(e.data);if(m.method===name){clearTimeout(timer);sock.removeEventListener('message',f);resolve(true);}}sock.addEventListener('message',f);});}sock.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result||{});}});sock.addEventListener('open',async()=>{try{await rpc('Page.enable');let result={};if(op==='navigate'){await rpc('Emulation.setDeviceMetricsOverride',{width:756,height:488,deviceScaleFactor:1,mobile:false});const loaded=event('Page.loadEventFired');await rpc('Page.navigate',{url:arg});await loaded;}else if(op==='capture'){const s=await rpc('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(arg,Buffer.from(s.data,'base64'));}else if(op==='type'||op==='click'){const [x,y]=arg.split(',').map(Number);await rpc('Input.dispatchMouseEvent',{type:'mouseMoved',x,y,button:'none'});await rpc('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',buttons:1,clickCount:1});await rpc('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',buttons:0,clickCount:1});if(op==='type'){await rpc('Input.insertText',{text:arg2});}else{await event('Page.loadEventFired',3000);}}else if(op==='reload'){const loaded=event('Page.loadEventFired');await rpc('Page.reload',{ignoreCache:true});await loaded;}else{throw Error('unsupported operation');}const tree=await rpc('Page.getFrameTree');result=tree.frameTree.frame;console.log(JSON.stringify(result));sock.close();process.exit(0);}catch(e){console.error(String(e));process.exit(2);}});'''
BROWSER_CLOSE = r'''const w=new WebSocket(process.argv[1]);let done=false;w.addEventListener('open',()=>w.send(JSON.stringify({id:1,method:'Browser.close'})));w.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id===1){done=true;process.exit(m.error?1:0);}});w.addEventListener('close',()=>process.exit(0));w.addEventListener('error',()=>process.exit(done?0:1));setTimeout(()=>process.exit(2),5000);'''


def _digest_int(value):
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:4],
                          "big") % 2_000_000_000 + 2


def _sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _EdgePointHarness:
    """The exact V5 execute method over retained live Edge screenshots."""

    def __init__(self, *, target_id, process_generation, capture_frame,
                 image_path, scope):
        self.target_id = target_id
        self.process_generation = process_generation
        self.capture_frame = capture_frame
        self.image_path = image_path
        self.sequence = 0
        self.current = None
        self.pixels = None
        self.point_source_history = {}
        self.handles = TargetHandleStore(scope)
        self.events = []
        self.snapshot("source", 0)
        self.point_source_history[self.sequence] = {
            "observation": copy.deepcopy(self.current),
            "image": self.pixels.copy(),
        }

    def _observation(self, frame):
        self.sequence += 1
        window_generation = _sha("|".join((self.target_id, frame["id"],
                                            frame.get("loaderId", ""))))
        return {
            "sequence": self.sequence,
            "capture_ns": time.perf_counter_ns(),
            "pointer_binding": {
                "focus": _digest_int(self.target_id),
                "surface": _digest_int("http://127.0.0.1"),
                "geometry": [0, 0, 756, 488],
                "process_generation": self.process_generation,
                "window_generation": window_generation,
            },
        }

    def observation(self):
        return copy.deepcopy(self.current)

    def image(self):
        return self.pixels.copy()

    def emit(self, row):
        self.events.append(copy.deepcopy(row))

    def snapshot(self, _identifier, _index):
        frame = self.capture_frame(self.image_path)
        self.current = self._observation(frame)
        with Image.open(self.image_path) as opened:
            self.pixels = opened.convert("RGB")
        return copy.deepcopy(self.current)


class ChromiumV5EdgeCallerV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence_root = Path(os.environ["AGENT_INTERFACE_EDGE_V5_EVIDENCE_DIR"])
        cls.evidence_root.mkdir(parents=True, exist_ok=False)
        cls.edge = (Path(os.environ.get("ProgramFiles(x86)",
                                      r"C:\Program Files (x86)")) /
                    "Microsoft" / "Edge" / "Application" / "msedge.exe")
        cls.node = shutil.which("node.exe") or shutil.which("node")
        if not cls.edge.is_file() or cls.node is None:
            raise unittest.SkipTest("Edge and Node.js are required")
        source_paths = [
            Path(__file__).resolve(),
            LIVE / "session_v33.py",
            LIVE / "test_chromium_v5_generation_mint_guard_v1.py",
            LIVE / "test_windows_compiled_gui_edge_live_v1.py",
            LIVE / "model_point_target_v1.py",
            LIVE / "integrated_efficiency_compiled_adapter_v2.py",
            LIVE / "integrated_efficiency_compiled_execution_v2.py",
            LIVE / "adaptive_acquisition_caller_v3.py",
            LIVE / "windows_ocr_observer_v1.py",
            LIVE / "windows_ocr_worker_v1.ps1",
            REPO / "runtime/core_v1/compiled_gui.py",
            REPO / "runtime/guarded_x11_v1/handles.py",
            REPO / "runtime/guarded_x11_v1/handles_base.py",
            REPO / "runtime/guarded_x11_v1/handles_texture.py",
            REPO / "docs/PROJECT_OVERVIEW.md",
            cls.evidence_root.parents[1] / "PROTOCOL.md",
        ]
        source_hashes = {str(path.relative_to(REPO)):
                         hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in source_paths}
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                capture_output=True, text=True, check=True).stdout.splitlines()
        conditions = {
            "scope": "one positive and one changed-generation local Edge task per Python mode",
            "main_base": "3979669f5fb25115cd38ab67fba219ba3d87f494",
            "experiment_head": head,
            "tracked_worktree_diff_empty": not subprocess.run(
                ["git", "diff", "--quiet"], cwd=REPO).returncode,
            "worktree_status_before_run": status,
            "task_value": TOKEN,
            "task_scorer": "independent local HTTP server exact POST body",
            "target_point_source": "fixed fixture points for known local HTML controls; no model call",
            "browser": str(cls.edge.resolve()),
            "node": subprocess.run([cls.node, "--version"], capture_output=True,
                                   text=True, check=True).stdout.strip(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "input_adapter": "headless Edge CDP mouse press/release and insertText; not OS input",
            "provider_calls": 0,
            "network_scope": "loopback form server only",
            "cases": {
                "positive": "V5 mint, real TargetHandleStore, caller v3, compiled two-action path, exact POST score",
                "changed-generation": "after entry, same-target page reload changes loader generation; exact token restored from localStorage; next admission must refuse",
            },
            "python_optimization": __debug__ is False,
            "source_sha256": source_hashes,
        }
        conditions_path = cls.evidence_root / "conditions.json"
        conditions_path.write_text(json.dumps(conditions, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
        cls.conditions_sha256 = hashlib.sha256(
            conditions_path.read_bytes()).hexdigest()

    def _case(self, case_name, *, invalidate_after_entry):
        case_root = self.evidence_root / case_name
        case_root.mkdir()
        exact_posts = []
        posts_lock = threading.Lock()
        token = TOKEN

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):
                body = ("<!doctype html><meta charset='utf-8'>"
                        "<style>body{margin:0;font:16px Arial}"
                        "input{position:absolute;left:150px;top:100px;"
                        "width:300px;height:42px;font:bold 26px Arial}"
                        "button{position:absolute;left:500px;top:100px;"
                        "width:90px;height:42px;font:18px Arial}</style>"
                        "<form method='post' action='/submit'>"
                        "<label>Value <input id='value' name='value' "
                        "placeholder='Enter code'></label>"
                        "<button type='submit'>Save</button></form>"
                        "<script>const i=document.querySelector('#value');"
                        "try{i.value=localStorage.getItem('ai-v5-value')||'';}"
                        "catch(e){}i.addEventListener('input',()=>{try{"
                        "localStorage.setItem('ai-v5-value',i.value);}catch(e){}});"
                        "</script>").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                submitted = urllib.parse.parse_qs(
                    raw.decode("utf-8", "replace"), keep_blank_values=True)
                row = {"path": self.path, "raw_body": raw.decode("utf-8", "strict"),
                       "submitted_values": submitted.get("value", []),
                       "exact": submitted == {"value": [token]},
                       "received_ns": time.perf_counter_ns()}
                with posts_lock:
                    exact_posts.append(row)
                text = "AI INTEGRATED SAVED" if row["exact"] else "REJECTED"
                body = ("<!doctype html><meta charset='utf-8'><h1>" +
                        text + "</h1>").encode("utf-8")
                self.send_response(200 if row["exact"] else 422)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        origin = f"http://127.0.0.1:{server.server_port}/form"
        profile = LIVE / ("interface-edge-submit-" + secrets.token_hex(8))
        screenshot = case_root / "scratch.png"
        edge_process = None
        version = None
        state = {"observations": {}, "last": None, "baseline_field_digest": None,
                 "previous_digest": None, "dispatched": [], "admissions": [],
                 "effects": [], "outer_scores": [], "journal": [],
                 "ocr_rows": [], "receipts": [], "authorization": {},
                 "mint_events": [], "minted": {}, "frame_rows": []}
        capture_number = 0
        result = None
        errors = []
        server_posts = []
        profile_cleaned = None
        try:
            edge_process = subprocess.Popen([
                str(self.edge), "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=0", "--remote-allow-origins=*",
                f"--user-data-dir={profile}", "about:blank"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            port_file = profile / "DevToolsActivePort"
            deadline = time.monotonic() + 12
            port = None
            while time.monotonic() < deadline:
                if port_file.exists():
                    try:
                        port = int(port_file.read_text(encoding="ascii").splitlines()[0])
                        version = json.load(urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/json/version", timeout=1))
                        break
                    except (OSError, ValueError, json.JSONDecodeError):
                        pass
                time.sleep(0.1)
            self.assertIsNotNone(version, "isolated Edge did not expose DevTools")
            targets = json.load(urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/list", timeout=2))
            target = next(row for row in targets if row.get("type") == "page")
            page_ws = target["webSocketDebuggerUrl"]
            target_id = target["id"]

            def cdp(operation, *args, timeout=10):
                completed = subprocess.run(
                    [self.node, "-e", CDP, page_ws, operation, *map(str, args)],
                    capture_output=True, text=True, timeout=timeout)
                if completed.returncode:
                    raise RuntimeError("Edge CDP failed: " + completed.stderr[-500:])
                output = completed.stdout.strip().splitlines()
                return json.loads(output[-1]) if output else {}

            cdp("navigate", origin, timeout=12)
            process_generation = _sha(
                str(edge_process.pid) + "|" + str(self.edge.resolve()))

            def capture(path):
                nonlocal capture_number
                frame = cdp("capture", path)
                capture_number += 1
                shutil.copyfile(path, case_root / f"capture-{capture_number:02}.png")
                state["frame_rows"].append({"frame_id": frame.get("id"),
                                            "loader_id": frame.get("loaderId"),
                                            "url": frame.get("url")})
                return frame

            harness = _EdgePointHarness(
                target_id=target_id, process_generation=process_generation,
                capture_frame=capture, image_path=screenshot, scope=SCOPE)
            for alias, point, size in (("field", FIELD_POINT, FIELD_SIZE),
                                       ("submit", SUBMIT_POINT, SUBMIT_SIZE)):
                step = {"op": OPERATION, "name": alias,
                        "coordinate_frame": "window_content", "source_sequence": 1,
                        "point": point, "region_size": size, "ttl_ms": 30000,
                        "freshness_ms": 5000, "search_radius": 0,
                        "allowed_transformations": ["window_translation"]}
                minted = PointMintBackend.execute(
                    harness, step, None, "mint-" + alias, 0)
                state["minted"][alias] = {
                    "alias": minted["handle"],
                    "offset": minted["derived_offset"],
                    "source_patch_sha256": minted["source_patch_sha256"],
                    "fresh_patch_sha256": minted["fresh_patch_sha256"],
                    "fresh_patch_exact": minted["fresh_patch_exact"],
                    "reference_kind": minted["reference_kind"],
                    "private_registry_id_exposed": minted[
                        "private_registry_id_exposed"],
                }
            state["mint_events"] = harness.events

            with WindowsOcrObserver(timeout_seconds=12) as observer:
                def observe(_payload):
                    frame = capture(screenshot)
                    with Image.open(screenshot) as opened:
                        image = opened.convert("RGB")
                    full_observation = harness._observation(frame)
                    sequence = full_observation["sequence"]
                    # This is also the generation the real handle store checks.
                    field_patch = image.crop((150, 100, 450, 142)).tobytes()
                    field_digest = hashlib.sha256(field_patch).hexdigest()
                    full_digest = hashlib.sha256(image.tobytes()).hexdigest()
                    field_ocr = observer.recognize(
                        screenshot, region=(145, 95, 310, 55), scale=2)
                    submit_ocr = observer.recognize(
                        screenshot, region=(490, 95, 110, 55), scale=2)
                    page_ocr = observer.recognize(
                        screenshot, region=(0, 0, 756, 200), scale=1)
                    value_state = exact_token_state(field_ocr["text"], token)
                    submit_present = "save" in page_ocr["text"].casefold()
                    if state["baseline_field_digest"] is None:
                        state["baseline_field_digest"] = field_digest
                    completion_text = re.sub(
                        r"[^a-z0-9]", "", page_ocr["text"].casefold())
                    submitted_pixels = (
                        "aiintegratedsaved" in completion_text
                        and full_digest != state["previous_digest"])
                    digest = hashlib.sha256(
                        (full_digest + full_observation["pointer_binding"][
                            "window_generation"]).encode()).hexdigest()
                    compiled_observation = {
                        "sequence": sequence,
                        "captured_ns": full_observation["capture_ns"],
                        "surface": SCOPE,
                        "predicates": {
                            "field_pixels_changed": field_digest !=
                                state["baseline_field_digest"],
                            "field_value_matches_task": value_state,
                            "field_target_present": bool(field_ocr["text"].strip()),
                            "submit_target_present": submit_present,
                            "submission_pixels_changed": bool(submitted_pixels),
                        },
                        "evidence_ref": f"edge-v5-frame-{sequence}",
                        "evidence_digest": digest,
                    }
                    stored_image = image.copy()
                    image.close()
                    state["observations"][sequence] = (
                        full_observation, stored_image)
                    state["last"] = compiled_observation
                    state["previous_digest"] = full_digest
                    state["ocr_rows"].append({
                        "sequence": sequence,
                        "frame_id": frame.get("id"),
                        "loader_id": frame.get("loaderId"),
                        "url": frame.get("url"),
                        "ocr_field": field_ocr["text"],
                        "ocr_submit": submit_ocr["text"],
                        "value_state": value_state,
                        "page_ocr": page_ocr["text"],
                        "predicates": compiled_observation["predicates"],
                        "evidence_digest": digest,
                    })
                    shutil.copyfile(screenshot, case_root / f"frame-{sequence}.png")
                    return compiled_observation

                def resolve(alias, observation):
                    config = state["minted"][alias]
                    stored_observation, image = state["observations"][
                        observation["sequence"]]
                    resolved = harness.handles.resolve_point(
                        alias, config["offset"], stored_observation, image,
                        time.perf_counter_ns(), session_scope=SCOPE)
                    return resolved

                def revalidate(target):
                    frame = capture(screenshot)
                    full = harness._observation(frame)
                    with Image.open(screenshot) as opened:
                        image = opened.convert("RGB")
                    state["observations"][full["sequence"]] = (full, image)
                    outcomes = [resolve(alias, {"sequence": full["sequence"]})
                                for alias in target.values()]
                    status = "revalidated" if all(row["eligible"] for row in outcomes) else (
                        "association_changed" if any(row["status"] == "SCOPE_MISMATCH"
                                                      for row in outcomes) else "stale")
                    state["admissions"].append({"stage": "caller_revalidation",
                                                "resolutions": outcomes})
                    return {"status": status}

                def admit(payload):
                    alias = payload["symbol"]["target_reference"]
                    resolved = resolve(alias, payload["observation"])
                    state["admissions"].append({"stage": "compiled_admission",
                                                "alias": alias,
                                                "status": resolved["status"],
                                                "reason": resolved.get("reason"),
                                                "point": resolved.get("point"),
                                                "sequence": resolved.get("sequence")})
                    if not resolved["eligible"]:
                        mapping = {"STALE": "stale", "MISSING": "missing",
                                   "SCOPE_MISMATCH": "association_changed",
                                   "AMBIGUOUS": "missing", "MOVED": "stale"}
                        return {"eligible": False,
                                "status": mapping.get(resolved["status"],
                                                      "association_changed"),
                                "authorization": None,
                                "expected_sequence": payload["observation"]["sequence"],
                                "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}
                    authorization = secrets.token_urlsafe(24)
                    state["authorization"][authorization] = {
                        "alias": alias, "point": resolved["point"],
                        "sequence": payload["observation"]["sequence"],
                        "operation": payload["operation"],
                    }
                    return {"eligible": True, "status": "revalidated",
                            "authorization": authorization,
                            "expected_sequence": payload["observation"]["sequence"],
                            "valid_until_ns": min(
                                resolved["valid_until_ns"],
                                time.perf_counter_ns() + 1_000_000_000)}

                def execute(payload):
                    ticket = state["authorization"].pop(
                        payload["authorization"], None)
                    if (ticket is None or ticket["sequence"] !=
                            payload["expected_sequence"] or
                            ticket["operation"] != payload["operation"] or
                            time.perf_counter_ns() >= payload["valid_until_ns"]):
                        return {"status": "refused", "action_id": "expired-ticket",
                                "effect_ref": "no-dispatch",
                                "release": {"verified": True, "keys_down": [],
                                            "buttons_down": []},
                                "input_dispatched": False}
                    x, y = ticket["point"]
                    if payload["operation"] == "enter_exact_token":
                        cdp("type", f"{x},{y}", token)
                        if invalidate_after_entry:
                            cdp("reload", timeout=12)
                    elif payload["operation"] == "activate_submit":
                        cdp("click", f"{x},{y}", timeout=12)
                    else:
                        raise RuntimeError("unexpected operation")
                    state["dispatched"].append(payload["operation"])
                    return {"status": "completed",
                            "action_id": f"edge-action-{len(state['dispatched'])}",
                            "effect_ref": f"edge-effect-{len(state['dispatched'])}",
                            "release": {"verified": True, "keys_down": [],
                                        "buttons_down": []},
                            "input_dispatched": True}

                def verify_core_effect(payload):
                    state["effects"].append(copy.deepcopy(payload))
                    expected = payload["expected_effect"]
                    observation = payload["observation"]
                    if all(observation["predicates"].get(key) == value
                           for key, value in expected.items()):
                        return {"status": "succeeded",
                                "evidence_ref": observation["evidence_ref"]}
                    return {"status": "failed",
                            "evidence_ref": observation["evidence_ref"]}

                def verify_outer(_payload):
                    with posts_lock:
                        posts = copy.deepcopy(exact_posts)
                    exact = len(posts) == 1 and posts[0]["exact"]
                    state["outer_scores"].append({"posts": posts, "exact": exact})
                    return {"status": "succeeded" if exact else "failed",
                            "evidence_ref": "independent-local-http-post-score"}

                target = {name: name for name in ("field", "submit")}
                interface_for_target = lambda payload: validate(compile_form_method(
                    interface_id="chromium-v5-edge-form",
                    session_scope=SCOPE,
                    surface=SCOPE,
                    field_handle=payload["target"]["field"],
                    submit_handle=payload["target"]["submit"],
                    method_contract=EXPECTED_METHOD_CONTRACT,
                ))
                caller_adapters = {
                    "reuse_revalidate": revalidate,
                    "final_revalidate": revalidate,
                    "verify_effect": verify_outer,
                    "journal": lambda row: state["journal"].append(
                        copy.deepcopy(row)),
                }
                spec = {"target": "enter and submit exact local form token",
                        "route": "reuse", "coarse_origin": "caller_provided",
                        "provided_coarse": None, "cached_target": target,
                        "repair_on": [], "local_repair_on": [],
                        "session_id": SCOPE}
                result = run_compiled_interface_in_caller(
                    spec, caller_adapters, interface_for_target,
                    {"observe": observe, "admit": admit, "execute": execute,
                     "verify_effect": verify_core_effect,
                     "journal": lambda row: state["journal"].append(
                         copy.deepcopy(row)),
                     "cancelled": lambda: False},
                    on_receipt=lambda receipt: state["receipts"].append(
                        copy.deepcopy(receipt)))
                with posts_lock:
                    server_posts = copy.deepcopy(exact_posts)
                self.assertEqual(result["outcome"],
                                 "EXECUTION_INCOMPLETE" if invalidate_after_entry
                                 else "TASK_SUCCEEDED", result)
                if invalidate_after_entry:
                    self.assertEqual(result["delivery"], "confirmed_partial")
                    self.assertEqual(result["execution_progress"]["completed_actions"], 1)
                    self.assertEqual(state["dispatched"], ["enter_exact_token"])
                    self.assertEqual(len(server_posts), 0)
                    failed = [row for row in state["admissions"]
                              if row["stage"] == "compiled_admission"][-1]
                    self.assertEqual(failed["status"], "SCOPE_MISMATCH")
                    self.assertEqual(failed["reason"],
                                     "window_generation_changed_or_missing")
                    self.assertEqual(len(state["outer_scores"]), 0)
                else:
                    self.assertEqual(result["task_effect"], "succeeded")
                    self.assertEqual(result["delivery"], "confirmed")
                    self.assertEqual(state["dispatched"], [
                        "enter_exact_token", "activate_submit"])
                    self.assertEqual(len(server_posts), 1)
                    self.assertTrue(server_posts[0]["exact"])
                    self.assertEqual(result["compiled_execution_receipt"][
                        "completed_transitions"], 2)
                    self.assertTrue(all(row["release_verified"] for row in
                        result["compiled_execution_receipt"]["transitions"]))
                    self.assertEqual(len(state["outer_scores"]), 1)
                return result
        except Exception as error:
            errors.append({"type": type(error).__name__, "error": str(error)})
            raise
        finally:
            if edge_process is not None:
                if edge_process.poll() is None:
                    try:
                        subprocess.run([self.node, "-e", BROWSER_CLOSE,
                                        version["webSocketDebuggerUrl"] if version else ""],
                                       capture_output=True, text=True, timeout=6)
                    except Exception:
                        pass
                    if edge_process.poll() is None:
                        edge_process.terminate()
                try:
                    edge_process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    edge_process.kill()
                    edge_process.wait()
            try:
                _cleanup_edge_test_profile(profile)
                profile_cleaned = not profile.exists()
            except Exception as error:
                profile_cleaned = not profile.exists()
                errors.append({"cleanup_type": type(error).__name__,
                               "cleanup_error": str(error)})
            server.shutdown()
            server_thread.join(timeout=3)
            server.server_close()
            with posts_lock:
                if not server_posts:
                    server_posts = copy.deepcopy(exact_posts)
            output = {"case": case_name,
                      "invalidate_after_entry": invalidate_after_entry,
                      "outcome": None if result is None else result.get("outcome"),
                      "result": result,
                      "minted_handles": state["minted"],
                      "mint_events": state["mint_events"],
                      "observations": state["ocr_rows"],
                      "admissions": state["admissions"],
                      "dispatched_operations": state["dispatched"],
                      "core_effect_checks": state["effects"],
                      "outer_scores": state["outer_scores"],
                      "server_posts": server_posts,
                      "receipts": state["receipts"],
                      "journal": state["journal"],
                      "browser_frames": state["frame_rows"],
                      "edge_version": version,
                      "profile_cleaned": profile_cleaned,
                      "conditions_sha256": self.conditions_sha256,
                      "python": platform.python_version(),
                      "optimization": __debug__ is False,
                      "errors": errors}
            (case_root / "run.json").write_text(
                json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8", newline="\n")

    def test_positive_and_changed_window_generation(self):
        self._case("positive", invalidate_after_entry=False)
        self._case("changed-generation", invalidate_after_entry=True)
        for case in ("positive", "changed-generation"):
            saved = json.loads((self.evidence_root / case / "run.json").read_text(
                encoding="utf-8"))
            self.assertTrue(saved["profile_cleaned"], saved)
            self.assertEqual(saved["errors"], [], saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
