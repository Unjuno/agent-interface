"""One-shot deterministic V39 scorer-tail command-priority construction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
sys.path.insert(0, str(RESEARCH / "doom"))

from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin  # noqa: E402


class Clock:
    def __init__(self):
        self.ns = 0

    def now(self):
        return self.ns


class Loop:
    period_ns = 10
    max_buffer_bytes = 1024

    def __init__(self, clock):
        self.clock = clock
        self.ready = False
        self.reads = 0
        self.chunks = [b'{"op":"finish"}\n']

    def clock_ns(self):
        return self.clock.now()

    def wait_readable(self, _fd, _timeout):
        return self.ready

    def read_fn(self, _fd, _size):
        self.reads += 1
        return self.chunks.pop(0)


def verified_release():
    return {
        "event": "input_release_transition",
        "operation": "up",
        "id": "a04-program-1",
        "step": 2,
        "key": "d",
        "owner_id": "a04-owner-1",
        "intent_token": "a04-token-1",
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
            "owner_id": "a04-owner-1",
            "intent_token": "a04-token-1",
            "server_sync_completed": True,
        },
    }


def main():
    clock = Clock()
    loop = Loop(clock)
    callback_times = []
    rows = []
    def sample():
        callback_times.append(clock.ns)
        if len(callback_times) == 1:
            clock.ns = 125
            loop.ready = True
        return {"state": "running"}

    adapter = MainThreadScorerStdin(
        type("Stream", (), {"fileno": lambda _self: 0})(),
        sample,
        rows.append,
        loop=loop,
    )
    tail = adapter.sample_tail(
        release_receipt=verified_release(),
        max_duration_ns=100,
        max_samples=5,
        stop_when=lambda _sample: False,
    )
    reads_before_resume = loop.reads
    command = next(adapter)
    raw = {
        "schema": "v39-scorer-tail-command-priority-raw-a04-v1",
        "scenario": {
            "release_returned_ns": 0,
            "tail_deadline_ns": 100,
            "callback_start_ns": 0,
            "callback_finish_ns": 125,
            "command_became_readable_during_callback": True,
            "command_json": '{"op":"finish"}',
            "command_terminator": "LF",
        },
        "tail": tail,
        "tail_rows": [
            {key: value for key, value in row.items() if key != "payload"}
            | {"payload": row["payload"]}
            for row in rows
        ],
        "callback_times_ns": callback_times,
        "reads_before_resume": reads_before_resume,
        "command_returned_after_resume": command,
        "callback_count_after_resume": len(callback_times),
        "read_count_after_resume": loop.reads,
        "command_count_after_resume": adapter.commands,
    }
    out = HERE / "results" / "a04" / "RAW.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite retained candidate output: {out}")
    out.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
