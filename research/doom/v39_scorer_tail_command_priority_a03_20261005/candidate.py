"""One-shot Windows socketpair probe of the frozen V39 scorer-tail adapter."""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "source"))
from map01_scorer_stdio_adapter_v2 import MainThreadScorerStdin  # noqa: E402
from main_thread_scorer_polling_v1 import MainThreadScorerPolling  # noqa: E402

RESULT = ROOT / "results" / "a03" / "RESULT.json"
COMMAND = b'{"op":"finish"}\n'


def release_receipt(release_ns: int, case_id: str) -> dict:
    return {
        "event": "input_release_transition",
        "operation": "up",
        "id": case_id,
        "step": 1,
        "key": "d",
        "owner_id": "a03-owner",
        "intent_token": "a03-token",
        "owner_transition_verified": True,
        "owner_thread_keyup_verified": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True,
        "owned_keycodes_after_batch": [],
        "release_call_returned_ns": release_ns,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup",
            "operation": "up",
            "owner_id": "a03-owner",
            "key": "d",
            "intent_token": "a03-token",
            "server_sync_completed": True,
        },
    }


def run_case(name: str) -> dict:
    reader, writer = socket.socketpair()
    reader.setblocking(True)
    writer.setblocking(True)
    callback_entered = threading.Event()
    command_sent = threading.Event()
    callbacks: list[int] = []
    readiness_checks: list[float] = []
    sender_error: list[str] = []

    class Stream:
        def fileno(self):
            return reader.fileno()

    def wait_readable(_fd, timeout_s):
        readiness_checks.append(timeout_s)
        ready, _, _ = select.select([reader], [], [], timeout_s)
        return bool(ready)

    def read_fn(_fd, count):
        return reader.recv(count)

    def sample():
        callbacks.append(time.perf_counter_ns())
        callback_entered.set()
        if name == "slow_callback":
            if not command_sent.wait(2):
                raise TimeoutError("sender did not publish during slow callback")
            time.sleep(0.025)
        elif name == "normal_wait":
            time.sleep(0.001)
        else:
            time.sleep(0.025)
        return {"construction_sample": len(callbacks)}

    def send_after_callback_starts(delay_s: float):
        try:
            if not callback_entered.wait(2):
                raise TimeoutError("scorer callback did not start")
            if delay_s:
                time.sleep(delay_s)
            writer.sendall(COMMAND)
            command_sent.set()
        except BaseException as error:
            sender_error.append(f"{type(error).__name__}: {error}")
            command_sent.set()

    if name == "ready_at_entry":
        writer.sendall(COMMAND)
    else:
        delay = 0.002 if name == "normal_wait" else 0
        sender = threading.Thread(target=send_after_callback_starts,
                                  args=(delay,), daemon=True)
        sender.start()

    loop = MainThreadScorerPolling(
        sample_hz=100.0, wait_readable=wait_readable, read_fn=read_fn)
    adapter = MainThreadScorerStdin(Stream(), sample, lambda _row: None,
                                    loop=loop)
    started_ns = time.perf_counter_ns()
    tail = adapter.sample_tail(
        release_receipt=release_receipt(started_ns, name),
        max_duration_ns=100_000_000, max_samples=10)
    tail_returned_ns = time.perf_counter_ns()
    unread = reader.recv(1024, socket.MSG_PEEK)
    delivered = next(adapter)
    final_stats = adapter.stats()
    if name != "ready_at_entry":
        sender.join(timeout=2)
    record = {
        "case": name,
        "termination": tail["termination"],
        "disposition": tail["disposition"],
        "tail_samples": tail["tail_samples"],
        "deadline_overrun": tail["deadline_overrun"],
        "samples_before_resume": len(callbacks) - (final_stats["samples"] - tail["tail_samples"]),
        "samples_total_after_resume": final_stats["samples"],
        "resume_samples": final_stats["samples"] - tail["tail_samples"],
        "readiness_checks": len(readiness_checks),
        "unread_command_after_tail": unread.decode("ascii"),
        "delivered_command": delivered,
        "commands_delivered": final_stats["commands"],
        "call_elapsed_ns": tail_returned_ns - started_ns,
        "sender_error": sender_error or None,
    }
    writer.close()
    reader.close()
    return record


def run() -> dict:
    if os.name != "nt" or sys.version_info[:2] != (3, 11):
        raise RuntimeError("frozen environment requires Windows CPython 3.11")
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    cases = [run_case(name) for name in
             ("ready_at_entry", "slow_callback", "normal_wait")]
    result = {
        "schema": "issue59-scorer-tail-command-priority-result-v3",
        "run_id": "MAP01-V39-SCORER-TAIL-COMMAND-PRIORITY-A03-20261005",
        "classification": "one-shot Windows socketpair construction",
        "source_commit": json.loads((ROOT / "FREEZE.json").read_text())["source_commit"],
        "cases": cases,
        "scope": "OS socket readiness only; no real stdin, game, GUI, OS input, model, or live allocation",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
