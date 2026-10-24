"""One-shot model-grounded visual target trial through the standard caller."""

import asyncio
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
ARGS = argparse.ArgumentParser()
ARGS.add_argument("--pair", required=True, choices=("p01", "p02", "p03"))
ARGS.add_argument("--arm", required=True, choices=("direct_public_input", "compiled_public_caller"))
CLI = ARGS.parse_args()
OUT = PACKET / "run" / f"{CLI.pair}-{CLI.arm}"
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
from research.integration.current_main_appserver_matched_efficiency_20261025_p09.fake_factory import (
    grounding_fake_owner_factory,
)
from research.integration.current_main_appserver_matched_efficiency_20261025_p09.privacy_redact import (
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
    def normalize(item):
        if item is None or type(item) in (bool, int, float, str):
            return item
        if type(item) is dict:
            return {str(key): normalize(child) for key, child in item.items()}
        if type(item) in (list, tuple):
            return [normalize(child) for child in item]
        if hasattr(item, "model_dump"):
            return normalize(item.model_dump(mode="json", by_alias=True))
        if hasattr(item, "__dict__"):
            return normalize(vars(item))
        raise TypeError(f"unsupported JSON evidence object: {type(item).__name__}")
    Path(path).write_text(json.dumps(normalize(value), indent=2, sort_keys=True) + "\n",
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
        "effort": EFFORT, "python": sys.version, "study": "p09",
        "pair": CLI.pair, "arm": CLI.arm})

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
            None, "observe-p09", "interface_guarded_observe", {})
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
        initialize = client.initialize(name="agent-interface-p09", version="1")
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

        provider_started_ns = time.perf_counter_ns()
        provider_completed_ns = None
        def prepare_mint_arguments(generation):
            nonlocal phase, provider_completed_ns
            provider_completed_ns = time.perf_counter_ns()
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
            arguments = {"alias": "grounded_green",
                         "source_sequence": observed["source"]["sequence"],
                         "point": selected["point"], "region_size": [4, 4]}
            write_json(OUT / "model-derived-mint-request.json", arguments)
            return arguments

        joined = await caller.invoke_generation_to_tool(
            "appserver-p09", request_bytes, provider_call, "mint-p09",
            "interface_guarded_mint", prepare_mint_arguments)
        phase = "mint_response_received"
        mint_response = joined.get("tool_response")
        mint = tool_body(mint_response, "interface_guarded_mint")
        if mint is not None:
            write_json(OUT / "public-mint-response.json", mint_response)

        action_response = None
        action_started = None
        action_returned = None
        if mint is not None and mint.get("status") == "minted":
            action_started = time.perf_counter_ns()
            if CLI.arm == "direct_public_input":
                phase = "direct_action_pending"
                payload = {"alias": "grounded_green", "offset": mint["offset"],
                           "tail": [], "interaction": "click",
                           "observe_after": True, "wait_for_result_ms": 10000}
                write_json(OUT / "planned-direct-arguments.json", payload)
                action_response = await caller.call_tool(
                    "appserver-p09", "direct-p09", "interface_guarded_input", payload)
                write_json(OUT / "public-direct-response.json", action_response)
            else:
                phase = "compiled_action_pending"
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], mint["offset"])
                payload["interface"]["symbols"]["field"]["target_reference"] = "grounded_green"
                payload["bindings"]["enter"]["interaction"] = "click"
                payload["bindings"]["enter"]["tail"] = []
                payload["wait_for_result_ms"] = 10000
                write_json(OUT / "planned-compiled-arguments.json", payload)
                action_response = await caller.call_tool(
                    "appserver-p09", "compiled-p09",
                    "interface_guarded_compiled", payload)
                write_json(OUT / "public-compiled-response.json", action_response)
            action_returned = time.perf_counter_ns()

        # The independent scorer reads the exact model point, owner-side click
        # receipt, and persisted app pixel. It does not trust graph outcome.
        selected_record = (json.loads((OUT / "model-selected-point.json").read_text(
            encoding="utf-8")) if (OUT / "model-selected-point.json").exists() else None)
        mint_request = (json.loads((OUT / "model-derived-mint-request.json").read_text(
            encoding="utf-8")) if (OUT / "model-derived-mint-request.json").exists() else None)
        click_files = list(server_root.rglob("synthetic-target-click.json"))
        effect_files = list(server_root.rglob("synthetic-effect-receipt.json"))
        final_files = list(server_root.rglob("synthetic-application-state.rgb"))
        final_raw = final_files[0].read_bytes() if len(final_files) == 1 else initial_raw
        (OUT / "final-framebuffer.bgrx").write_bytes(final_raw)
        final_pixel = list(Image.frombytes(
            "RGB", (32, 32), final_raw, "raw", "BGRX").getpixel(SUCCESS_PIXEL))
        click = (json.loads(click_files[0].read_text(encoding="utf-8"))
                 if len(click_files) == 1 else None)
        owner_mint_files = list(server_root.rglob("mint-grounded_green.json"))
        owner_mint = (json.loads(owner_mint_files[0].read_text(encoding="utf-8"))
                      if len(owner_mint_files) == 1 else None)
        effect = (json.loads(effect_files[0].read_text(encoding="utf-8"))
                  if len(effect_files) == 1 else None)
        point = selected_record.get("point") if selected_record else None
        point_inside = bool(
            type(point) is list and len(point) == 2 and
            GREEN_RECT[0] <= point[0] <= GREEN_RECT[2] and
            GREEN_RECT[1] <= point[1] <= GREEN_RECT[3])
        click_point = click.get("event", {}).get("point") if click else None
        click_inside = bool(
            type(click_point) is list and len(click_point) == 2 and
            GREEN_RECT[0] <= click_point[0] <= GREEN_RECT[2] and
            GREEN_RECT[1] <= click_point[1] <= GREEN_RECT[3])
        exact_one_click = bool(click and click.get("event", {}).get(
            "button_press_count") == 1)
        click_matches_selected = click_point == point
        method = "interface_guarded_input" if CLI.arm == "direct_public_input" else "interface_guarded_compiled"
        action = tool_body(action_response, method)
        receipt = ((action or {}).get("method_receipt", {}) if CLI.arm == "compiled_public_caller"
                   else (action or {}).get("result", {}))
        releases = receipt.get("transitions", [{}])[0].get("release_verified") is True if CLI.arm == "compiled_public_caller" else bool(
            receipt.get("execution", {}).get("releases") and
            receipt["execution"]["releases"][-1].get("verified") is True)
        close_receipt = None
        if action is not None and action.get("status") == "completed":
            close_receipt = await server.call_tool("interface_close", {})
            close_receipt = json.loads(close_receipt.model_dump_json(by_alias=True))
            close_body = tool_body(close_receipt, "interface_close")
            if close_body and close_body.get("status") == "busy":
                await asyncio.sleep(0.01)
                close_receipt = await server.call_tool("interface_close", {})
                close_receipt = json.loads(close_receipt.model_dump_json(by_alias=True))
                close_body = tool_body(close_receipt, "interface_close")
            write_json(OUT / "post-action-close.json", close_receipt)
        released = releases or bool((tool_body(close_receipt, "interface_close") or {}).get("verified"))
        task_success = bool(
            point_inside and click_inside and click_matches_selected and exact_one_click and effect is not None and
            effect.get("button_press_count") == 1 and
            mint_request is not None and
            mint_request.get("source_sequence") == selected_record.get("observation_sequence") and
            owner_mint is not None and owner_mint.get("created_sequence") == selected_record.get("observation_sequence") and
            final_pixel == SUCCESS_RGB and
            action is not None and action.get("status") == "completed" and released)
        recorder.record_task_score(
            "independent-green-target-click-pixel-v1", task_success,
            json.dumps({"point": point, "click": click,
                        "effect": effect, "final_pixel": final_pixel},
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
            action is not None and task_success and ledger.get("complete") is True)
        terminal = {
            "classification": "PASS_MODEL_GROUNDED_PUBLIC_MCP_FAKE_X_ONLY" if result_ok else
                              "FAIL_OR_HOLD_FIRST_OUTCOME_RETAINED",
            "model": MODEL, "effort": EFFORT,
            "provider_status": None if generation is None else generation.get("status"),
            "provider_usage": None if generation is None else generation.get("usage"),
            "input_tokens": None if generation is None else generation.get("usage", {}).get("input_tokens"),
            "output_tokens": None if generation is None else generation.get("usage", {}).get("output_tokens"),
            "reasoning_output_tokens": None if generation is None else generation.get("usage", {}).get("reasoning_output_tokens"),
            "observation_sequence": observed["source"]["sequence"],
            "process_generation": observed["source"]["pointer_binding"]["process_generation"],
            
            "observation_image_sha256": artifact["sha256"],
            "model_image_sha256": selected_record.get("image_sha256") if selected_record else None,
            "tool_call_submitted": joined.get("tool_call_submitted"),
            "mint_status": None if mint is None else mint.get("status"),
            "mint_source_sequence": None if mint_request is None else mint_request.get("source_sequence"),
            "mint_created_sequence": None if owner_mint is None else owner_mint.get("created_sequence"),
            "pair": CLI.pair, "arm": CLI.arm,
            "action_status": None if action_response is None else action_response.get("status"),
            "runtime_outcome": receipt.get("outcome"),
            "runtime_task_success": None if action is None else action.get("task_success"),
            "release_verified": released,
            "selected_point": point, "selected_point_inside_green": point_inside,
            "owner_click_point": click_point, "owner_click_inside_green": click_inside,
            "owner_click_matches_model_point": click_matches_selected,
            "owner_button_press_count": None if click is None else
                click.get("event", {}).get("button_press_count"),
            "independent_final_pixel": final_pixel,
            "independent_task_success": task_success,
            "ledger_complete": ledger.get("complete"),
            "ledger_summary": summary,
            "provider_turn_ms": (None if provider_completed_ns is None else (provider_completed_ns-provider_started_ns)/1e6),
            "observation_to_action_return_ms": (None if action_returned is None else (action_returned - int(observed["source"].get("capture_ns", action_started))) / 1e6),
            "action_call_ms": (None if action_started is None or action_returned is None else (action_returned-action_started)/1e6),
            "total_trial_ms": (time.perf_counter_ns() - started) / 1e6,
            "public_tool_call_count": len(ledger.get("events", [])),
            "compiled_transition_count": len(receipt.get("transitions", [])) if CLI.arm == "compiled_public_caller" else 0,
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
            "direct_action_pending": "FAIL_AFTER_MINT_DURING_DIRECT_ACTION",
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

    redactions = redact_run(OUT)
    write_json(OUT / "redaction-count.json", {
        "redaction_count": len(redactions["redactions"]),
        "redactions_sha256": sha((OUT / "REDACTIONS.json").read_bytes())})
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
