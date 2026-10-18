#!/usr/bin/env python3
"""Run a deterministic readiness-overrun probe on the frozen PR adapter."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
sys.path.insert(0, str(INPUTS))
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin  # noqa: E402

OUTPUT = ROOT / "RESULT.json"


def verified_release() -> dict[str, Any]:
    return {
        "event": "input_release_transition",
        "operation": "up",
        "id": "program-1",
        "step": 2,
        "key": "d",
        "owner_id": "owner-1",
        "intent_token": "token-1",
        "owner_transition_verified": True,
        "owner_thread_keyup_verified": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True,
        "owned_keycodes_after_batch": [],
        "release_call_returned_ns": 0,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup",
            "operation": "up",
            "owner_id": "owner-1",
            "intent_token": "token-1",
            "server_sync_completed": True,
        },
    }


def run_case(name: str, *, duration_ns: int, ready_at_start: bool,
             ready_during_first_sample: bool) -> dict[str, Any]:
    class Clock:
        ns = 0

        def now(self) -> int:
            return self.ns

    clock = Clock()

    class Loop:
        period_ns = 10_000_000
        max_buffer_bytes = 1024

        def __init__(self) -> None:
            self.ready = ready_at_start
            self.readiness_checks = 0
            self.reads = 0

        def clock_ns(self) -> int:
            return clock.now()

        def wait_readable(self, _fd: int, _timeout: float) -> bool:
            self.readiness_checks += 1
            return self.ready

        def read_fn(self, _fd: int, _size: int) -> bytes:
            self.reads += 1
            return b'{"op":"finish"}\n'

    loop = Loop()
    sample_starts: list[int] = []
    rows: list[dict[str, Any]] = []

    def sample() -> dict[str, int]:
        sample_starts.append(clock.ns)
        clock.ns += duration_ns
        if ready_during_first_sample and len(sample_starts) == 1:
            loop.ready = True
        return {"sample_index": len(sample_starts)}

    stream = type("FakeStream", (), {"fileno": lambda _self: 7})()
    adapter = MainThreadScorerStdin(stream, sample, rows.append, loop=loop)
    tail = adapter.sample_tail(
        release_receipt=verified_release(),
        max_duration_ns=100_000_000,
        max_samples=10,
        stop_when=lambda _payload: False,
    )
    return {
        "name": name,
        "ready_at_start": ready_at_start,
        "ready_during_first_sample": ready_during_first_sample,
        "sample_duration_ns": duration_ns,
        "sample_period_ns": loop.period_ns,
        "sample_starts_ns": sample_starts,
        "scorer_rows": len(rows),
        "readiness_checks": loop.readiness_checks,
        "command_reads": loop.reads,
        "tail": tail,
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    cases = [
        run_case("ready_fast_control", duration_ns=1_000_000,
                 ready_at_start=True, ready_during_first_sample=False),
        run_case("ready_at_entry_overrun", duration_ns=25_000_000,
                 ready_at_start=True, ready_during_first_sample=False),
        run_case("command_arrives_during_overrun", duration_ns=25_000_000,
                 ready_at_start=False, ready_during_first_sample=True),
    ]
    slow = cases[1:]
    failed = any(
        case["tail"]["termination"] != "command_ready"
        and (case["ready_at_start"] or case["ready_during_first_sample"])
        for case in slow
    )
    result = {
        "schema": "issue59-scorer-tail-command-priority-a01-v1",
        "candidate_head": "0c3627d63072b89d1c769fd0048e93baf157f5c7",
        "classification": "synthetic source-boundary construction; no runtime or live allocation",
        "sample_period_ns": 10_000_000,
        "tail_deadline_ns": 100_000_000,
        "max_samples": 10,
        "scenarios": cases,
        "disposition": "FAIL_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN" if failed
                       else "PASS_COMMAND_PRIORITY",
        "scope": "command readiness is represented by a deterministic fake loop; scorer work is a synchronous fake call",
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
