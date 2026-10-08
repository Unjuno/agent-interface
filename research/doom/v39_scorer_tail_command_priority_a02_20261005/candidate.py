#!/usr/bin/env python3
"""Exercise the frozen scorer-tail adapter against real OS socket readiness."""
from __future__ import annotations

import json
import select
import socket
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "inputs"))
from main_thread_scorer_polling_v1 import MainThreadScorerPolling  # noqa: E402
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin  # noqa: E402

OUTPUT = ROOT / "RESULT_V3.json"
PERIOD_NS = 10_000_000
DEADLINE_NS = 100_000_000


def verified_release(release_returned_ns: int) -> dict[str, Any]:
    return {
        "event": "input_release_transition", "operation": "up", "id": "program-1",
        "step": 2, "key": "d", "owner_id": "owner-1", "intent_token": "token-1",
        "owner_transition_verified": True, "owner_thread_keyup_verified": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True, "owned_keycodes_after_batch": [],
        "release_call_returned_ns": release_returned_ns,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "operation": "up", "owner_id": "owner-1",
            "intent_token": "token-1", "server_sync_completed": True,
        },
    }


def run_case(name: str, *, sample_duration_ns: int, ready_at_entry: bool,
             schedule_during_first_sample: bool) -> dict[str, Any]:
    reader, writer = socket.socketpair()
    reader.setblocking(False)
    writer.setblocking(False)
    if ready_at_entry:
        writer.sendall(b'{"op":"finish"}\n')

    period_s = PERIOD_NS / 1_000_000_000
    loop = MainThreadScorerPolling(sample_hz=1.0 / period_s)
    original_wait_readable = loop.wait_readable
    readiness_checks = 0

    def wait_readable(fd: int, timeout_s: float) -> bool:
        nonlocal readiness_checks
        readiness_checks += 1
        return original_wait_readable(fd, timeout_s)

    loop.wait_readable = wait_readable
    sample_returns: list[int] = []
    scorer_rows: list[dict[str, Any]] = []

    def sample() -> dict[str, int]:
        duration_s = sample_duration_ns / 1_000_000_000
        if schedule_during_first_sample and not sample_returns:
            time.sleep(min(0.005, duration_s / 2))
            writer.sendall(b'{"op":"finish"}\n')
            time.sleep(max(0, duration_s - 0.005))
        else:
            time.sleep(duration_s)
        sample_returns.append(time.perf_counter_ns())
        return {"sample_index": len(sample_returns)}

    adapter = MainThreadScorerStdin(reader, sample, scorer_rows.append, loop=loop)
    release_returned_ns = time.perf_counter_ns()
    receipt = verified_release(release_returned_ns)
    started_ns = time.perf_counter_ns()
    tail = adapter.sample_tail(
        release_receipt=receipt, max_duration_ns=DEADLINE_NS,
        max_samples=10, stop_when=lambda _payload: False,
    )
    ended_ns = time.perf_counter_ns()
    ready_after = bool(select.select([reader], [], [], 0)[0])
    unread_bytes = len(reader.recv(65536, socket.MSG_PEEK)) if ready_after else 0
    result = {
        "name": name,
        "sample_duration_ns": sample_duration_ns,
        "sample_period_ns": PERIOD_NS,
        "tail_deadline_ns": DEADLINE_NS,
        "ready_at_entry": ready_at_entry,
        "scheduled_during_first_sample": schedule_during_first_sample,
        "sample_return_count": len(sample_returns),
        "sample_return_offsets_ns": [t - started_ns for t in sample_returns],
        "scorer_row_count": len(scorer_rows),
        "readiness_check_count": readiness_checks,
        "tail": tail,
        "tail_wall_elapsed_ns": ended_ns - started_ns,
        "command_bytes_still_unread": unread_bytes,
        "socket_readable_after_tail": ready_after,
        "sender_completed": True if schedule_during_first_sample else None,
    }
    reader.close()
    writer.close()
    return result


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    cases = [
        run_case("ready_fast_control", sample_duration_ns=1_000_000,
                 ready_at_entry=True, schedule_during_first_sample=False),
        run_case("ready_at_entry_overrun", sample_duration_ns=25_000_000,
                 ready_at_entry=True, schedule_during_first_sample=False),
        run_case("command_arrives_during_overrun", sample_duration_ns=25_000_000,
                 ready_at_entry=False, schedule_during_first_sample=True),
    ]
    overrun_starvation = all(
        c["tail"].get("termination") == "deadline"
        and c["tail"].get("tail_samples", 0) >= 3
        and c["command_bytes_still_unread"] > 0
        for c in cases[1:]
    )
    control_ok = cases[0]["tail"].get("termination") == "command_ready"
    if not control_ok or not overrun_starvation:
        disposition = "INCONCLUSIVE_OR_DIFFERENT_SOURCE_BEHAVIOR"
    else:
        disposition = "FAIL_OS_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN"
    result = {
        "schema": "issue59-scorer-tail-command-priority-a02-v1",
        "candidate_source_head": "0c3627d63072b89d1c769fd0048e93baf157f5c7",
        "construction_only": True,
        "platform": {"os": __import__("platform").platform(),
                     "python": __import__("platform").python_version()},
        "clock": "time.perf_counter_ns",
        "readiness": "select.select on socketpair receiver; command payload sent as real bytes",
        "disposition": disposition,
        "scenarios": cases,
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
