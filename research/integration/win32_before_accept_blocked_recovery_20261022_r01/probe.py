"""Exercise public recovery while inert SendInput blocks before acceptance."""
from __future__ import annotations

import argparse
import hashlib
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


class BeforeAcceptBlockedAPI:
    def __init__(self) -> None:
        self.down: set[int] = set()
        self.events: list[dict] = []
        self.lock = threading.Lock()
        self.down_entered = threading.Event()
        self.allow_accept = threading.Event()
        self.down_accepted = threading.Event()
        self.allow_return = threading.Event()
        self._first_down = True

    def SendInput(self, count, items, size):
        require(count == 1, "probe expects one input per SendInput call")
        item = items[0]
        require(item.type == native.INPUT_KEYBOARD,
                "probe expects keyboard events only")
        vk = int(item.ki.wVk)
        is_down = not bool(item.ki.dwFlags & native.KEYEVENTF_KEYUP)
        if is_down and self._first_down:
            self._first_down = False
            self.down_entered.set()
            require(self.allow_accept.wait(5),
                    "pre-acceptance barrier expired")
            self._record("old_down", vk, True)
            self.down_accepted.set()
            require(self.allow_return.wait(5),
                    "post-acceptance barrier expired")
            return 1
        self._record("up" if not is_down else "down", vk, is_down)
        return 1

    def _record(self, kind: str, vk: int, is_down: bool) -> None:
        with self.lock:
            if is_down:
                self.down.add(vk)
            else:
                self.down.discard(vk)
            self.events.append({"kind": kind, "vk": vk,
                                "accepted_ns": time.monotonic_ns(),
                                "api_keys_down": sorted(self.down)})

    def snapshot(self) -> tuple[list[dict], list[int]]:
        with self.lock:
            return list(self.events), sorted(self.down)

    def GetAsyncKeyState(self, vk):
        with self.lock:
            return 0x8000 if vk in self.down else 1


def run(mode: str) -> dict:
    backend = native.Win32Backend.__new__(native.Win32Backend)
    backend.targets = {}
    backend.held_keys = {}
    backend.held_buttons = set()
    backend.pending_unicode_ups = set()
    backend.emissions = 0
    api = BeforeAcceptBlockedAPI()
    backend.user32 = api
    session = Win32RuntimeSession(backend)
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": f"before-accept-recovery-{mode}",
        "source": {"observation_seq": 0, "binding_revision": 0},
        "authority": {"lease_id": "synthetic-before-accept-r01",
                       "expires_at_ns": 2**63 - 1},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "key_state", "key": "CTRL", "down": True},
                {"op": "release_all"}],
    }
    dispatch_results: list[dict] = []
    owner = threading.Thread(
        target=lambda: dispatch_results.append(session.dispatch(
            program, current_observation_seq=0, current_binding_revision=0)),
        name="synthetic-old-input-owner",
    )
    started_ns = time.monotonic_ns()
    owner.start()
    require(api.down_entered.wait(3),
            "DOWN did not reach the pre-acceptance barrier")
    before_recovery_events, before_recovery_state = api.snapshot()
    before_recovery = {
        "events": before_recovery_events,
        "api_keys_down": before_recovery_state,
        "backend_held_keys": dict(backend.held_keys),
        "session_recovery_required": session.recovery_required,
    }

    recovery_started_ns = time.monotonic_ns()
    recovery_result = session.recover_input()
    recovery_returned_ns = time.monotonic_ns()
    recovery_events, recovery_state = api.snapshot()
    after_recovery = {
        "started_ns": recovery_started_ns,
        "returned_ns": recovery_returned_ns,
        "response_ms": (recovery_returned_ns - recovery_started_ns) / 1e6,
        "result": recovery_result,
        "events": recovery_events,
        "api_keys_down": recovery_state,
        "backend_held_keys": dict(backend.held_keys),
        "session_recovery_required": session.recovery_required,
    }
    require(recovery_result.get("status") == "refused"
            and recovery_result.get("error") == "INPUT_RECOVERY_NOT_REQUIRED"
            and recovery_result.get("release_attempted") is False,
            "current public recovery outcome changed")
    require(recovery_events == [] and recovery_state == [],
            "public recovery emitted input or changed fake state")

    api.allow_accept.set()
    require(api.down_accepted.wait(3),
            "old DOWN did not reach the post-acceptance barrier")
    late_events, late_state = api.snapshot()
    require([row["kind"] for row in late_events] == ["old_down"]
            and late_state == [0x11],
            "old producer did not accept a late CTRL-down after recovery returned")

    api.allow_return.set()
    owner.join(5)
    require(not owner.is_alive(), "owner did not finish after barrier release")
    require(len(dispatch_results) == 1, "missing unique dispatch result")
    final_events, final_state = api.snapshot()
    require([row["kind"] for row in final_events] == ["old_down", "up"]
            and final_state == [],
            "ordinary terminal release did not leave fake input neutral")

    return {
        "schema": "win32-before-accept-blocked-recovery-r01",
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
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_ns": started_ns,
        "before_recovery": before_recovery,
        "after_recovery": after_recovery,
        "after_late_down_before_old_call_return": {
            "events": late_events, "api_keys_down": late_state},
        "after_old_call_return": {
            "events": final_events, "api_keys_down": final_state,
            "dispatch_result": dispatch_results[0]},
        "scope": "deterministic inert API schedule; not evidence of Windows SendInput blocking or physical release",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("normal", "optimized"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"mode": result["mode"],
                      "recovery": result["after_recovery"]["result"],
                      "fake_keys_down_after_recovery": result["after_recovery"]["api_keys_down"],
                      "fake_keys_down_after_late_down": result[
                          "after_late_down_before_old_call_return"]["api_keys_down"],
                      "final_fake_keys_down": result["after_old_call_return"]["api_keys_down"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
