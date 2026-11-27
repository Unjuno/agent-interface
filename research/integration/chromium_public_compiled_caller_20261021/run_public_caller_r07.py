"""One-shot real Codex grounding + Chromium + public guarded-MCP form run."""
from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from PIL import Image
from Xlib import X, display
from Xlib.ext import res

from runtime.cli_v1.mcp_server import create_server
from research.live_control.compiled_form_grounding_v1 import validate as validate_grounding
from research.live_control.integrated_efficiency_app_server_model_v1 import PersistentGroundingModel
from research.live_control.integrated_efficiency_compiled_adapter_v1 import (
    EXPECTED_METHOD_CONTRACT, compile_form_method,
)
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient


REPO = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RAW = PACKET / "raw" / "r07"
TOKEN = "uictrl-20261021-a7c8"
FORM_RESPONSE_DELAY_MS = 100
MODEL_NAME = "gpt-6.1-sol"
EFFORT = "medium"
DISPLAY = os.environ.get("DISPLAY", ":100")
CHROME = "/home/user/.cache/agent-interface-live-caller-20261021/browsers/chromium-1248/chrome-linux64/chrome"
LIBS = "/home/user/.cache/agent-interface-live-caller-20261021/linux-libs/rootfs/usr/lib/x86_64-linux-gnu"
CODEX = "/mnt/c/Users/user/AppData/Local/OpenAI/Codex/bin/896a0166b774037a/codex.exe"


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def metadata(reply):
    block = next((item for item in reply.content if getattr(item, "type", None) == "text"), None)
    if block is None:
        raise ValueError("MCP response did not contain metadata text")
    return json.loads(block.text)


def windows_path(path: Path) -> str:
    return subprocess.run(["wslpath", "-w", str(path.resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


def find_chromium_window(timeout=20):
    d = display.Display(DISPLAY)
    root = d.screen().root
    deadline = time.monotonic() + timeout
    candidates = []
    while time.monotonic() < deadline:
        candidates = []
        for window in root.query_tree().children:
            try:
                attrs, geometry = window.get_attributes(), window.get_geometry()
                if attrs.map_state != X.IsViewable or geometry.width < 800 or geometry.height < 600:
                    continue
                prop = window.get_full_property(d.intern_atom("_NET_WM_PID"), X.AnyPropertyType)
                pid = int(prop.value[0]) if prop is not None and len(prop.value) else None
                candidates.append({"window":window, "id":window.id, "width":geometry.width,
                                   "height":geometry.height, "title":window.get_wm_name(),
                                   "pid":pid})
            except Exception:
                continue
        if candidates:
            break
        time.sleep(0.1)
    if not candidates:
        d.close()
        raise TimeoutError("no mapped Chromium window at least 800x600")
    chosen = max(candidates, key=lambda row: row["width"] * row["height"])
    chosen["window"].set_input_focus(X.RevertToParent, X.CurrentTime)
    d.sync()
    query = d.res_query_client_ids([{"client":chosen["id"], "mask":res.LocalClientPIDMask}])
    xres_pids = []
    if len(query.ids) == 1:
        xres_pids = [int(value) for value in query.ids[0].value]
    d.close()
    chosen.pop("window")
    chosen["xres_local_client_pids"] = xres_pids
    chosen["candidate_windows"] = [
        {key:value for key,value in row.items() if key != "window"}
        for row in candidates]
    return chosen


def make_fixture_server(post_path: Path, ready_path: Path):
    records = []
    ready_records = []
    lock = threading.Lock()
    page_ready = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def do_GET(self):
            body = f'''<!doctype html><meta charset="utf-8">
<title>Control task</title>
<style>
html,body{{margin:0;width:100%;height:100%;font-family:Arial,sans-serif;background:#f5f7fb;color:#161b22}}
h1{{position:absolute;left:100px;top:36px;font-size:28px}}
p{{position:absolute;left:100px;top:94px;font-size:18px}}
label{{position:absolute;left:180px;top:162px;font-size:16px}}
input{{box-sizing:border-box;position:absolute;left:180px;top:190px;width:320px;height:48px;
 border:2px solid #25364a;border-radius:3px;padding:4px 8px;color:#111;font:20px monospace;
 background:repeating-linear-gradient(90deg,#fff0c0 0 6px,#e0e8ff 6px 8px)}}
#filled-cue{{position:absolute;left:520px;top:190px;width:64px;height:48px;background:#f400ff}}
button{{box-sizing:border-box;position:absolute;left:620px;top:190px;width:128px;height:48px;
 border:2px solid #1e2d44;border-radius:3px;background:#3559d5;color:white;font:bold 18px Arial}}
#saved-cue{{position:absolute;left:780px;top:190px;width:64px;height:48px;background:#fff}}
#status{{position:absolute;left:180px;top:270px;font-size:18px}}
</style>
<h1>Local control task</h1><p>Enter this exact token, then select Save: <strong>{TOKEN}</strong></p>
<label for="token">Access token</label><input id="token" name="value" form="task" autocomplete="off" autofocus>
<div id="filled-cue" aria-hidden="true"></div><button id="save" type="submit" form="task">Save</button>
<div id="saved-cue" aria-hidden="true"></div><div id="status">Not submitted</div>
<form id="task" method="post" action="/submit"></form>
 <script>const field=document.getElementById('token');field.addEventListener('input',()=>{{
 document.getElementById('filled-cue').style.background=field.value.length?'#00c864':'#f400ff';}});
 requestAnimationFrame(()=>requestAnimationFrame(()=>fetch('/ready',{{method:'POST'}})));</script>'''.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.path == "/ready":
                row = {"event":"render_ready", "path":self.path,
                       "received_monotonic_ns":time.monotonic_ns(),
                       "client_address":self.client_address[0],
                       "body_bytes":len(raw)}
                with lock:
                    ready_records.append(row)
                    ready_path.write_text(json.dumps(ready_records, indent=2) + "\n",
                                          encoding="utf-8")
                page_ready.set()
                self.send_response(204)
                self.end_headers()
                return
            parsed = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
            row = {"path":self.path, "submitted_values":parsed.get("value", []),
                   "body_text":raw.decode("utf-8", "replace"),
                   "received_monotonic_ns":time.monotonic_ns(),
                   "client_address":self.client_address[0]}
            with lock:
                records.append(row)
                post_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
            time.sleep(FORM_RESPONSE_DELAY_MS / 1000)
            row["response_ready_monotonic_ns"] = time.monotonic_ns()
            row["response_delay_actual_ns"] = (
                row["response_ready_monotonic_ns"] - row["received_monotonic_ns"])
            with lock:
                post_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
            body = ('''<!doctype html><meta charset="utf-8"><title>Control task result</title>
<style>html,body{margin:0;width:100%;height:100%;font-family:Arial;background:#f5f7fb}
#saved-cue{position:absolute;left:780px;top:190px;width:64px;height:48px;background:#00c864}
#status{position:absolute;left:180px;top:270px;font-size:24px;color:#15321e}</style>
<div id="saved-cue"></div><div id="status">Submission received</div>''').encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, records, lock, page_ready, ready_records


async def run():
    RAW.mkdir(parents=True, exist_ok=False)
    report = {"schema":"agent-interface/chromium-public-compiled-caller-live-v1",
              "run_id":"chromium-public-compiled-standard-caller-live-r07-20261021",
              "status":"RUNNING", "display":DISPLAY,
              "model":{"requested":MODEL_NAME,"effort":EFFORT},
              "token":TOKEN,"timeline_ns":{},"input_attempted":False}
    http = client = model = None
    server = None
    browser = None
    browser_fd = None
    try:
        chromium_env = dict(os.environ, LD_LIBRARY_PATH=LIBS)
        version = subprocess.check_output([CHROME, "--version"], env=chromium_env,
                                          text=True).strip()
        (page_server, page_thread, post_records, post_lock,
         page_ready, ready_records) = make_fixture_server(
             RAW/"fixture-post.json", RAW/"page-render-ready.json")
        report["browser_version"] = version
        report["local_fixture_origin"] = f"http://127.0.0.1:{page_server.server_port}/form"
        profile = tempfile.TemporaryDirectory(prefix="agent-interface-chromium-", dir=str(RAW))
        browser_log = open(RAW/"chromium-stderr.txt", "wb")
        browser = subprocess.Popen([
            CHROME,"--no-sandbox","--disable-gpu","--disable-dev-shm-usage",
            "--no-first-run","--no-default-browser-check","--disable-background-networking",
            "--disable-component-update","--disable-sync","--disable-default-apps",
            "--disable-extensions","--password-store=basic","--window-size=1024,768",
            "--window-position=0,0",f"--user-data-dir={profile.name}",
            f"--app={report['local_fixture_origin']}"],
            stdout=subprocess.DEVNULL,stderr=browser_log,env=chromium_env,start_new_session=True)
        window = find_chromium_window()
        report["target_window"] = window
        report["timeline_ns"]["browser_window_ready"] = time.monotonic_ns()
        render_wait_started = time.monotonic_ns()
        render_ready = await asyncio.to_thread(page_ready.wait, 10.0)
        render_wait_returned = time.monotonic_ns()
        if not render_ready or len(ready_records) != 1:
            raise TimeoutError("fixture did not report exactly one two-frame render-ready receipt")
        report["page_render_readiness"] = {
            "signal":"local page POST after two requestAnimationFrame callbacks",
            "wait_started_ns":render_wait_started,
            "wait_returned_ns":render_wait_returned,
            "receipt":ready_records[0]}
        write_json(RAW/"page-render-ready.json", ready_records)

        mcp_root = RAW/"mcp"
        mcp_root.mkdir()
        server = create_server({"app":window["id"]}, mcp_root, display_name=DISPLAY,
            session_mode="guarded-x11", guarded_process_identity=True,
            guarded_query_worker=True, guarded_window_lifecycle=True,
            guarded_owned_process=True)
        observe_started = time.monotonic_ns()
        observation_reply = await server.call_tool("interface_guarded_observe", {})
        observation_returned = time.monotonic_ns()
        observed = metadata(observation_reply)
        image_block = next((item for item in observation_reply.content
                            if getattr(item,"type",None)=="image"),None)
        if image_block is None:
            raise RuntimeError("public observation did not return its source image")
        image_path = RAW/"source-observation.png"
        image_path.write_bytes(base64.b64decode(image_block.data))
        image = Image.open(image_path).convert("RGB")
        write_json(RAW/"source-observation.json", observed)
        report["source_observation"] = {
            "call_started_ns":observe_started,"call_returned_ns":observation_returned,
            "source_sequence":observed["source"]["sequence"],
            "image_size":list(image.size),
            "image_sha256":__import__("hashlib").sha256(image_path.read_bytes()).hexdigest(),
            "compiled_scope":observed["session"]["compiled_scope"],
            "compiled_surface":observed["session"]["compiled_surface"],
        }
        if image.size != (1024,768):
            raise ValueError(f"unexpected source image dimensions: {image.size!r}")

        client = CodexAppServerClient([CODEX,"app-server","--stdio"],
            journal_path=RAW/"provider-protocol.jsonl")
        init = client.initialize()
        write_json(RAW/"provider-initialize.json", init)
        workspace = REPO.resolve()
        model = PersistentGroundingModel(RAW/"provider-session", workspace,
            node="unused", cli="unused", contract="compiled", model=MODEL_NAME,
            effort=EFFORT, client=client, path_converter=windows_path)
        task_prompt = (
            "Task: in the current local form, enter the exact token " + TOKEN +
            " into the visible Access token field and then select Save. From the supplied "
            "current screenshot only, return the center point of the Access token input and "
            "the center point of the Save button in source_observation_pixels. The method "
            "must be the fixed two-action sequence: enter_exact_token; continue only when "
            "the filled-field visual cue changes and the Save target is revalidated; activate_submit; "
            "complete only after the submission visual cue changes. Do not claim execution."
        )
        model_started = time.monotonic_ns()
        model_result = model.call(RAW/"provider-call-01", task_prompt, image_path,
                                  "compiled", workspace)
        model_returned = time.monotonic_ns()
        report["timeline_ns"].update(model_started=model_started,model_returned=model_returned)
        report["provider_attempt"] = {
            "thread_id":model_result["thread_id"],"turn_id":model_result["turn_id"],
            "answer_eligible":model_result["answer_eligible"],
            "requested_model":model_result["requested_model"],
            "requested_effort":model_result["requested_effort"],
            "visible_images_submitted":1,"usage":model_result["usage"],
            "wait_ns":model_result["runner_ns"],
            "result_path":"provider-call-01/result.json"}
        grounding = validate_grounding(model_result["raw"])
        field_point = grounding["field_point"]
        submit_point = grounding["submit_point"]
        field_anchor = [field_point[0], field_point[1]-20]
        report["grounded_points"] = {"field":field_point,"stable_anchor": field_anchor,"submit":submit_point,
                                     "source_sequence":observed["source"]["sequence"]}

        # Re-observe after the provider wait, then verify that its grounded
        # points still land on the same visibly configured field and button.
        fresh_started = time.monotonic_ns()
        fresh_reply = await server.call_tool("interface_guarded_observe", {})
        fresh_returned = time.monotonic_ns()
        fresh = metadata(fresh_reply)
        fresh_block = next((item for item in fresh_reply.content
                            if getattr(item,"type",None)=="image"),None)
        if fresh_block is None:
            raise RuntimeError("fresh public observation did not return image")
        fresh_path = RAW/"post-model-fresh-observation.png"
        fresh_path.write_bytes(base64.b64decode(fresh_block.data))
        fresh_image = Image.open(fresh_path).convert("RGB")
        write_json(RAW/"post-model-fresh-observation.json", fresh)
        if (fresh["session"]["compiled_scope"] != observed["session"]["compiled_scope"] or
            fresh["session"]["compiled_surface"] != observed["session"]["compiled_surface"]):
            raise RuntimeError("public caller scope or target surface changed during model wait")
        if fresh_image.size != image.size:
            raise RuntimeError("source image geometry changed during model wait")
        field_probe = field_anchor
        fill_cue = [field_point[0]+212, field_point[1]]
        submit_probe = [submit_point[0], submit_point[1]+14]
        saved_cue = [field_point[0]+472, field_point[1]]
        if any(x<0 or y<0 or x>=fresh_image.width or y>=fresh_image.height
               for x,y in (field_probe,fill_cue,submit_probe,saved_cue)):
            raise RuntimeError("model grounding places a compiled predicate point out of frame")
        field_rgb=fresh_image.getpixel(tuple(field_probe))
        fill_rgb=fresh_image.getpixel(tuple(fill_cue))
        submit_rgb=fresh_image.getpixel(tuple(submit_probe))
        saved_rgb=fresh_image.getpixel(tuple(saved_cue))
        if fill_rgb != (244,0,255):
            raise RuntimeError(f"filled cue was not in its frozen initial state: {fill_rgb!r}")
        if submit_rgb != (53,89,213):
            raise RuntimeError(f"grounded Save point missed the visible button fill: {submit_rgb!r}")
        if saved_rgb != (255,255,255):
            raise RuntimeError(f"submission cue not initially neutral: {saved_rgb!r}")
        if field_rgb not in ((255,240,192),(224,232,255)):
            raise RuntimeError(f"grounded field point missed its textured target: {field_rgb!r}")
        report["post_model_recheck"] = {
            "started_ns":fresh_started,"returned_ns":fresh_returned,
            "source_sequence":fresh["source"]["sequence"],
            "compiled_scope_same":True,"compiled_surface_same":True,
            "field_probe_rgb":list(field_rgb),"fill_cue_rgb":list(fill_rgb),
            "submit_probe_rgb":list(submit_rgb),"saved_cue_rgb":list(saved_rgb)}

        aliases = {}
        for alias,point,size in (("field",field_anchor,[4,4]),("submit",submit_point,[32,32])):
            started=time.monotonic_ns()
            minted=metadata(await server.call_tool("interface_guarded_mint",{
                "alias":alias,"source_sequence":fresh["source"]["sequence"],
                "point":point,"region_size":size}))
            ended=time.monotonic_ns()
            write_json(RAW/f"mint-{alias}.json",minted)
            if minted.get("status") != "minted":
                raise RuntimeError(f"target alias mint failed for {alias}: {minted!r}")
            aliases[alias]={"offset":minted["offset"],"started_ns":started,
                            "returned_ns":ended,"lifetime":minted.get("lifetime")}
        interface=compile_form_method(
            interface_id="chromium-public-caller-live-r07",
            session_scope=observed["session"]["compiled_scope"],
            surface=observed["session"]["compiled_surface"],
            field_handle="field",submit_handle="submit",
            method_contract=EXPECTED_METHOD_CONTRACT,
            effect_timeout_ms=250,effect_poll_interval_ms=25)
        predicate_rules={
            "field_pixels_changed":{"point":fill_cue,"states":[
                {"rgb":[244,0,255],"value":False},
                {"rgb":[0,200,100],"value":True}]},
            "field_target_present":{"point":field_probe,"states":[
                {"rgb":list(field_rgb),"value":True}]},
            "submit_target_present":{"point":submit_probe,"states":[
                {"rgb":list(submit_rgb),"value":True}]},
            "submission_pixels_changed":{"point":saved_cue,"states":[
                {"rgb":[255,255,255],"value":False},
                {"rgb":[0,200,100],"value":True}]}}
        effect_rules={
            "enter_token":{"point":fill_cue,"rgb":[0,200,100]},
            "submit_form":{"point":saved_cue,"rgb":[0,200,100]}}
        bindings={
            "enter_token":{"interaction":"click","offset":aliases["field"]["offset"],
                           "tail":[{"op":"text","text":TOKEN,"gap_ms":20}]},
            "submit_form":{"interaction":"click","offset":aliases["submit"]["offset"],
                            "tail":[]}}
        write_json(RAW/"compiled-interface.json",interface)
        write_json(RAW/"compiled-profile.json",{
            "predicate_rules":predicate_rules,"effect_rules":effect_rules,
            "bindings":bindings})

        call_started=time.monotonic_ns()
        report["input_attempted"]=True
        call_reply=await server.call_tool("interface_guarded_compiled",{
            "interface":interface,"bindings":bindings,
            "predicate_rules":predicate_rules,"effect_rules":effect_rules,
            "wait_for_result_ms":10000})
        call_returned=time.monotonic_ns()
        call=metadata(call_reply)
        report["timeline_ns"].update(public_call_started=call_started,
                                     public_call_returned=call_returned)
        write_json(RAW/"public-compiled-invoke.json",call)
        if type(call.get("call_id")) is not str or not call["call_id"]:
            raise RuntimeError(f"public caller returned no call id: {call!r}")
        call_id=call["call_id"]
        deadline=time.monotonic()+35
        terminal=call
        while terminal.get("status")=="pending" and time.monotonic()<deadline:
            await asyncio.sleep(0.05)
            terminal=metadata(await server.call_tool("interface_results",{
                "call_id":call_id,"include_image":False}))
        write_json(RAW/"public-compiled-terminal.json",terminal)
        if terminal.get("status")=="pending":
            raise TimeoutError("public compiled call did not become terminal within 35 seconds")
        report["public_call"]={"call_id":call_id,"status":terminal.get("status"),
            "call_directory":terminal.get("call_directory"),
            "method_receipt":terminal.get("method_receipt"),
            "owner_timing":terminal.get("owner_timing"),
            "task_success":terminal.get("task_success"),
            "replay_allowed":terminal.get("replay_allowed"),
            "started_ns":call_started,"returned_ns":call_returned}
        with post_lock:
            post_rows=list(post_records)
        write_json(RAW/"fixture-post.json",post_rows)
        score={"scorer":"independent test-harness parser over captured HTTP POST body",
               "expected_token":TOKEN,"submission_count":len(post_rows),
               "submitted_values":post_rows[0]["submitted_values"] if len(post_rows)==1 else None,
               "success":len(post_rows)==1 and post_rows[0]["path"]=="/submit"
                         and post_rows[0]["submitted_values"]==[TOKEN],
               "runtime_task_success":terminal.get("task_success")}
        write_json(RAW/"independent-score.json",score)
        report["independent_score"]=score
        if terminal.get("method_receipt",{}).get("outcome")!="TASK_SUCCEEDED":
            raise RuntimeError("compiled method did not reach TASK_SUCCEEDED")
        if not score["success"]:
            raise RuntimeError("independent exact POST scorer did not pass")

        report["status"]="PASS_SCOPED_LIVE_CHROMIUM_PUBLIC_CALLER"
        report["timeline_ns"]["completed_ns"]=time.monotonic_ns()
    except Exception as error:
        report.update(status="FAIL_PRESERVED_NO_RETRY",error_type=type(error).__name__,error=repr(error))
        report["timeline_ns"]["failed_ns"]=time.monotonic_ns()
    finally:
        if server is not None:
            try:
                started=time.monotonic_ns()
                closed=metadata(await server.call_tool("interface_close",{}))
                write_json(RAW/"public-close.json",closed)
                report["close"]={"started_ns":started,"returned_ns":time.monotonic_ns(),
                                 "status":closed.get("status"),
                                 "release_confirmed":closed.get("release_confirmed"),
                                 "session":closed.get("session")}
            except Exception as error:
                report["close_error"]={"type":type(error).__name__,"error":repr(error)}
        if model is not None:
            try: model.close()
            except Exception as error: report["model_close_error"]=repr(error)
        if client is not None:
            try: client.close(timeout=8)
            except Exception as error: report["appserver_close_error"]=repr(error)
        if browser is not None and browser.poll() is None:
            try: os.killpg(browser.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            try: browser.wait(timeout=4)
            except subprocess.TimeoutExpired:
                try: os.killpg(browser.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                browser.wait()
        if 'browser_log' in locals():
            try: browser_log.close()
            except Exception: pass
        if 'profile' in locals():
            profile.cleanup()
        if 'page_server' in locals():
            page_server.shutdown(); page_server.server_close(); page_thread.join(timeout=2)
        report["cleanup"]={"browser_exitcode":None if browser is None else browser.returncode,
                            "appserver_closed":bool(client is None or client.process.poll() is not None),
                            "fixture_server_closed":bool('page_server' not in locals() or
                                                          not page_thread.is_alive())}
        write_json(RAW/"run.json",report)
        print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["status"]=="PASS_SCOPED_LIVE_CHROMIUM_PUBLIC_CALLER" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))


