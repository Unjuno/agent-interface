"""Run one frozen Calculator task over the public supervised Win32 MCP route."""
from __future__ import annotations

import asyncio
import base64
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from ctypes import wintypes
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
ATTEMPT = "win32-public-mcp-calculator-20261024-r05-76fe423b62db484a9ee279c57cb36e65"
TARGET_NAME = "calculator"
HWND = 55117672
EXPECTED_SOURCE = "6aea5d3f359f42811d4e1dd1060fc575560ceeae"
SCREEN_REGION = (40, 32, 336, 541)
EXPECTED_DIMENSIONS = (336, 541)
CLIENT_SIZE = (320, 533)
CLIENT_ORIGIN_SCREEN = (48, 32)


def save_json(path: Path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
                               ensure_ascii=False) + "\n", encoding="utf-8")


def result_text(reply):
    return next((item.text for item in reply.content
                 if getattr(item, "type", None) == "text"), "")


def record_reply(name, reply):
    text = result_text(reply)
    parsed = None
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        pass
    blocks = []
    for index, item in enumerate(reply.content):
        kind = getattr(item, "type", "unknown")
        if kind == "image":
            raw = base64.b64decode(item.data)
            destination = RUN / f"{name}-{index}.png"
            destination.write_bytes(raw)
            blocks.append({"type": "image", "path": destination.name,
                           "sha256": hashlib.sha256(raw).hexdigest(),
                           "bytes": len(raw), "mimeType": item.mimeType})
        elif kind == "text":
            blocks.append({"type": "text", "sha256": hashlib.sha256(
                item.text.encode("utf-8")).hexdigest()})
    record = {"isError": bool(reply.isError), "raw_text": text,
              "parsed": parsed, "blocks": blocks}
    save_json(RUN / f"{name}.json", record)
    return record


def find_first(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_first(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_first(value, key)
            if found is not None:
                return found
    return None


def find_action(obj):
    if isinstance(obj, dict):
        candidate = obj.get("action")
        if isinstance(candidate, dict) and isinstance(candidate.get("status"), str):
            return candidate
        for value in obj.values():
            found = find_action(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_action(value)
            if found is not None:
                return found
    return None


def build_ops(width, height, origin_x, origin_y):
    x = {"left": round(width * 0.13), "second": round(width * 0.375),
         "third": round(width * 0.625), "right": round(width * 0.875)}
    y = {"clear": round(height * 0.388), "789": round(height * 0.643), "456": round(height * 0.745),
         "123+": round(height * 0.848), "0=": round(height * 0.945)}
    centers = {"C": [origin_x + x["third"], origin_y + y["clear"]],
               "3": [origin_x + x["third"], origin_y + y["123+"]],
               "1": [origin_x + x["left"], origin_y + y["123+"]],
               "4": [origin_x + x["left"], origin_y + y["456"]],
               "+": [origin_x + x["right"], origin_y + y["123+"]],
               "7": [origin_x + x["left"], origin_y + y["789"]],
               "2": [origin_x + x["second"], origin_y + y["123+"]],
               "8": [origin_x + x["second"], origin_y + y["789"]],
               "=": [origin_x + x["right"], origin_y + y["0="]]}
    ops = [{"op": "focus", "target": TARGET_NAME}]
    for label in ("C", "3", "1", "4", "+", "7", "2", "8", "="):
        px, py = centers[label]
        ops.extend([
            {"op": "pointer_move", "frame": "screen_physical_px", "x": px, "y": py},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "pointer_button", "button": "left", "down": False},
        ])
    ops.append({"op": "release_all"})
    return ops, centers


async def main():
    if RUN.exists() and any(RUN.iterdir()):
        raise RuntimeError("run directory already contains data; never reuse an attempt")
    RUN.mkdir(parents=True, exist_ok=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    dpi_aware = bool(user32.SetProcessDPIAware())
    foreground = int(user32.GetForegroundWindow() or 0)
    foreground_root = int(user32.GetAncestor(wintypes.HWND(foreground), 2) or 0)
    if foreground_root != HWND:
        raise RuntimeError("Calculator was not foreground at pre-run; stop without input")
    actual_source = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if actual_source != EXPECTED_SOURCE:
        raise RuntimeError(f"unexpected source commit {actual_source}")
    cond_bytes = (PACKET / "conditions.json").read_bytes()
    metadata = {
        "schema": "win32-public-mcp-calculator-runtime-preflight-v1",
        "attempt_id": ATTEMPT,
        "host": os.environ.get("COMPUTERNAME"),
        "python": sys.version,
        "source_commit": actual_source,
        "conditions_sha256": hashlib.sha256(cond_bytes).hexdigest(),
        "started_unix_ns": time.time_ns(),
        "target_hwnd": HWND,
        "foreground_root": foreground_root,
        "process_dpi_aware_set": dpi_aware,
        "pre_input": True,
    }
    save_json(RUN / "preflight.json", metadata)
    targets = RUN / "targets.json"
    save_json(targets, {TARGET_NAME: HWND})
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(RUN / "server-receipts"),
              "--session-mode", "supervised-win32"],
        cwd=str(ROOT),
    )
    outcome = {"schema": "win32-public-mcp-calculator-run-v1",
               "attempt_id": ATTEMPT, "status": "FAIL_OR_UNKNOWN",
               "steps": [], "source_commit": actual_source,
               "conditions_sha256": metadata["conditions_sha256"]}
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            tools = await client.list_tools()
            names = sorted(tool.name for tool in tools.tools)
            save_json(RUN / "tools.json", {"tool_names": names})
            required = {"interface_clock", "interface_observe", "interface_validate",
                        "interface_dispatch", "interface_results", "interface_close"}
            if not required.issubset(set(names)):
                raise RuntimeError(f"public MCP tools missing: {sorted(required-set(names))}")

            observe_reply = await client.call_tool("interface_observe", {
                "target": TARGET_NAME, "frame": "screen_physical_px",
                "region": list(SCREEN_REGION),
            })
            observe_record = record_reply("observe-0", observe_reply)
            outcome["steps"].append({"name": "observation", **observe_record})
            parsed = observe_record.get("parsed") or {}
            raw_report = (parsed.get("receipt", {}).get("source", {}).get("raw_report")
                          if isinstance(parsed, dict) else None)
            observation = raw_report.get("observation") if isinstance(raw_report, dict) else None
            generation = raw_report.get("target_generation") if isinstance(raw_report, dict) else None
            if (not isinstance(observation, dict)
                    or observation.get("native_window_id") != HWND
                    or observation.get("frame") != "screen_physical_px"
                    or observation.get("region") != list(SCREEN_REGION)
                    or (observation.get("width"), observation.get("height")) != EXPECTED_DIMENSIONS
                    or not isinstance(generation, str) or len(generation) != 64):
                raise RuntimeError("observation target, dimensions, or generation did not match frozen conditions")
            observation_id = raw_report.get("observation_id")
            if not isinstance(observation_id, str):
                raise RuntimeError("observation id missing")
            outcome["observation"] = {
                "observation_id": observation_id,
                "target_generation": generation,
                "native_window_id": observation["native_window_id"],
                "width": observation["width"], "height": observation["height"],
                "region": observation["region"],
                "image_file": next((block["path"] for block in observe_record["blocks"]
                                    if block["type"] == "image"), None),
            }
            save_json(RUN / "paused-before-dispatch.json", outcome)
            print("OBSERVATION_RECORDED", flush=True)
            print("IMAGE", outcome["observation"]["image_file"], flush=True)
            print("Check the saved image and type DISPATCH to proceed, otherwise STOP:",
                  flush=True)
            choice = sys.stdin.readline().strip()
            if choice != "DISPATCH":
                outcome["status"] = "STOPPED_BEFORE_INPUT"
                outcome["stop_reason"] = "operator did not authorize the frozen dispatch after observation review"
                save_json(RUN / "result.json", outcome)
                close = await client.call_tool("interface_close", {})
                outcome["steps"].append({"name": "server_close", **record_reply("close-0", close)})
                save_json(RUN / "result.json", outcome)
                return

            foreground = int(user32.GetForegroundWindow() or 0)
            foreground_root = int(user32.GetAncestor(wintypes.HWND(foreground), 2) or 0)
            if foreground_root != HWND:
                outcome["status"] = "STOPPED_BEFORE_INPUT"
                outcome["stop_reason"] = "Calculator ceased to be foreground before dispatch"
                save_json(RUN / "result.json", outcome)
                close = await client.call_tool("interface_close", {})
                outcome["steps"].append({"name": "server_close", **record_reply("close-0", close)})
                save_json(RUN / "result.json", outcome)
                return

            clock_reply = await client.call_tool("interface_clock", {})
            clock_record = record_reply("clock-0", clock_reply)
            outcome["steps"].append({"name": "clock", **clock_record})
            clock = (clock_record.get("parsed") or {}).get("monotonic_ns")
            if type(clock) is not int:
                raise RuntimeError("caller clock was unavailable; no action dispatched")
            ops, centers = build_ops(*CLIENT_SIZE, *CLIENT_ORIGIN_SCREEN)
            lease_id = uuid4().hex
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": "calc-r05-314plus728",
                "source": {"observation_seq": 1, "binding_revision": 1,
                            "target_generations": {TARGET_NAME: generation}},
                "authority": {"lease_id": lease_id,
                              "expires_at_ns": clock + 45_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": ops,
            }
            save_json(RUN / "program.json", {
                "program": program, "button_centers": centers,
                "note": "Absolute screen coordinates are derived from the frozen fractions over the retained Win32 client geometry and the reviewed screen observation."})
            validation_reply = await client.call_tool("interface_validate", {"program": program})
            validation = record_reply("validation-0", validation_reply)
            outcome["steps"].append({"name": "validation", **validation})
            validation_result = validation.get("parsed") or {}
            if validation_reply.isError or validation_result.get("static_valid") is not True:
                outcome["stop_reason"] = "frozen program failed static validation; no dispatch issued"
                save_json(RUN / "result.json", outcome)
                close = await client.call_tool("interface_close", {})
                outcome["steps"].append({"name": "server_close", **record_reply("close-0", close)})
                save_json(RUN / "result.json", outcome)
                return

            dispatch_started_ns = time.monotonic_ns()
            dispatch_reply = await client.call_tool("interface_dispatch", {
                "program": program, "current_observation_seq": 1,
                "current_binding_revision": 1, "wait_for_result_ms": 10000,
            })
            dispatch_returned_ns = time.monotonic_ns()
            dispatch = record_reply("dispatch-0", dispatch_reply)
            dispatch["client_timing_ns"] = {"started": dispatch_started_ns,
                                             "returned": dispatch_returned_ns}
            outcome["steps"].append({"name": "dispatch", **dispatch})
            report = dispatch.get("parsed") or {}
            call_id = report.get("call_id") if isinstance(report, dict) else None
            action = find_action(report)
            envelope_status = report.get("status") if isinstance(report, dict) else None
            if (dispatch_reply.isError or not isinstance(call_id, str)
                    or len(call_id) != 32 or envelope_status not in ("returned", "pending")):
                outcome["stop_reason"] = "dispatch outcome ambiguous; no replay or recovery"
                save_json(RUN / "result.json", outcome)
            else:
                if envelope_status == "pending":
                    polls = []
                    for index in range(5):
                        retained_reply = await client.call_tool("interface_results", {
                            "call_id": call_id, "include_image": False,
                        })
                        retained = record_reply(f"results-{index}", retained_reply)
                        polls.append(retained)
                        candidate = find_action(retained.get("parsed") or {})
                        if candidate and candidate.get("status") in (
                                "completed", "recovered", "failed", "unknown"):
                            action = candidate
                            report = retained.get("parsed") or {}
                            break
                        await asyncio.sleep(0.25)
                    outcome["steps"].append({"name": "read_only_results", "polls": polls})
                outcome["action"] = action
                outcome["call_id"] = call_id
                outcome["target_generation"] = ((action or {}).get("target_generation")
                                                 or (report.get("target_generation") if isinstance(report, dict) else None))
                outcome["operation_id"] = ((action or {}).get("operation_id")
                                            or (report.get("operation_id") if isinstance(report, dict) else None))
                if (action and action.get("status") == "completed"
                        and action.get("release_confirmed") is True
                        and outcome["target_generation"] == generation):
                    effect_reply = await client.call_tool("interface_observe", {
                        "target": TARGET_NAME, "frame": "screen_physical_px",
                        "region": list(SCREEN_REGION),
                    })
                    effect_record = record_reply("post-action-observe-0", effect_reply)
                    outcome["steps"].append({"name": "post_action_observation",
                                             **effect_record})
                    effect_parsed = effect_record.get("parsed") or {}
                    effect_raw = (effect_parsed.get("receipt", {}).get("source", {}).get("raw_report")
                                  if isinstance(effect_parsed, dict) else None)
                    effect_observation = effect_raw.get("observation") if isinstance(effect_raw, dict) else None
                    if (not effect_reply.isError and isinstance(effect_observation, dict)
                            and effect_observation.get("native_window_id") == HWND
                            and effect_observation.get("frame") == "screen_physical_px"
                            and effect_observation.get("region") == list(SCREEN_REGION)
                            and (effect_observation.get("width"), effect_observation.get("height")) == EXPECTED_DIMENSIONS
                            and effect_raw.get("target_generation") == generation):
                        outcome["post_action_observation"] = {
                            "observation_id": effect_raw.get("observation_id"),
                            "target_generation": effect_raw.get("target_generation"),
                            "image_file": next((block["path"] for block in effect_record["blocks"]
                                                if block["type"] == "image"), None),
                            "app_value_assessment": "pending visual audit",
                        }
                        outcome["status"] = "ACTION_COMPLETED_RELEASE_CONFIRMED_POST_OBSERVED"
                    else:
                        outcome["stop_reason"] = "post-action observation missing, mismatched, or generation changed"
                else:
                    outcome["stop_reason"] = "completion, generation, or release evidence incomplete; no replay"
                save_json(RUN / "result.json", outcome)

            close = await client.call_tool("interface_close", {})
            outcome["steps"].append({"name": "server_close", **record_reply("close-0", close)})
            save_json(RUN / "result.json", outcome)
    print(json.dumps({"attempt_id": ATTEMPT, "status": outcome["status"],
                      "call_id": outcome.get("call_id"),
                      "operation_id": outcome.get("operation_id"),
                      "release_confirmed": (outcome.get("action") or {}).get("release_confirmed")},
                     ensure_ascii=True), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as exc:
        RUN.mkdir(parents=True, exist_ok=True)
        failure_path = RUN / "harness-failure.json"
        if not failure_path.exists():
            save_json(failure_path, {
                "schema": "win32-public-mcp-calculator-harness-failure-v1",
                "attempt_id": ATTEMPT,
                "status": "FAIL_OR_UNKNOWN",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "time_unix_ns": time.time_ns(),
                "prior_output_present": any(path.name != failure_path.name for path in RUN.iterdir()),
            })
        raise
