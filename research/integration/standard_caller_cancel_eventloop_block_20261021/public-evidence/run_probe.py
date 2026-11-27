"""Measure synchronous cancellation stalls through the public Fake X caller."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import multiprocessing
import sys
import re
import time
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from runtime.cli_v1.test_mcp_process_identity import metadata
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


async def _wait_for(path: Path, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return True
        await asyncio.sleep(0.005)
    return path.exists()


async def _one_trial(arm: str, delay_ms: int, index: int,
                     runs_root: Path, run_id: str) -> dict:
    trial_id = f"{arm}-{index:02d}"
    root = runs_root / run_id / trial_id
    root.mkdir(parents=True, exist_ok=False)
    server = create_server(
        {"app": 20}, root, session_mode="guarded-x11",
        guarded_process_identity=True, guarded_query_worker=True,
        guarded_owned_process=True, _guarded_owner_factory=_fake_owner_factory,
    )
    heartbeat_ns = []
    stop_heartbeat = asyncio.Event()
    heartbeat_task = None
    pending = None
    start_ns = returned_ns = None
    cancel = None
    terminal = None

    async def heartbeat():
        while not stop_heartbeat.is_set():
            heartbeat_ns.append(time.monotonic_ns())
            await asyncio.sleep(0.01)

    def persist(name, value):
        (root / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8", newline="\n")

    try:
        observation = metadata(await server.call_tool("interface_guarded_observe", {}))
        minted = metadata(await server.call_tool("interface_guarded_mint", {
            "alias": "field", "source_sequence": observation["source"]["sequence"],
            "point": [8, 8], "region_size": [12, 12],
        }))
        (root / "block-owner-io").write_text("block", encoding="utf-8")
        pending = metadata(await server.call_tool("interface_guarded_input", {
            "alias": "field", "offset": minted["offset"],
            "interaction": "keyboard", "observe_after": False,
            "wait_for_result_ms": 0,
            "tail": [{"op": "key_chord", "keys": ["CTRL", "a"]}],
        }))
        persist("pending.json", pending)
        if pending.get("status") != "pending":
            raise AssertionError("expected pending standard caller result: " + repr(pending))
        if not await _wait_for(root / "owner-io-entered.json", 3.0):
            raise AssertionError("Fake X owner did not reach injected blocked sync")

        fence = {"status": "disconnected", "worker_retired": True, "elapsed_ms": 1.0}
        release = {"status": "unknown", "reason": "injected_fake_x_boundary",
                   "worker_retired": True}

        def disconnect_boundary(*_args, **_kwargs):
            if delay_ms:
                time.sleep(delay_ms / 1000.0)
            return dict(fence)

        def release_boundary(_owner, obligations):
            if obligations != {"keys": {"CTRL": 1}, "buttons": []}:
                raise AssertionError("unexpected owner obligations: " + repr(obligations))
            if delay_ms:
                time.sleep(delay_ms / 1000.0)
            return dict(release)

        heartbeat_task = asyncio.create_task(heartbeat())
        await asyncio.sleep(0.035)
        start_ns = time.monotonic_ns()
        with (patch(
                "runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised",
                side_effect=disconnect_boundary),
              patch.object(OwnedGuardedSessionOwner,
                           "_release_retired_owner_inputs", new=release_boundary)):
            cancel = metadata(await server.call_tool(
                "interface_guarded_cancel", {"call_id": pending["call_id"]}))
        returned_ns = time.monotonic_ns()
        persist("cancel-response.json", cancel)
        if cancel.get("status") == "not_active":
            raise AssertionError("public caller did not admit cancellation for active call")

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            terminal = metadata(await server.call_tool("interface_results", {
                "call_id": pending["call_id"], "include_image": False,
            }))
            if terminal.get("status") != "pending":
                break
            await asyncio.sleep(0.01)
        persist("terminal-call.json", terminal)
        event_times = heartbeat_ns + [start_ns, returned_ns]
        event_times.sort()
        gaps_ms = [(right - left) / 1_000_000
                   for left, right in zip(event_times, event_times[1:])]
        record = {
            "trial_id": trial_id, "arm": arm,
            "injected_delay_each_boundary_ms": delay_ms,
            "cancel_started_ns": start_ns, "cancel_returned_ns": returned_ns,
            "cancel_tool_elapsed_ms": (returned_ns - start_ns) / 1_000_000,
            "heartbeat_count": len(heartbeat_ns),
            "max_event_loop_gap_ms": max(gaps_ms, default=0.0),
            "cancel": cancel, "terminal_call": terminal,
            "owner_input_obligations": json.loads(
                (root / "owner-io-entered.json").read_text(encoding="utf-8")),
            "evidence_directory": str(root),
        }
        persist("trial.json", record)
        return record
    finally:
        stop_heartbeat.set()
        if heartbeat_task is not None and not heartbeat_task.done():
            await heartbeat_task
        (root / "resume-owner-io").write_text("resume", encoding="utf-8")
        close = metadata(await server.call_tool("interface_close", {}))
        persist("close-response.json", close)


async def run(run_id: str) -> dict:
    conditions = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
    rows = []
    failures = []
    runs_root = HERE / "raw" / "trials"
    for arm, record in conditions["arms"].items():
        for index in range(1, record["trials"] + 1):
            try:
                rows.append(await _one_trial(
                    arm, record["delay_each_cleanup_boundary_ms"], index,
                    runs_root, run_id))
            except Exception as error:
                failures.append(f"{arm}-{index:02d}: {type(error).__name__}: {error!r}")
                rows.append({"trial_id": f"{arm}-{index:02d}", "arm": arm,
                             "status": "incomplete", "error": repr(error)})
    for row in rows:
        if row.get("status") == "incomplete":
            continue
        cancel = row["cancel"]
        if (cancel.get("release_confirmed") is not False
                or cancel.get("cleanup_status") != "UNKNOWN"
                or cancel.get("task_success") is not None
                or cancel.get("replay_allowed") is not False):
            failures.append(row["trial_id"] + ": cancellation uncertainty contract changed")
        if row["terminal_call"].get("status") == "pending":
            failures.append(row["trial_id"] + ": terminal standard caller result stayed pending")
    delayed = [r for r in rows if r["arm"] == "injected-cleanup-boundary-delay"
               and "cancel_tool_elapsed_ms" in r]
    baseline = [r for r in rows if r["arm"] == "no-injected-cleanup-delay"
                and "cancel_tool_elapsed_ms" in r]
    if len(rows) != 6 or len(delayed) != 3 or len(baseline) != 3:
        failures.append("trial count mismatch")
    if delayed and baseline and not (
            min(r["cancel_tool_elapsed_ms"] for r in delayed)
            > max(r["cancel_tool_elapsed_ms"] for r in baseline)):
        failures.append("injected cleanup delay did not separate cancel latency arms")
    return {
        "schema": "agent-interface/standard-caller-cancel-eventloop-result-v1",
        "run_id": run_id,
        "conditions_sha256": hashlib.sha256(
            (HERE / "conditions.json").read_bytes()).hexdigest(),
        "runtime": {"python": __import__("sys").version,
                    "platform": __import__("platform").platform(),
                    "clock": "time.monotonic_ns"},
        "audit": {"status": "PASS" if not failures else "FAIL",
                  "failures": failures,
                  "meaning": "method-scoped observation of the current composed route; PASS is not a product safety qualification"},
        "trials": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", args.run_id):
        raise SystemExit("run-id must use 1-32 letters, digits, hyphens or underscores")
    result = asyncio.run(run(args.run_id))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["audit"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
