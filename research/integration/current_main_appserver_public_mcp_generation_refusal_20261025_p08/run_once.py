"""One-shot model-grounded visual target trial through the standard caller."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
OUT = PACKET / "run"
MODEL = "gpt-6.1-sol"
EFFORT = "low"
GREEN_RECT = (12, 3, 20, 13)
SUCCESS_PIXEL = (1, 1)
SUCCESS_RGB = [255, 0, 0]

sys.path[:0] = [
    str(REPO), str(REPO / "research" / "live_control"),
    str(REPO / "research" / "integration" / "standard_mcp_task_ledger_57_v1")]

from PIL import Image

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_relay import Relay
from runtime.cli_v1.test_mcp_owned_process import _compiled_profile_payload
from research.integration.standard_mcp_task_ledger_57_v1.app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall, parse_app_server_tool_request,
)
from research.integration.standard_mcp_task_ledger_57_v1.ledger import summarize
from research.integration.standard_mcp_task_ledger_57_v1.provider_attempt_recorder import ProviderAttemptRecorder
from research.integration.standard_mcp_task_ledger_57_v1.recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from research.integration.standard_mcp_task_ledger_57_v1.recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter
from research.integration.current_main_appserver_public_mcp_generation_refusal_20261025_p08.fake_factory import (
    grounding_fake_owner_factory,
)
from research.integration.current_main_appserver_public_mcp_generation_refusal_20261025_p08.privacy_redact import (
    redact_run,
)


def strict_schema(value):
    if type(value) is dict:
        return {"type": "object",
                "properties": {k: strict_schema(v) for k, v in value.items()},
                "required": list(value), "additionalProperties": False}
    if type(value) is list:
        return {"type": "array",
                "items": strict_schema(value[0]) if value else {"type": "integer"}}
    if value is None:
        return {"type": "null"}
    if type(value) is bool:
        return {"type": "boolean"}
    if type(value) is int:
        return {"type": "integer"}
    if type(value) is float:
        return {"type": "number"}
    if type(value) is str:
        return {"type": "string"}
    raise TypeError(f"unsupported schema value: {type(value).__name__}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")


def build_command():
    codex = subprocess.run(["where.exe", "codex"], check=True,
                           capture_output=True, text=True).stdout.splitlines()[0].strip()
    command = [codex, "app-server", "--stdio"]
    for feature in ("apps", "plugins", "remote_plugin", "browser_use",
                    "browser_use_external", "computer_use", "in_app_browser",
                    "code_mode", "code_mode_host"):
        command += ["--disable", feature]
    for name in ("openaiDeveloperDocs", "node_repl"):
        command += ["-c", f"mcp_servers.{name}.enabled=false"]
    return command


def tool_body(response, method):
    if type(response) is not dict or response.get("status") != "returned":
        return None
    try:
        return json.loads(response["result"]["content"][0]["text"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


async def run():
    if OUT.exists():
        raise FileExistsError(f"immutable run path already exists: {OUT}")
    OUT.mkdir(parents=True)
    server_root = OUT / "server"
    server_root.mkdir()
    (server_root / "compiled-profile-mode").write_text("enabled", encoding="ascii")
    workspace = OUT / "empty-workspace"
    workspace.mkdir()
    appserver_dir = OUT / "app-server"
    appserver_dir.mkdir()
    journal = appserver_dir / "protocol.jsonl"
    ledger_dir = OUT / "ledger"
    screenshot_path = OUT / "observed-public-mcp.png"
    command = build_command()
    write_json(OUT / "invocation.json", {
        "command": command, "cwd": str(workspace), "model": MODEL,
        "effort": EFFORT, "python": sys.version, "trial": "p08"})

    server = create_server(
        {"app": 20}, server_root, session_mode="guarded-x11",
        guarded_process_identity=True, guarded_query_worker=True,
        guarded_owned_process=True,
        _guarded_owner_factory=grounding_fake_owner_factory)

    class ServerClient:
        async def call_tool(self, name, arguments):
            return await server.call_tool(name, arguments)

    recorder = ProviderAttemptRecorder(ledger_dir)
    caller = RecordedPublicMcpCaller(Relay(ServerClient()), recorder)
    client = None
    planner = None
    started = time.perf_counter_ns()
    phase = "before_observation"
    terminal = {"classification": "FAIL_BEFORE_PROVIDER_CALL",
                "wslc_used": False, "physical_input": False}
    run_error = None
    try:
        observed_response = await caller.call_tool(
            None, "observe-p08", "interface_guarded_observe", {})
        observed = tool_body(observed_response, "interface_guarded_observe")
        if observed is None or observed.get("status") != "observed":
            raise RuntimeError("public observation did not return an observed receipt")
        phase = "observation_returned"
        artifact = observed["observation_report"]["observation"]["artifact"]
        source_image = Path(artifact["path"]).read_bytes()
        if sha(source_image) != artifact["sha256"]:
            raise ValueError("public observation image digest mismatch")
        screenshot_path.write_bytes(source_image)
        initial_path = server_root / "synthetic-application-initial.rgb"
        initial_raw = initial_path.read_bytes()
        (OUT / "initial-framebuffer.bgrx").write_bytes(initial_raw)

        point_schema = strict_schema({"point": [0, 0]})
        client = CodexAppServerClient(command, cwd=workspace,
                                      journal_path=journal)
        initialize_started = time.perf_counter_ns()
        initialize = client.initialize(name="agent-interface-p08", version="1")
        write_json(appserver_dir / "initialize.json", initialize)
        planner = PersistentPlannerAdapter(
            client, model=MODEL, effort=EFFORT, cwd=str(workspace),
            base_instructions=(
                "You are a visual target selector. Follow the user's target task, "
                "return only the JSON object required by the supplied schema, and "
                "do not call tools or add explanations."))
        thread_id = planner.start_session()
        write_json(appserver_dir / "thread-started.json", {
            "thread_id": thread_id,
            "elapsed_ns": time.perf_counter_ns() - initialize_started})
        model = AppServerPublicMcpModelCall(
            planner, journal, workspace=workspace, contract="public-mcp",
            output_schema=point_schema, model=MODEL, effort=EFFORT,
            path_converter=str, turn_timeout=90)
        prompt = (
            "The attached screenshot shows three small colored square buttons "
            "labeled R, G, and B. Click the green button labeled G. Return only "
            "the point [x,y] at its center using full-image pixel coordinates "
            "with origin at the top left. Do not infer or return any other "
            "coordinates, aliases, actions, or tool arguments.")
        request_bytes, provider_call = build_model_provider_call(
            model_call=model.call, root=OUT / "provider-call", prompt=prompt,
            image=screenshot_path, contract="public-mcp", workspace=workspace)
        phase = "provider_call_pending"

        def prepare_mint_arguments(generation):
            nonlocal phase
            phase = "provider_completed_pre_mint"
            selected = parse_app_server_tool_request(
                generation["response_bytes"],
                thread_id=generation["backend_result"]["thread_id"],
                turn_id=generation["backend_result"]["turn_id"])
            if (set(selected) != {"point"} or type(selected["point"]) is not list or
                    len(selected["point"]) != 2 or
                    any(type(value) is not int for value in selected["point"])):
                raise ValueError("model point must be exactly two integers")
            write_json(OUT / "model-selected-point.json", {
                "point": selected["point"],
                "schema": "two integer screenshot coordinates",
                "observation_sequence": observed["source"]["sequence"],
                "target_generation": {
                    "process": observed["source"]["pointer_binding"]["process_generation"]},
                "image_sha256": artifact["sha256"]})
            marker = server_root / "invalidate-generation-after-provider"
            marker.write_text("provider turn completed; invalidate prior target",
                              encoding="utf-8")
            write_json(OUT / "generation-invalidation-marker.json", {
                "written_after_provider_response": True,
                "written_before_public_mint": True,
                "old_process_generation": observed["source"]["pointer_binding"]["process_generation"],
                "new_process_generation": "b" * 64,
            })
            arguments = {"alias": "grounded_green",
                         "source_sequence": observed["source"]["sequence"],
                         "point": selected["point"], "region_size": [4, 4]}
            write_json(OUT / "model-derived-mint-request.json", arguments)
            return arguments

        joined = await caller.invoke_generation_to_tool(
            "appserver-p08", request_bytes, provider_call, "mint-p08",
            "interface_guarded_mint", prepare_mint_arguments)
        phase = "mint_response_received"
        mint_response = joined.get("tool_response")
        mint = tool_body(mint_response, "interface_guarded_mint")
        if mint is not None:
            write_json(OUT / "public-mint-response.json", mint_response)

        compiled_response = None
        if mint is not None and mint.get("status") == "minted":
            phase = "compiled_action_pending"
            payload = _compiled_profile_payload(
                observed["session"]["compiled_scope"],
                observed["session"]["compiled_surface"], mint["offset"])
            payload["interface"]["symbols"]["field"]["target_reference"] = "grounded_green"
            payload["bindings"]["enter"]["interaction"] = "click"
            payload["bindings"]["enter"]["tail"] = []
            payload["wait_for_result_ms"] = 10000
            write_json(OUT / "planned-compiled-arguments.json", payload)
            compiled_response = await caller.call_tool(
                "appserver-p08", "compiled-p08",
                "interface_guarded_compiled", payload)
            write_json(OUT / "public-compiled-response.json", compiled_response)

        # Score the stale-generation refusal from owner-side logs and public
        # receipts. No physical input or product task success is claimed.
        selected_record = (json.loads((OUT / "model-selected-point.json").read_text(
            encoding="utf-8")) if (OUT / "model-selected-point.json").exists() else None)
        mint_request = (json.loads((OUT / "model-derived-mint-request.json").read_text(
            encoding="utf-8")) if (OUT / "model-derived-mint-request.json").exists() else None)
        owner_input_events = json.loads(
            (server_root / "owner-input-events.json").read_text(encoding="utf-8"))
        write_json(OUT / "owner-input-events.json", owner_input_events)
        click_files = list(server_root.rglob("synthetic-target-click.json"))
        effect_files = list(server_root.rglob("synthetic-effect-receipt.json"))
        final_files = list(server_root.rglob("synthetic-application-state.rgb"))
        final_raw = final_files[0].read_bytes() if len(final_files) == 1 else initial_raw
        (OUT / "final-framebuffer.bgrx").write_bytes(final_raw)
        observation_dir = server_root / ("guarded-session-" + observed["session"]["session_id"])
        observation_rows = []
        for path in observation_dir.glob("observation-*.json"):
            row = json.loads(path.read_text(encoding="utf-8"))
            observation_rows.append({"sequence": row.get("sequence"),
                                     "process_generation": row.get("pointer_binding", {}).get("process_generation")})
        observation_rows.sort(key=lambda row: row["sequence"])
        write_json(OUT / "generation-observations.json", observation_rows)
        fresh_generations = [row for row in observation_rows
                             if row["sequence"] > observed["source"]["sequence"]]
        compiled = tool_body(compiled_response, "interface_guarded_compiled")
        receipt = (compiled or {}).get("method_receipt", {})
        critical = receipt.get("critical_events", [])
        refusals = [event for event in critical
                    if event.get("event") == "admission_refused"]
        final_pixel = list(Image.frombytes(
            "RGB", (32, 32), final_raw, "raw", "BGRX").getpixel(SUCCESS_PIXEL))
        point = selected_record.get("point") if selected_record else None
        point_inside = bool(
            type(point) is list and len(point) == 2 and
            GREEN_RECT[0] <= point[0] <= GREEN_RECT[2] and
            GREEN_RECT[1] <= point[1] <= GREEN_RECT[3])
        mint_receipt_path = observation_dir / "mint-grounded_green.json"
        mint_receipt = (json.loads(mint_receipt_path.read_text(encoding="utf-8"))
                        if mint_receipt_path.exists() else {})
        no_action = (receipt.get("completed_transitions") == 0 and
                     receipt.get("outcome") == "SAFE_YIELD" and
                     receipt.get("reason") == "association_changed" and
                     len(refusals) == 1 and refusals[0].get("status") == "association_changed" and
                     not any(event.get("event") == "action_terminal" for event in critical))
        stale_refusal = bool(
            point_inside and selected_record and selected_record.get("image_sha256") == artifact["sha256"] and
            mint_request and mint_request.get("source_sequence") == observed["source"]["sequence"] and
            mint_receipt.get("created_sequence") == observed["source"]["sequence"] and
            any(row["process_generation"] == "b" * 64 for row in fresh_generations) and
            no_action and not owner_input_events and not click_files and not effect_files and
            not final_files and final_raw == initial_raw)
        recorder.record_task_score(
            "independent-stale-generation-refusal-v1", stale_refusal,
            json.dumps({"point": point, "refusals": refusals,
                        "owner_input_events": owner_input_events,
                        "initial_equals_final": final_raw == initial_raw},
                       sort_keys=True).encode("utf-8"))
        ledger = recorder.reconcile()
        write_json(OUT / "LEDGER-RECONCILED.json", ledger)
        generation = joined.get("generation")
        summary = summarize(ledger["events"])
        result_ok = bool(
            generation and generation.get("status") == "completed" and
            generation.get("usage", {}).get("status") == "reported" and
            joined.get("tool_call_submitted") is True and
            mint is not None and mint.get("status") == "minted" and
            compiled is not None and stale_refusal and ledger.get("complete") is True)
        terminal = {
            "classification": "PASS_STALE_GENERATION_REFUSED_BEFORE_INPUT_FAKE_X_ONLY" if result_ok else
                              "FAIL_OR_HOLD_FIRST_OUTCOME_RETAINED",
            "model": MODEL, "effort": EFFORT,
            "provider_status": None if generation is None else generation.get("status"),
            "provider_usage": None if generation is None else generation.get("usage"),
            "observation_sequence": observed["source"]["sequence"],
            "process_generation": observed["source"]["pointer_binding"]["process_generation"],
            
            "observation_image_sha256": artifact["sha256"],
            "model_image_sha256": selected_record.get("image_sha256") if selected_record else None,
            "tool_call_submitted": joined.get("tool_call_submitted"),
            "mint_status": None if mint is None else mint.get("status"),
            "mint_source_sequence": None if mint_request is None else mint_request.get("source_sequence"),
            "mint_created_sequence": mint_receipt.get("created_sequence"),
            "compiled_status": None if compiled_response is None else compiled_response.get("status"),
            "runtime_outcome": receipt.get("outcome"),
            "refusal_reason": receipt.get("reason"),
            "runtime_task_success": (compiled or {}).get("task_success"),
            "selected_point": point, "selected_point_inside_green": point_inside,
            "generation_observations": observation_rows,
            "admission_refusals": refusals,
            "completed_transitions": receipt.get("completed_transitions"),
            "owner_input_events": owner_input_events,
            "owner_click_count": len(click_files), "effect_receipt_count": len(effect_files),
            "application_state_unchanged": final_raw == initial_raw,
            "independent_final_pixel": final_pixel,
            "independent_refusal_success": stale_refusal,
            "ledger_complete": ledger.get("complete"),
            "ledger_summary": summary,
            "elapsed_ns": time.perf_counter_ns() - started,
            "wslc_used": False, "physical_input": False,
        }
        write_json(OUT / "RESULT.json", terminal)
    except BaseException as error:
        classifications = {
            "provider_completed_pre_mint": "FAIL_AFTER_PROVIDER_PRE_MINT",
            "provider_call_pending": "PROVIDER_OUTCOME_UNKNOWN",
            "mint_response_received": "FAIL_AFTER_MINT_BEFORE_EFFECT_SCORE",
            "compiled_action_pending": "FAIL_AFTER_MINT_DURING_COMPILED_ACTION",
            "observation_returned": "FAIL_BEFORE_PROVIDER_CALL",
            "before_observation": "FAIL_BEFORE_OBSERVATION",
        }
        terminal.update({"classification": classifications.get(
                             phase, "FAIL_OR_HOLD_FIRST_OUTCOME_RETAINED"),
                         "phase": phase,
                         "error_type": type(error).__name__, "error": str(error),
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

    redactions = redact_run()
    write_json(OUT / "redaction-count.json", {
        "redaction_count": len(redactions["redactions"]),
        "redactions_sha256": sha((PACKET / "REDACTIONS.json").read_bytes())})
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rows.append(f"{sha(path.read_bytes())}  {path.relative_to(OUT).as_posix()}")
    (OUT / "SHA256SUMS").write_text("\n".join(rows) + "\n",
                                   encoding="utf-8", newline="\n")
    print(json.dumps(terminal, indent=2, sort_keys=True))
    if run_error is not None:
        raise run_error


if __name__ == "__main__":
    asyncio.run(run())
