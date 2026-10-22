"""Inert Win32 API schedule: early UP followed by a late DOWN.

The fake accepts neither OS input nor desktop input. It blocks the first
SendInput DOWN before acceptance, lets a separate test sender submit UP, then
accepts the old DOWN and blocks its return so the state can be sampled before
ordinary terminal cleanup.
"""
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


class BeforeAcceptThenBlockedAPI:
    def __init__(self) -> None:
        self.down: set[int] = set()
        self.events: list[dict] = []
        self.lock = threading.Lock()
        self.old_down_entered = threading.Event()
        self.allow_old_down_accept = threading.Event()
        self.old_down_accepted = threading.Event()
        self.allow_old_down_return = threading.Event()
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
            self.old_down_entered.set()
            require(self.allow_old_down_accept.wait(5),
                    "pre-acceptance barrier expired")
            self._record("old_down", vk, True)
            self.old_down_accepted.set()
            require(self.allow_old_down_return.wait(5),
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
                                "api_down_after": sorted(self.down)})

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
    api = BeforeAcceptThenBlockedAPI()
    backend.user32 = api
    session = Win32RuntimeSession(backend)
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": f"late-down-after-early-up-{mode}",
        "source": {"observation_seq": 0, "binding_revision": 0},
        "authority": {"lease_id": "synthetic-r01",
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
    require(api.old_down_entered.wait(3),
            "old DOWN did not reach the pre-acceptance barrier")
    pre_accept_events, pre_accept_down = api.snapshot()
    require(pre_accept_down == [], "DOWN affected fake state before acceptance")

    # Counterfactual recovery sender: bypasses the current session refusal to
    # model a design that submits UP without first fencing the old producer.
    early_up_started_ns = time.monotonic_ns()
    backend._send_key(0x11, False)
    early_up_returned_ns = time.monotonic_ns()
    early_up_events, early_up_state = api.snapshot()
    require(early_up_state == [], "early UP should leave fake state neutral")

    api.allow_old_down_accept.set()
    require(api.old_down_accepted.wait(3),
            "old DOWN did not reach the post-acceptance barrier")
    late_events, late_state = api.snapshot()
    require(late_state == [0x11], "old DOWN was not visible after early UP")
    require([row["kind"] for row in late_events] == ["up", "old_down"],
            "unexpected event order before old SendInput returned")

    api.allow_old_down_return.set()
    owner.join(5)
    require(not owner.is_alive(), "owner did not finish after final barrier")
    require(len(dispatch_results) == 1, "missing unique dispatch result")
    final_events, final_down = api.snapshot()
    require(final_down == [], "ordinary terminal cleanup did not neutralize fake state")
    require([row["kind"] for row in final_events] == ["up", "old_down", "up"],
            "expected early UP, late old DOWN, then terminal UP")

    return {
        "schema": "win32-late-down-after-early-up-r01",
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
        "pre_acceptance": {"events": pre_accept_events,
                           "fake_keys_down": pre_accept_down},
        "early_up": {"started_ns": early_up_started_ns,
                     "returned_ns": early_up_returned_ns,
                     "events": early_up_events,
                     "fake_keys_down": early_up_state,
                     "sender": "counterfactual direct test sender; not session recovery"},
        "late_down_before_old_call_return": {"events": late_events,
                                              "fake_keys_down": late_state},
        "after_old_call_return": {"events": final_events,
                                  "fake_keys_down": final_down,
                                  "dispatch_result": dispatch_results[0]},
        "scope": "deterministic inert API schedule; not evidence of Windows SendInput ordering or physical release",
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
    print(json.dumps({"mode": args.mode,
                      "events_before_old_return": [
                          row["kind"] for row in result[
                              "late_down_before_old_call_return"]["events"]],
                      "fake_keys_down_before_old_return": result[
                          "late_down_before_old_call_return"]["fake_keys_down"],
                      "final_fake_keys_down": result[
                          "after_old_call_return"]["fake_keys_down"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
