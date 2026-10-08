"""One local public-MCP stale-refusal plus Chromium effect allocation."""
import asyncio
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import runner as retained


OUT = Path(os.environ.get("OUTPUT_DIR", "/evidence/formal01"))
DISPLAY = ":142"
SOURCE_COMMIT = os.environ["SOURCE_COMMIT"]
IMAGE_ID = os.environ["EXPERIMENT_IMAGE_ID"]
ENV = dict(os.environ, DISPLAY=DISPLAY)
MARKER = "agent-mcp-effect-2907-20260927-01"
TARGET = "chromium"


def save_response(path, result):
    metadata = retained.save_mcp_response(path, result)
    text = [row.text for row in result.content if getattr(row, "type", None) == "text"]
    if len(text) != 1:
        raise AssertionError("EXPECTED_ONE_TEXT_BLOCK")
    payload = json.loads(text[0])
    receipt = payload.get("receipt", {})
    if payload.get("schema") != "agent-interface/review-v1" or receipt.get("schema") != "agent-interface/receipt-view-v1":
        raise AssertionError("PUBLIC_RECEIPT_SCHEMA_MISMATCH")
    raw = receipt.get("source", {}).get("raw_report")
    if not isinstance(raw, dict):
        raise AssertionError("PUBLIC_RAW_REPORT_MISSING")
    return payload, raw, metadata


def program(program_id, sequence, revision, ops):
    return {
        "schema": "agent-interface/program-v1",
        "program_id": program_id,
        "source": {"observation_seq": sequence, "binding_revision": revision},
        "authority": {"lease_id": "local-fixture-lease-" + program_id,
                      "expires_at_ns": time.monotonic_ns() + 120_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": ops + [{"op": "release_all"}],
    }


async def execute_mcp(targets, html_path):
    params = StdioServerParameters(
        command="python3",
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(OUT / "targets.json"),
              "--output-directory", str(OUT / "server-receipts"), "--display", DISPLAY,
              "--session-mode", "persistent-x11"],
        env=ENV,
        cwd="/opt/importroot",
    )
    trace = {"session_mode": "persistent-x11", "target": TARGET, "calls": []}
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            initialized = await client.initialize()
            listed = await client.list_tools()
            tools = sorted(tool.name for tool in listed.tools)
            required = {"interface_observe", "interface_dispatch", "interface_close", "interface_results"}
            trace["protocol_version"] = initialized.protocolVersion
            trace["tools"] = tools
            if not required.issubset(tools):
                raise AssertionError("PUBLIC_MCP_TOOL_SET_INCOMPLETE")

            async def call(label, name, args):
                response = await client.call_tool(name, args)
                response_file = OUT / "mcp-responses" / (label + ".json")
                payload, raw, metadata = save_response(response_file, response)
                record = {"label": label, "tool": name, "response_file": response_file.name,
                          "is_error": bool(response.isError), "payload": payload, "raw_report": raw,
                          "response_metadata": metadata}
                trace["calls"].append(record)
                return record

            observed1 = await call("01-observe-seq1", "interface_observe", {
                "target": TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed1["payload"].get("receipt", {}).get("source", {}).get("raw_report", {}).get("status") != "returned":
                raise AssertionError("FIRST_OBSERVATION_NOT_RETURNED")
            trace["session_id"] = observed1["payload"].get("session", {}).get("session_id")
            trace["binding_revision"] = observed1["payload"].get("session", {}).get("binding_revision")

            observed2 = await call("02-observe-seq2", "interface_observe", {
                "target": TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed2["payload"].get("session", {}).get("session_id") != trace["session_id"]:
                raise AssertionError("SESSION_CHANGED_BETWEEN_OBSERVATIONS")
            trace["observation_sequences"] = [1, 2]

            stale_program = program("stale-f6", 1, trace["binding_revision"],
                                    [{"op": "focus", "target": TARGET},
                                     {"op": "key_chord", "keys": ["F6"]}])
            stale = await call("03-stale-dispatch", "interface_dispatch", {
                "program": stale_program, "current_observation_seq": 2,
                "current_binding_revision": trace["binding_revision"]})
            stale_result = stale["raw_report"].get("result", {})
            trace["stale_gate"] = {
                "reported_status": stale_result.get("status"),
                "error": stale_result.get("error"),
                "backend_emissions": stale_result.get("backend_emissions"),
                "input_dispatched": stale["raw_report"].get("input_dispatched"),
                "program_source_sequence": 1, "caller_current_sequence": 2,
            }
            if (stale_result.get("status") != "refused" or
                    stale_result.get("error") != "STALE_OBSERVATION" or
                    stale_result.get("backend_emissions") != 0):
                trace["decision"] = "FAIL_STALE_OBSERVATION_NOT_REFUSED"
                return trace

            url = html_path.resolve().as_uri()
            action_program = program("fresh-local-file-navigation", 2, trace["binding_revision"], [
                {"op": "focus", "target": TARGET},
                {"op": "key_chord", "keys": ["CTRL", "l"]},
                {"op": "text", "text": url},
                {"op": "key_chord", "keys": ["ENTER"]},
            ])
            action = await call("04-fresh-dispatch", "interface_dispatch", {
                "program": action_program, "current_observation_seq": 2,
                "current_binding_revision": trace["binding_revision"]})
            action_result = action["raw_report"].get("result", {})
            execution = action_result.get("execution", {})
            trace["action"] = {
                "status": action_result.get("status"), "error": action_result.get("error"),
                "input_dispatched": action["raw_report"].get("input_dispatched"),
                "releases": execution.get("releases", []),
                "program_emissions": execution.get("program_emissions"),
                "source_sequence": 2, "binding_revision": trace["binding_revision"],
            }
            if action_result.get("status") != "completed":
                trace["decision"] = "FAIL_FRESH_DISPATCH_NOT_COMPLETED"
                return trace

            deadline = time.monotonic() + 15
            title_result = None
            while time.monotonic() < deadline:
                prop = subprocess.run(["xprop", "-id", str(targets[TARGET]), "WM_NAME"],
                                      env=ENV, text=True, capture_output=True, check=False)
                title_result = prop.stdout.strip()
                if MARKER in title_result:
                    break
                time.sleep(.2)
            trace["effect_receipt"] = {"window_id": targets[TARGET], "wm_name": title_result,
                                       "marker": MARKER, "matched": MARKER in (title_result or "")}
            observed3 = await call("05-post-effect-observe", "interface_observe", {
                "target": TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed3["payload"].get("session", {}).get("session_id") != trace["session_id"]:
                raise AssertionError("SESSION_CHANGED_AFTER_EFFECT")
            close = await call("06-close", "interface_close", {})
            trace["close"] = close["raw_report"]
            if (not trace["effect_receipt"]["matched"] or close["raw_report"].get("status") != "closed" or
                    close["raw_report"].get("release_attempted") is not True):
                trace["decision"] = "FAIL_EFFECT_OR_NEUTRAL_CLOSE"
                return trace
            retained_reads = []
            for record in list(trace["calls"]):
                read = await client.call_tool("interface_results", {
                    "call_id": record["payload"].get("call_id"), "include_image": False})
                path = OUT / "mcp-responses" / ("retained-" + record["label"] + ".json")
                payload, raw, metadata = save_response(path, read)
                retained_reads.append({"source_label": record["label"],
                                       "response_file": path.name,
                                       "operation_invoked": payload.get("operation_invoked"),
                                       "state": payload.get("retained_call", {}).get("state"),
                                       "session_id": payload.get("session", {}).get("session_id"),
                                       "metadata": metadata})
            trace["retained_reads"] = retained_reads
            trace["decision"] = "PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED"
    return trace


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "mcp-responses").mkdir()
    (OUT / "server-receipts").mkdir()
    (OUT / "fixtures").mkdir()
    html_path = OUT / "fixtures" / (MARKER + ".html")
    html_path.write_text(
        "<!doctype html><title>" + MARKER +
        "</title><body style='background:#19c55b'><h1>" + MARKER + "</h1></body>",
        encoding="ascii")
    display = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wm = None
    app = None
    outcome = {"decision": "STOP_BEFORE_MCP", "input_operations": 0,
               "model_calls": 0, "network_calls": 0, "authority_granted": False}
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not Path("/tmp/.X11-unix/X142").exists():
            time.sleep(.05)
        if not Path("/tmp/.X11-unix/X142").exists():
            raise RuntimeError("XVFB_NOT_READY")
        wm = subprocess.Popen(["openbox", "--replace"], env=ENV,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(.5)
        _, chrome_args, class_hint = next(row for row in retained.APPS if row[0] == TARGET)
        app, identity = retained.launch_owned(TARGET, chrome_args, class_hint)
        targets = {TARGET: identity["window_id"]}
        retained.write_json(OUT / "app-identities.json", [identity])
        retained.write_json(OUT / "targets.json", targets)
        retained.write_json(OUT / "environment.json", {
            "source_commit": SOURCE_COMMIT, "image_id": IMAGE_ID,
            "platform": "linux/amd64", "display": DISPLAY,
            "base_image_id": "sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3",
            "model_calls": 0, "network_calls": 0,
        })
        trace = asyncio.run(execute_mcp(targets, html_path))
        retained.write_json(OUT / "trace.json", trace)
        outcome.update(decision=trace.get("decision", "HOLD_INCOMPLETE_TRACE"),
                       trace_file="trace.json", session_id=trace.get("session_id"),
                       input_operations=(trace.get("action") or {}).get("program_emissions", 0),
                       stale_gate=trace.get("stale_gate"), action=trace.get("action"),
                       effect_receipt=trace.get("effect_receipt"), close=trace.get("close"))
    except Exception as error:
        outcome.update(decision="STOP_OR_FAIL_CALLER", error=repr(error))
    finally:
        cleanup = []
        for proc in (app, wm, display):
            if proc is None:
                continue
            cleanup.append({"pid": proc.pid, **retained.terminate_tree(proc.pid)})
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        outcome["cleanup"] = cleanup
        outcome["server_processes_after_shutdown"] = retained.server_processes()
        outcome["x_socket_absent"] = not Path("/tmp/.X11-unix/X142").exists()
        retained.write_json(OUT / "result.json", outcome)
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["decision"] == "PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED" and outcome["x_socket_absent"] and not outcome["server_processes_after_shutdown"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
