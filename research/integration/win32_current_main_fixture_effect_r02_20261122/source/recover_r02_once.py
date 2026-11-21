"""Perform exactly one evidence-bound recovery for the retained R01 action."""

import asyncio
import hashlib
import json
import sys
import time
from datetime import timedelta, datetime, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


REPO = Path(sys.argv[1]).resolve()
PACKET = Path(sys.argv[2]).resolve()
RAW = PACKET / "raw"
RECOVERY = RAW / "recovery"
DISPATCH_CALL = "5ff9e53fbf44464ebaa0916d3425c6a7"
DISPATCH_REPORT = RAW / "mcp" / DISPATCH_CALL / "report.json"
PRODUCER_REPORT = (RAW / "mcp" / "supervised-win32-producers" /
                   DISPATCH_CALL / "producer-result.json")
ABSENCE_REPORT = RECOVERY / "producer-absence.json"


def save_result(name, result):
    value = result.model_dump(mode="json", exclude_none=True)
    (RECOVERY / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def first_json(value):
    for block in value.get("content", []):
        if block.get("type") == "text":
            try:
                decoded = json.loads(block["text"])
            except (TypeError, ValueError):
                continue
            if isinstance(decoded, dict):
                return decoded
    return None


def is_terminal(value):
    if not isinstance(value, dict) or value.get("status") == "pending":
        return False
    action = value.get("action")
    if isinstance(action, dict):
        return action.get("status") in ("completed", "recovered", "unknown")
    return value.get("status") in (
        "returned", "recovered", "unknown", "runtime_failed",
        "receipt_unavailable")


async def main():
    dispatch = json.loads(DISPATCH_REPORT.read_text(encoding="utf-8-sig"))
    producer = json.loads(PRODUCER_REPORT.read_text(encoding="utf-8-sig"))
    absence = json.loads(ABSENCE_REPORT.read_text(encoding="utf-8-sig"))
    if absence.get("exact_producer_absent") is not True:
        raise RuntimeError("exact producer absence is not established")
    if dispatch.get("status") != "returned" or dispatch.get("operation_id") != "29e90d7cf3c54ed4b36136a424a9f77b":
        raise RuntimeError("retained dispatch receipt identity mismatch")
    supervision = dispatch.get("supervision", {})
    action = supervision.get("action", {})
    cancellation = supervision.get("cancellation", {})
    result = cancellation.get("result", {})
    obligations = result.get("obligations")
    if (action.get("status") != "unknown" or
            action.get("operation_id") != dispatch["operation_id"] or
            action.get("target_generation") != dispatch["target_generation"] or
            result.get("status") != "unknown" or
            result.get("release_confirmed") is not False or
            not isinstance(obligations, list) or
            obligations != ["key:fixture:A:virtual_key"] or
            producer.get("operation_id") != dispatch["operation_id"] or
            producer.get("target_generation") != dispatch["target_generation"]):
        raise RuntimeError("retained action/producer custody evidence mismatch")

    dispatch_bytes = DISPATCH_REPORT.read_bytes()
    producer_bytes = PRODUCER_REPORT.read_bytes()
    identity = result.get("producer_identity")
    if (type(identity) is not dict or
            identity.get("pid") != absence.get("expected_pid") or
            str(identity.get("creation_time_100ns")) !=
            absence.get("expected_creation_time_100ns")):
        raise RuntimeError("producer-absence check does not bind exact receipt identity")
    custody = {
        "classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
        "operation_id": dispatch["operation_id"],
        "target_generation": dispatch["target_generation"],
        "obligations": obligations,
        "do_not_replay": True,
        "observed_producer_live": False,
        "late_server_request_possible": not (
            type(result.get("late_input_horizon_ns")) is int and
            result.get("late_input_horizon_ns", 0) > 0 and
            result.get("late_input_max_sample_gap_ns") is not None and
            result.get("late_input_observation_count", 0) > 0),
        "dispatch": {
            "input_dispatched": dispatch.get("input_dispatched"),
            "release_confirmed": dispatch.get("release_confirmed"),
            "task_success": dispatch.get("task_success"),
            "replay_allowed": dispatch.get("replay_allowed"),
        },
        "producer_identity": identity,
        "producer_absence_check": absence,
        "source_dispatch_report_sha256": hashlib.sha256(dispatch_bytes).hexdigest(),
        "source_producer_report_sha256": hashlib.sha256(producer_bytes).hexdigest(),
    }
    if (custody["late_server_request_possible"] is not True or
            custody["dispatch"] != {
                "input_dispatched": None, "release_confirmed": False,
                "task_success": None, "replay_allowed": False}):
        raise RuntimeError("source custody classification is not the frozen UNKNOWN case")
    (RECOVERY / "source-custody-record.json").write_text(
        json.dumps(custody, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")

    targets = RAW / "targets.json"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(RECOVERY / "mcp"),
              "--session-mode", "supervised-win32",
              "--supervised-win32-late-input-horizon-ms", "2000"],
        cwd=str(REPO))
    summary = {"recovery_attempts": 0, "source_operation_id": dispatch["operation_id"],
               "source_target_generation": dispatch["target_generation"],
               "producer_absent": True, "started_at_utc": datetime.now(
                   timezone.utc).isoformat()}
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer,
                                 read_timeout_seconds=timedelta(seconds=50)) as client:
            init = await client.initialize()
            (RECOVERY / "initialize.json").write_text(
                json.dumps(init.model_dump(mode="json", exclude_none=True),
                           ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            observed = await client.call_tool("interface_observe", {
                "target": "fixture", "frame": "screen_physical_px",
                "region": [80, 80, 420, 220]})
            observed_raw = save_result("observation.json", observed)
            observed_view = first_json(observed_raw)
            observed_body = (observed_view.get("receipt", {}).get("source", {}).get(
                "raw_report") if isinstance(observed_view, dict) and
                observed_view.get("schema") == "agent-interface/review-v1"
                else observed_view)
            if (not observed_body or observed_body.get("status") != "returned" or
                    observed_body.get("target_generation_consistency") != "matched" or
                    type(observed_body.get("target_generation")) is not str):
                summary["observation"] = observed_view
                summary["final"] = "STOP_FRESH_RECOVERY_OBSERVATION_NOT_VERIFIED"
                (RECOVERY / "summary-r02.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
                print(json.dumps(summary, ensure_ascii=False, indent=2))
                return
            recovery_generation = observed_body["target_generation"]
            (RECOVERY / "recovery-request.json").write_text(json.dumps({
                "tool": "interface_recover_orphaned_input",
                "source_operation_id": dispatch["operation_id"],
                "source_target_generation": dispatch["target_generation"],
                "recovery_target_generation": recovery_generation,
                "obligations": obligations,
                "source_custody_record": custody,
                "retry_count": 0,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            reply = await client.call_tool("interface_recover_orphaned_input", {
                "source_operation_id": dispatch["operation_id"],
                "source_target_generation": dispatch["target_generation"],
                "recovery_target_generation": recovery_generation,
                "obligations": obligations,
                "source_custody_record": custody})
            summary["recovery_attempts"] = 1
            raw = save_result("recovery.json", reply)
            body = first_json(raw)
            if not body:
                raise RuntimeError("orphan recovery response is not parseable")
            call_id = body.get("call_id")
            deadline = time.monotonic() + 45
            polls = []
            while (not is_terminal(body) and isinstance(call_id, str) and
                   time.monotonic() < deadline):
                await asyncio.sleep(0.25)
                query = await client.call_tool("interface_results", {
                    "call_id": call_id, "include_image": False})
                query_raw = save_result(f"recovery-poll-{len(polls)+1:02d}.json", query)
                query_body = first_json(query_raw)
                polls.append(query_body)
                if query_body and is_terminal(query_body):
                    body = query_body
            summary["recovery_generation"] = recovery_generation
            summary["recovery_result"] = body
            summary["recovery_poll_count"] = len(polls)
            action = body.get("action") if isinstance(body, dict) else None
            recovery_result = (action.get("result") if isinstance(action, dict)
                               else body)
            recovery_status = (action.get("status") if isinstance(action, dict)
                               else recovery_result.get("status"))
            release_confirmed = (body.get("release_confirmed") is True or
                                 (isinstance(recovery_result, dict) and
                                  recovery_result.get("release_confirmed") is True))
            if (recovery_status in ("recovered", "completed") and
                    release_confirmed):
                closed = await client.call_tool("interface_close", {})
                summary["close"] = first_json(save_result("close.json", closed))
            else:
                summary["close"] = "not_called: recovery did not confirm release"
            summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            (RECOVERY / "summary-r02.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            print(json.dumps(summary, ensure_ascii=False, indent=2))


asyncio.run(main())


