import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO / 'research' / 'live_control'), str(REPO / 'research' / 'integration' / 'standard_mcp_task_ledger_57_v1')]

from PIL import Image

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_relay import Relay
from runtime.cli_v1.test_mcp_owned_process import (
    _compiled_profile_payload, _fake_owner_factory,
)
from research.integration.standard_mcp_task_ledger_57_v1.app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall, parse_app_server_tool_request,
)
from research.integration.standard_mcp_task_ledger_57_v1.ledger import summarize
from research.integration.standard_mcp_task_ledger_57_v1.provider_attempt_recorder import ProviderAttemptRecorder
from research.integration.standard_mcp_task_ledger_57_v1.recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from research.integration.standard_mcp_task_ledger_57_v1.recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter

MODEL = "gpt-6.1-sol"
EFFORT = "low"
PACKET = Path(__file__).resolve().parent
OUT = PACKET / "run"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")


def build_command():
    codex = subprocess.run(["where.exe", "codex"], check=True, capture_output=True,
                           text=True).stdout.splitlines()[0].strip()
    command = [codex, "app-server", "--stdio"]
    for feature in ("apps", "plugins", "remote_plugin", "browser_use",
                    "browser_use_external", "computer_use", "in_app_browser",
                    "code_mode", "code_mode_host"):
        command += ["--disable", feature]
    for name in ("blender", "chrome-devtools", "node_repl", "playwright", "puppeteer"):
        command += ["-c", f"mcp_servers.{name}.enabled=false"]
    return command


async def run():
    if OUT.exists():
        raise FileExistsError(f"immutable run path already exists: {OUT}")
    OUT.mkdir(parents=True)
    server_root = OUT / "server"
    server_root.mkdir()
    (server_root / "compiled-profile-mode").write_text("enabled", encoding="utf-8")
    workspace = OUT / "empty-workspace"
    workspace.mkdir()
    appserver_dir = OUT / "app-server"
    appserver_dir.mkdir()
    journal = appserver_dir / "protocol.jsonl"
    ledger_dir = OUT / "ledger"
    image_path = OUT / "initial-fakex.png"
    command = build_command()
    write_json(OUT / "invocation.json", {
        "command": command, "cwd": str(workspace), "model": MODEL,
        "effort": EFFORT, "python": sys.version, "trial": "p02",
    })

    server = create_server(
        {"app": 20}, server_root, session_mode="guarded-x11",
        guarded_process_identity=True, guarded_query_worker=True,
        guarded_owned_process=True,
        _guarded_owner_factory=_fake_owner_factory,
    )

    class ServerClient:
        async def call_tool(self, name, arguments):
            return await server.call_tool(name, arguments)

    recorder = ProviderAttemptRecorder(ledger_dir)
    caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
    client = None
    planner = None
    terminal = {"classification": "FAIL_BEFORE_TRIAL", "wslc_used": False}
    run_error = None
    started = time.perf_counter_ns()
    try:
        observed_response = await caller.call_tool(
            None, "observe-p01", "interface_guarded_observe", {})
        observed = json.loads(observed_response["result"]["content"][0]["text"])
        initial_path = server_root / "synthetic-application-initial.rgb"
        initial_raw = initial_path.read_bytes()
        (OUT / "initial-fakex.bgrx").write_bytes(initial_raw)
        Image.frombytes("RGB", (32, 32), initial_raw, "raw", "BGRX").save(image_path)

        minted_response = await caller.call_tool(
            None, "mint-p01", "interface_guarded_mint", {
                "alias": "field", "source_sequence": observed["source"]["sequence"],
                "point": [8, 8], "region_size": [12, 12],
            })
        minted = json.loads(minted_response["result"]["content"][0]["text"])
        payload = _compiled_profile_payload(
            observed["session"]["compiled_scope"],
            observed["session"]["compiled_surface"], minted["offset"])
        payload["wait_for_result_ms"] = 10000
        (OUT / "planned-public-mcp-arguments.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")

        journal.write_bytes(b"")
        client = CodexAppServerClient(command, cwd=workspace, journal_path=journal)
        initialize_started = time.perf_counter_ns()
        initialize_response = client.initialize(name="agent-interface-p01", version="1")
        (appserver_dir / "initialize.json").write_text(
            json.dumps(initialize_response, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        planner = PersistentPlannerAdapter(
            client, model=MODEL, effort=EFFORT, cwd=str(workspace),
            base_instructions=(
                "You are a single-call structured output adapter. Return only the "
                "JSON object requested by the user, matching the supplied schema. "
                "Do not invoke tools or add explanatory text."),
        )
        thread_id = planner.start_session()
        (appserver_dir / "thread-started.json").write_text(
            json.dumps({"thread_id": thread_id,
                        "elapsed_ns": time.perf_counter_ns() - initialize_started},
                       indent=2) + "\n", encoding="utf-8", newline="\n")
        model = AppServerPublicMcpModelCall(
            planner, journal, workspace=workspace, contract="public-mcp",
            output_schema={"type": "object"}, model=MODEL, effort=EFFORT,
            path_converter=str, turn_timeout=90)
        arguments_json = json.dumps(payload, allow_nan=False, separators=(",", ":"))
        prompt = (
            "A single bounded public-MCP call is planned for the synthetic UI in the "
            "attached image. Return exactly the JSON arguments object shown below, "
            "without markdown or additional fields. This smoke tests real provider "
            "accounting and caller wiring; the target and method were already fixed.\n"
            "ARGUMENTS_JSON=" + arguments_json)
        request_bytes, provider_call = build_model_provider_call(
            model_call=model.call, root=OUT / "provider-call",
            prompt=prompt, image=image_path, contract="public-mcp", workspace=workspace)
        generation_and_call = await caller.invoke_generation_to_tool(
            "appserver-p01", request_bytes, provider_call,
            "compiled-p01", "interface_guarded_compiled",
            lambda generation: parse_app_server_tool_request(
                generation["response_bytes"],
                thread_id=generation["backend_result"]["thread_id"],
                turn_id=generation["backend_result"]["turn_id"],
            ),
        )
        tool_response = generation_and_call.get("tool_response")
        if tool_response is not None:
            (OUT / "public-mcp-response.json").write_text(
                json.dumps(tool_response, indent=2, sort_keys=True) + "\n",
                encoding="utf-8", newline="\n")
        final_path = server_root / "synthetic-application-state.rgb"
        final_raw = final_path.read_bytes() if final_path.exists() else initial_raw
        (OUT / "final-fakex.bgrx").write_bytes(final_raw)
        pixel = list(Image.frombytes("RGB", (32, 32), final_raw, "raw", "BGRX").getpixel((1, 1)))
        task_success = pixel == [255, 0, 0]
        recorder.record_task_score(
            "separate-fakex-pixel-oracle-v1", task_success, final_raw)
        ledger = recorder.reconcile()
        write_json(OUT / "LEDGER-RECONCILED.json", ledger)
        summary = summarize(ledger["events"])
        generation = generation_and_call.get("generation")
        runtime_body = None
        if tool_response and tool_response.get("status") == "returned":
            try:
                runtime_body = json.loads(tool_response["result"]["content"][0]["text"])
            except Exception:
                runtime_body = None
        pass_gate = bool(
            generation and generation.get("status") == "completed" and
            generation.get("usage", {}).get("status") == "reported" and
            generation_and_call.get("tool_call_submitted") is True and
            ledger.get("complete") is True and task_success is True)
        terminal = {
            "classification": "PASS_PROVIDER_CALLER_FAKE_X_ONLY" if pass_gate else
                              "FAIL_OR_HOLD_FIRST_OUTCOME_RETAINED",
            "model": MODEL, "effort": EFFORT,
            "provider_status": None if generation is None else generation.get("status"),
            "provider_usage": None if generation is None else generation.get("usage"),
            "tool_call_submitted": generation_and_call.get("tool_call_submitted"),
            "tool_status": None if tool_response is None else tool_response.get("status"),
            "runtime_outcome": (runtime_body or {}).get("method_receipt", {}).get("outcome"),
            "runtime_task_success": (runtime_body or {}).get("task_success"),
            "independent_pixel": pixel,
            "independent_task_success": task_success,
            "ledger_complete": ledger.get("complete"),
            "ledger_summary": summary,
            "elapsed_ns": time.perf_counter_ns() - started,
            "wslc_used": False,
            "physical_input": False,
        }
        write_json(OUT / "RESULT.json", terminal)
    except BaseException as error:
        terminal.update({"error_type": type(error).__name__, "error": str(error),
                         "elapsed_ns": time.perf_counter_ns() - started})
        write_json(OUT / "RESULT.json", terminal)
        run_error = error
    finally:
        try:
            await server.call_tool("interface_close", {})
        except BaseException as error:
            write_json(OUT / "CALLER_CLOSE_ERROR.json", {
                "error_type": type(error).__name__, "error": str(error)})
        if client is not None:
            try:
                client.close(timeout=5)
            except BaseException as error:
                write_json(OUT / "APP_SERVER_CLOSE_ERROR.json", {
                    "error_type": type(error).__name__, "error": str(error)})

    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rows.append(f"{sha(path.read_bytes())}  {path.relative_to(OUT).as_posix()}")
    (OUT / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(terminal, indent=2, sort_keys=True))
    if run_error is not None:
        raise run_error


if __name__ == "__main__":
    asyncio.run(run())