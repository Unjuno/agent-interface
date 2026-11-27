"""Fault-injection probe for Win32 input accepted before SendInput returns.

The fake API records an accepted key-down, then blocks the same call before
returning to the runtime. No Win32 DLL, desktop, or real input is used.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class AcceptedThenBlockedAPI:
    def __init__(self):
        self.down: set[int] = set()
        self.events: list[dict] = []
        self.accepted = threading.Event()
        self.resume = threading.Event()

    def SendInput(self, count, items, size):
        if count != 1:
            raise AssertionError("probe expects one input per SendInput call")
        item = items[0]
        if item.type != native.INPUT_KEYBOARD:
            raise AssertionError("probe expects keyboard events only")
        vk = int(item.ki.wVk)
        down = not bool(item.ki.dwFlags & native.KEYEVENTF_KEYUP)
        row = {"kind": "down" if down else "up", "vk": vk,
               "accepted_ns": time.monotonic_ns()}
        self.events.append(row)
        if down:
            self.down.add(vk)
            self.accepted.set()
            if not self.resume.wait(5):
                raise TimeoutError("probe resume barrier expired")
        else:
            self.down.discard(vk)
        return 1

    def GetAsyncKeyState(self, vk):
        return 0x8000 if vk in self.down else 1


def run(mode: str) -> dict:
    backend = native.Win32Backend.__new__(native.Win32Backend)
    backend.targets = {}
    backend.held_keys = {}
    backend.held_buttons = set()
    backend.pending_unicode_ups = set()
    backend.emissions = 0
    api = AcceptedThenBlockedAPI()
    backend.user32 = api
    session = Win32RuntimeSession(backend)
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": f"blocked-sendinput-{mode}",
        "source": {"observation_seq": 0, "binding_revision": 0},
        "authority": {"lease_id": "synthetic-blocked-sendinput",
                       "expires_at_ns": 2**63 - 1},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "key_state", "key": "CTRL", "down": True},
                {"op": "release_all"}],
    }
    dispatched: list[dict] = []

    def dispatch():
        dispatched.append(session.dispatch(
            program, current_observation_seq=0,
            current_binding_revision=0))

    owner = threading.Thread(target=dispatch, name="synthetic-input-owner")
    started_ns = time.monotonic_ns()
    owner.start()
    if not api.accepted.wait(3):
        api.resume.set()
        owner.join(5)
        raise TimeoutError("SendInput DOWN did not reach the fake acceptance barrier")

    blocked_snapshot = {
        "api_key_down": sorted(api.down),
        "backend_held_keys": dict(backend.held_keys),
        "session_recovery_required": session.recovery_required,
        "events": list(api.events),
    }
    recovery_started_ns = time.monotonic_ns()
    recovery = session.recover_input()
    recovery_returned_ns = time.monotonic_ns()
    recovery_snapshot = {
        "result": recovery,
        "response_ms": (recovery_returned_ns - recovery_started_ns) / 1e6,
        "api_key_down": sorted(api.down),
        "backend_held_keys": dict(backend.held_keys),
        "events": list(api.events),
    }

    api.resume.set()
    owner.join(5)
    if owner.is_alive():
        raise TimeoutError("input owner failed to finish after barrier release")
    if len(dispatched) != 1:
        raise AssertionError("owner did not produce exactly one dispatch result")

    return {
        "schema": "win32-blocked-sendinput-recovery-probe-r01",
        "mode": mode,
        "python": platform.python_version(),
        "source_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "backend_blob": subprocess.check_output(
            ["git", "rev-parse", "HEAD:runtime/backends/win32_v1/backend.py"],
            cwd=ROOT, text=True).strip(),
        "session_blob": subprocess.check_output(
            ["git", "rev-parse", "HEAD:runtime/backends/win32_v1/session.py"],
            cwd=ROOT, text=True).strip(),
        "started_ns": started_ns,
        "blocked_snapshot": blocked_snapshot,
        "recovery_snapshot": recovery_snapshot,
        "dispatch_result": dispatched[0],
        "events_after_resume": list(api.events),
        "api_key_down_after_resume": sorted(api.down),
        "backend_held_keys_after_resume": dict(backend.held_keys),
        "recovery_required_after_resume": session.recovery_required,
        "interpretation": (
            "Fake SendInput accepted CTRL-down before blocking its return. "
            "Concurrent recover_input was refused because recovery_required "
            "was still false and emitted no UP. The key remained down until "
            "the original API call returned and its normal terminal release ran."
        ),
        "scope": "synthetic API fault injection; not a claim about internal Windows SendInput scheduling",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("normal", "optimized"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    row = run(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"mode": args.mode,
                      "recovery": row["recovery_snapshot"],
                      "api_key_down_after_resume": row["api_key_down_after_resume"],
                      "dispatch_status": row["dispatch_result"]["status"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
