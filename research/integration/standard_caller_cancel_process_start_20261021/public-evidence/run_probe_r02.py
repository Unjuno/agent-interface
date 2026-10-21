"""Exercise real spawn startup through public MCP cancellation on Fake X."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import multiprocessing
import re
import sys
import time
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from runtime.cli_v1.test_mcp_process_identity import metadata
from runtime.guarded_x11_v1 import xres_client_fence


def _fake_disconnect_worker(send):
    send.send({"status": "disconnected"})


def _fake_unknown_release_worker(send):
    send.send({"status": "unknown", "release": None})


class _DelayedProcess:
    def __init__(self, process, delay_ms, receipts, label):
        self._process = process
        self._delay_ms = delay_ms
        self._receipts = receipts
        self._label = label

    def start(self):
        requested_ns = time.monotonic_ns()
        if self._delay_ms:
            time.sleep(self._delay_ms / 1000.0)
        real_start_ns = time.monotonic_ns()
        try:
            result = self._process.start()
        except BaseException as error:
            self._receipts.append({
                "label": self._label, "requested_ns": requested_ns,
                "real_start_ns": real_start_ns, "returned_ns": time.monotonic_ns(),
                "delay_ms": self._delay_ms, "error": repr(error),
            })
            raise
        self._receipts.append({
            "label": self._label, "requested_ns": requested_ns,
            "real_start_ns": real_start_ns, "returned_ns": time.monotonic_ns(),
            "delay_ms": self._delay_ms, "pid": self._process.pid,
        })
        return result

    def __getattr__(self, name):
        return getattr(self._process, name)


class _DelayedContext:
    def __init__(self, context, delay_ms, receipts):
        self._context = context
        self._delay_ms = delay_ms
        self._receipts = receipts
        self._next_label = 0

    def Process(self, *args, **kwargs):
        self._next_label += 1
        label = "helper-%02d" % self._next_label
        process = self._context.Process(*args, **kwargs)
        return _DelayedProcess(process, self._delay_ms, self._receipts, label)

    def __getattr__(self, name):
        return getattr(self._context, name)


async def _wait_for(path: Path, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return True
        await asyncio.sleep(0.005)
    return path.exists()


def _persist(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


async def _one_trial(run_id: str, arm: str, delay_ms: int, index: int,
                     runs_root: Path, original_get_context) -> dict:
    trial_id = "%s-%02d" % (arm, index)
    root = runs_root / run_id / trial_id
    root.mkdir(parents=True, exist_ok=False)
    server = create_server(
        {"app": 20}, root, session_mode="guarded-x11",
        guarded_process_identity=True, guarded_query_worker=True,
        guarded_owned_process=True, _guarded_owner_factory=_fake_owner_factory,
    )
    heartbeat_ns = []
    start_receipts = []
    stop_heartbeat = asyncio.Event()
    heartbeat_task = None
    cancel = None
    terminal = None

    async def heartbeat():
        while not stop_heartbeat.is_set():
            heartbeat_ns.append(time.monotonic_ns())
            await asyncio.sleep(0.01)

    def delayed_get_context(method=None):
        return _DelayedContext(original_get_context(method), delay_ms, start_receipts)

    def synthetic_disconnect(*_args, **kwargs):
        return xres_client_fence.supervise_xres_worker(
            _fake_disconnect_worker, (), timeout_s=kwargs["timeout_s"],
            terminate_grace_s=kwargs["terminate_grace_s"],
            accepted_statuses=("disconnected",),
        )

    def synthetic_release(_target, _args, **kwargs):
        return xres_client_fence.supervise_xres_worker(
            _fake_unknown_release_worker, (), timeout_s=kwargs["timeout_s"],
            terminate_grace_s=kwargs["terminate_grace_s"],
            accepted_statuses=kwargs["accepted_statuses"],
        )

    try:
        observed = metadata(await server.call_tool("interface_guarded_observe", {}))
        minted = metadata(await server.call_tool("interface_guarded_mint", {
            "alias": "field", "source_sequence": observed["source"]["sequence"],
            "point": [8, 8], "region_size": [12, 12],
        }))
        (root / "block-owner-io").write_text("block", encoding="utf-8")
        pending = metadata(await server.call_tool("interface_guarded_input", {
            "alias": "field", "offset": minted["offset"],
            "interaction": "keyboard", "observe_after": False,
            "wait_for_result_ms": 0,
            "tail": [{"op": "key_chord", "keys": ["CTRL", "a"]}],
        }))
        _persist(root / "pending.json", pending)
        if pending.get("status") != "pending":
            raise AssertionError("expected pending standard caller result: " + repr(pending))
        if not await _wait_for(root / "owner-io-entered.json", 3.0):
            raise AssertionError("Fake X owner did not reach blocked sync")

        heartbeat_task = asyncio.create_task(heartbeat())
        await asyncio.sleep(0.035)
        started_ns = time.monotonic_ns()
        with (patch.object(multiprocessing, "get_context", new=delayed_get_context),
              patch("runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised",
                    side_effect=synthetic_disconnect),
              patch("runtime.cli_v1.owned_guarded_session.supervise_xres_worker",
                    side_effect=synthetic_release)):
            cancel = metadata(await server.call_tool(
                "interface_guarded_cancel", {"call_id": pending["call_id"]}))
        returned_ns = time.monotonic_ns()
        _persist(root / "cancel-response.json", cancel)

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            terminal = metadata(await server.call_tool("interface_results", {
                "call_id": pending["call_id"], "include_image": False,
            }))
            if terminal.get("status") != "pending":
                break
            await asyncio.sleep(0.01)
        _persist(root / "terminal-call.json", terminal)
        end_ns = time.monotonic_ns()
        event_times = heartbeat_ns + [started_ns, returned_ns]
        event_times.sort()
        max_gap_ms = max(((b - a) / 1_000_000
                          for a, b in zip(event_times, event_times[1:])), default=0.0)
        row = {
            "trial_id": trial_id, "arm": arm,
            "injected_delay_before_each_helper_start_ms": delay_ms,
            "cancel_started_ns": started_ns, "cancel_returned_ns": returned_ns,
            "cancel_tool_elapsed_ms": (returned_ns - started_ns) / 1_000_000,
            "heartbeat_count": len(heartbeat_ns),
            "max_event_loop_gap_ms": max_gap_ms,
            "helper_start_receipts": start_receipts,
            "cancel": cancel, "terminal_call": terminal,
            "owner_input_obligations": json.loads(
                (root / "owner-io-entered.json").read_text(encoding="utf-8")),
            "finished_ns": end_ns, "evidence_directory": str(root),
        }
        _persist(root / "trial.json", row)
        return row
    finally:
        stop_heartbeat.set()
        if heartbeat_task is not None and not heartbeat_task.done():
            await heartbeat_task
        (root / "resume-owner-io").write_text("resume", encoding="utf-8")
        _persist(root / "close-response.json",
                 metadata(await server.call_tool("interface_close", {})))


async def run(run_id: str) -> dict:
    conditions = json.loads((HERE / "conditions-r02.json").read_text(encoding="utf-8"))
    original_get_context = multiprocessing.get_context
    runs_root = HERE / "raw" / "trials"
    rows, failures = [], []
    for arm, settings in conditions["arms"].items():
        for index in range(1, settings["trials"] + 1):
            try:
                rows.append(await _one_trial(
                    run_id, arm, settings["injected_delay_before_each_helper_start_ms"],
                    index, runs_root, original_get_context))
            except Exception as error:
                failures.append("%s-%02d: %s: %r" % (
                    arm, index, type(error).__name__, error))
                rows.append({"trial_id": "%s-%02d" % (arm, index),
                             "arm": arm, "status": "incomplete",
                             "error": repr(error)})

    for row in rows:
        if row.get("status") == "incomplete":
            continue
        cancel = row["cancel"]
        receipts = row["helper_start_receipts"]
        disconnect = cancel.get("owner_client_disconnect", {})
        release_attempt = cancel.get("owner_release_attempt", {})
        if any("error" in receipt for receipt in receipts):
            failures.append(row["trial_id"] + ": real helper start raised")
        if len(receipts) != 1:
            failures.append(row["trial_id"] + ": expected exactly one real helper start before disconnect gate")
        if disconnect.get("status") != "unknown" or disconnect.get("reason") != "supervision_timeout":
            failures.append(row["trial_id"] + ": expected XRes disconnect supervision timeout")
        if release_attempt.get("status") != "not_attempted":
            failures.append(row["trial_id"] + ": release must stay gated after unknown disconnect")
        if any(receipt.get("pid") is None for receipt in receipts):
            failures.append(row["trial_id"] + ": missing helper PID")
        if (cancel.get("release_confirmed") is not False
                or cancel.get("cleanup_status") != "UNKNOWN"
                or cancel.get("task_success") is not None
                or cancel.get("replay_allowed") is not False):
            failures.append(row["trial_id"] + ": cancellation certainty contract changed")
        if row["terminal_call"].get("status") != "runtime_failed":
            failures.append(row["trial_id"] + ": expected terminal runtime_failed receipt")
    baseline = [r for r in rows if r["arm"] == "actual-spawn-no-delay"
                and "cancel_tool_elapsed_ms" in r]
    delayed = [r for r in rows if r["arm"] == "actual-spawn-with-delay"
               and "cancel_tool_elapsed_ms" in r]
    if len(rows) != 6 or len(baseline) != 3 or len(delayed) != 3:
        failures.append("six complete trials required")
    if baseline and delayed:
        if min(r["cancel_tool_elapsed_ms"] for r in delayed) <= max(
                r["cancel_tool_elapsed_ms"] for r in baseline):
            failures.append("delayed Process.start arm did not separate cancellation latency")
        if min(r["max_event_loop_gap_ms"] for r in delayed) <= max(
                r["max_event_loop_gap_ms"] for r in baseline):
            failures.append("delayed Process.start arm did not separate heartbeat gap")
    return {
        "schema": "agent-interface/standard-caller-cancel-process-start-result-v2",
        "run_id": run_id,
        "conditions_sha256": hashlib.sha256(
            (HERE / "conditions-r02.json").read_bytes()).hexdigest(),
        "runtime": {"python": sys.version, "platform": __import__("platform").platform(),
                    "clock": "time.monotonic_ns"},
        "audit": {"status": "PASS" if not failures else "FAIL",
                  "failures": failures,
                  "meaning": "real spawn startup timing plus existing unknown-disconnect release gate; not a safety/product pass"},
        "trials": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
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
