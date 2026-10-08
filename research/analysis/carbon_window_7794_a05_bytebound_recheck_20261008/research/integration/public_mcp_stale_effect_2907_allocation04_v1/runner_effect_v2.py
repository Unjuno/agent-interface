"""Fresh successor caller for allocation 02; allocation 01 remains untouched."""
import json
from pathlib import Path

import runner_effect as base


MARKER = "agent-mcp-effect-2907-20260927-02"
base.MARKER = MARKER
OUT = base.OUT


def decode_payload(text):
    payload = json.loads(text)
    if (payload.get("schema") == "agent-interface/review-v1"
            and payload.get("receipt", {}).get("schema") == "agent-interface/receipt-view-v1"):
        raw = payload.get("receipt", {}).get("source", {}).get("raw_report")
        if not isinstance(raw, dict):
            raise AssertionError("PUBLIC_RAW_REPORT_MISSING")
        return payload, raw
    if isinstance(payload, dict) and isinstance(payload.get("status"), str) and "session_id" in payload:
        return payload, payload
    raise AssertionError("UNKNOWN_PUBLIC_RESPONSE_SCHEMA")


def save_response(path, result):
    metadata = base.retained.save_mcp_response(path, result)
    text = [row.text for row in result.content if getattr(row, "type", None) == "text"]
    if len(text) != 1:
        raise AssertionError("EXPECTED_ONE_TEXT_BLOCK")
    payload, raw = decode_payload(text[0])
    return payload, raw, metadata


base.save_response = save_response


def persist_effect_receipt(targets):
    deadline = base.time.monotonic() + 15
    title_result = None
    while base.time.monotonic() < deadline:
        prop = base.subprocess.run(["xprop", "-id", str(targets[base.TARGET]), "WM_NAME"],
                                   env=base.ENV, text=True, capture_output=True, check=False)
        title_result = prop.stdout.strip()
        if MARKER in title_result:
            break
        base.time.sleep(.2)
    receipt = {"window_id": targets[base.TARGET], "wm_name": title_result,
               "marker": MARKER, "matched": MARKER in (title_result or "")}
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode() + b"\n"
    (OUT / "effect_receipt.json").write_bytes(raw)
    return receipt


async def execute_mcp_v2(targets, html_path):
    params = base.StdioServerParameters(
        command="python3",
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(OUT / "targets.json"),
              "--output-directory", str(OUT / "server-receipts"), "--display", base.DISPLAY,
              "--session-mode", "persistent-x11"],
        env=base.ENV,
        cwd="/opt/importroot",
    )
    trace = {"session_mode": "persistent-x11", "target": base.TARGET, "calls": []}
    async with base.stdio_client(params) as (read_stream, write_stream):
        async with base.ClientSession(read_stream, write_stream) as client:
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
                "target": base.TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed1["raw_report"].get("status") != "returned":
                raise AssertionError("FIRST_OBSERVATION_NOT_RETURNED")
            trace["session_id"] = observed1["payload"].get("session", {}).get("session_id")
            trace["binding_revision"] = observed1["payload"].get("session", {}).get("binding_revision")
            observed2 = await call("02-observe-seq2", "interface_observe", {
                "target": base.TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed2["payload"].get("session", {}).get("session_id") != trace["session_id"]:
                raise AssertionError("SESSION_CHANGED_BETWEEN_OBSERVATIONS")
            trace["observation_sequences"] = [1, 2]

            stale_program = base.program("stale-f6", 1, trace["binding_revision"], [
                {"op": "focus", "target": base.TARGET}, {"op": "key_chord", "keys": ["F6"]}])
            stale = await call("03-stale-dispatch", "interface_dispatch", {
                "program": stale_program, "current_observation_seq": 2,
                "current_binding_revision": trace["binding_revision"]})
            stale_result = stale["raw_report"].get("result", {})
            trace["stale_gate"] = {
                "reported_status": stale_result.get("status"), "error": stale_result.get("error"),
                "backend_emissions": stale_result.get("backend_emissions"),
                "input_dispatched": stale["raw_report"].get("input_dispatched"),
                "program_source_sequence": 1, "caller_current_sequence": 2}
            if (stale_result.get("status") != "refused" or stale_result.get("error") != "STALE_OBSERVATION"
                    or stale_result.get("backend_emissions") != 0):
                trace["decision"] = "FAIL_STALE_OBSERVATION_NOT_REFUSED"
                return trace

            url = html_path.resolve().as_uri()
            action_program = base.program("fresh-local-file-navigation", 2, trace["binding_revision"], [
                {"op": "focus", "target": base.TARGET}, {"op": "key_chord", "keys": ["CTRL", "l"]},
                {"op": "text", "text": url}, {"op": "key_chord", "keys": ["ENTER"]}])
            action = await call("04-fresh-dispatch", "interface_dispatch", {
                "program": action_program, "current_observation_seq": 2,
                "current_binding_revision": trace["binding_revision"]})
            action_result = action["raw_report"].get("result", {})
            execution = action_result.get("execution", {})
            trace["action"] = {"status": action_result.get("status"), "error": action_result.get("error"),
                "input_dispatched": action["raw_report"].get("input_dispatched"),
                "releases": execution.get("releases", []), "program_emissions": execution.get("program_emissions"),
                "source_sequence": 2, "binding_revision": trace["binding_revision"]}
            if action_result.get("status") != "completed":
                trace["decision"] = "FAIL_FRESH_DISPATCH_NOT_COMPLETED"
                return trace

            trace["effect_receipt"] = persist_effect_receipt(targets)
            if not trace["effect_receipt"]["matched"]:
                trace["decision"] = "FAIL_EFFECT_NOT_OBSERVED"
                return trace
            observed3 = await call("05-post-effect-observe", "interface_observe", {
                "target": base.TARGET, "frame": "window_client", "region": [0, 0, 128, 96]})
            if observed3["payload"].get("session", {}).get("session_id") != trace["session_id"]:
                raise AssertionError("SESSION_CHANGED_AFTER_EFFECT")
            close = await call("06-close", "interface_close", {})
            trace["close"] = close["raw_report"]
            if (not trace["effect_receipt"]["matched"] or close["raw_report"].get("status") != "closed"
                    or close["raw_report"].get("release_attempted") is not True):
                trace["decision"] = "FAIL_EFFECT_OR_NEUTRAL_CLOSE"
                return trace

            retained_reads = []
            for record in list(trace["calls"]):
                read = await client.call_tool("interface_results", {
                    "call_id": record["payload"].get("call_id"), "include_image": False})
                path = OUT / "mcp-responses" / ("retained-" + record["label"] + ".json")
                payload, _raw, metadata = save_response(path, read)
                record["retained_response_file"] = path.name
                record["retained_payload"] = payload
                record["retained_response_metadata"] = metadata
                retained_reads.append({"source_label": record["label"], "response_file": path.name,
                    "operation_invoked": payload.get("operation_invoked"),
                    "state": payload.get("retained_call", {}).get("state"),
                    "session_id": payload.get("session", {}).get("session_id"), "metadata": metadata})
            trace["retained_reads"] = retained_reads
            trace["decision"] = "PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED"
    return trace


def main():
    base.execute_mcp = execute_mcp_v2
    old_write_json = base.retained.write_json

    def persist_trace(path, value):
        if path.name == "trace.json" and value.get("effect_receipt"):
            effect_bytes = json.dumps(value["effect_receipt"], sort_keys=True,
                                      indent=2, ensure_ascii=False).encode() + b"\n"
            (OUT / "effect_receipt.json").write_bytes(effect_bytes)
        return old_write_json(path, value)

    base.retained.write_json = persist_trace
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())

