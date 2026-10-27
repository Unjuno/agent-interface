"""Reproduce the Win32 owner's admission decision after post-readback input."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


SOURCE_COMMIT = "52df8e2d934bd8b20d4d36da8a7f17a524c49210"
SOURCE_PATH = "runtime/guarded_win32_v1/operation_owner.py"
EXPECTED_SOURCE_SHA256 = "f6ce2e9fa5bab634495b2a4361a45dd8a06ab480aa0dd445cd96ad2fee10938a"
GENERATION_A = "a" * 64
GENERATION_B = "b" * 64
OPERATION_A = "1" * 32
OPERATION_B = "2" * 32


class FakeProcess:
    pid = 43101
    exitcode = None
    alive = True

    def is_alive(self):
        return self.alive


def main() -> None:
    source = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        cwd=ROOT, check=True, capture_output=True).stdout
    source_sha = hashlib.sha256(source).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("pinned current-main operation-owner source changed")
    pinned_module = types.ModuleType("pinned_current_main_operation_owner")
    exec(compile(source, SOURCE_PATH, "exec"), pinned_module.__dict__)
    OperationOwner = pinned_module.OperationOwner

    process = FakeProcess()
    identity = {"pid": process.pid, "creation_time_100ns": 91301}
    owner = OperationOwner(clock_ns=time.monotonic_ns,
        process_identity_reader=lambda handle: identity if handle is process else None)
    owner.admit(OPERATION_A, GENERATION_A, time.monotonic_ns() + 10_000_000_000,
                ["key:fixture:CTRL"], start_gate_required=True)
    if not owner.producer_started(OPERATION_A, GENERATION_A, process,
                                  process_identity=identity):
        raise RuntimeError("producer identity was not accepted")
    if not owner.authorize_producer_start(OPERATION_A, GENERATION_A, process,
                                          lambda: None):
        raise RuntimeError("gated producer was not authorized")
    cleanup_deadline = time.monotonic_ns() + 10_000_000_000
    owner.request_cancel(OPERATION_A, GENERATION_A,
                         cleanup_deadline_ns=cleanup_deadline)
    process.alive = False
    process.exitcode = 0
    if not owner.producer_retired(OPERATION_A, GENERATION_A, process):
        raise RuntimeError("exact producer retirement was not accepted")
    recovery = owner.claim_recovery(OPERATION_A, GENERATION_A)
    if recovery is None:
        raise RuntimeError("recovery claim did not return expected identity")
    recovery_id = recovery["recovery_id"]
    readback = {
        "operation_id": OPERATION_A,
        "target_generation": GENERATION_A,
        "recovery_id": recovery_id,
        "neutral": True,
        "observed_monotonic_ns": time.monotonic_ns(),
    }
    if not owner.recovery_completed(OPERATION_A, GENERATION_A, recovery_id,
                                   release_accepted=True, readback=readback):
        raise RuntimeError("neutral point-in-time recovery was not accepted")

    # Model an old queued DOWN becoming visible after the neutral readback.
    # This is a counterexample schedule, not a claim about real SendInput.
    simulated_external_state = {"ctrl_down": False}
    observed_neutral_at_recovery = not simulated_external_state["ctrl_down"]
    simulated_external_state["ctrl_down"] = True
    prior = owner.result(OPERATION_A)
    next_attempt = owner.admit(OPERATION_B, GENERATION_B,
        time.monotonic_ns() + 10_000_000_000,
        ["key:fixture:ALT"], start_gate_required=True)

    result = {
        "schema": "win32-delayed-input-quarantine-counterexample-v1",
        "source_commit": SOURCE_COMMIT,
        "source_path": SOURCE_PATH,
        "source_sha256": source_sha,
        "environment": "Windows fake process/state only; no Win32 API or SendInput",
        "events": [
            "generation-A producer admitted and authorized",
            "generation-A producer retirement confirmed",
            "recovery UP accepted and point-in-time neutral readback confirmed",
            "simulated old DOWN appears after that readback",
            "generation-B operation admitted while simulated CTRL remains down",
        ],
        "observations": {
            "neutral_at_recovery_readback": observed_neutral_at_recovery,
            "external_ctrl_down_after_delayed_event": simulated_external_state["ctrl_down"],
            "old_owner_phase_after_delayed_event": prior["phase"],
            "old_owner_release_confirmed": prior["release_confirmed"],
            "old_owner_task_success": prior["task_success"],
            "old_owner_replay_allowed": prior["replay_allowed"],
            "new_generation_admitted": next_attempt["phase"] == "admitted",
            "new_generation_phase": next_attempt["phase"],
        },
        "interpretation": (
            "The owner accepts a different target generation after a neutral snapshot; "
            "it has no late-event quarantine or post-readback horizon. The delayed DOWN "
            "is deliberately injected fake state and does not establish native Windows timing."
        ),
    }
    output = Path(__file__).with_name("result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
