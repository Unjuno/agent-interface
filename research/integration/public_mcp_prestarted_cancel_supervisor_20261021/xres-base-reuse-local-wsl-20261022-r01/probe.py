"""Identify XRes resource-base reuse by the cleanup observer vs a bystander."""
from __future__ import annotations

import json
import multiprocessing
import os
import time
import uuid
from pathlib import Path


def _owner(display_name: str, ready, hold) -> None:
    from Xlib.display import Display

    display = Display(display_name)
    ready.send({
        "pid": os.getpid(),
        "resource_base": display.display.info.resource_id_base,
    })
    hold.wait(10)
    display.close()


def _replacement(display_name: str, ready, hold) -> None:
    _owner(display_name, ready, hold)


def _cancel_worker(display_name: str, request_recv, ready, result) -> None:
    from runtime.guarded_x11_v1 import xres_client_fence
    from runtime.guarded_x11_v1.cancel_supervisor import x11_cancel_worker

    observed = []
    original = xres_client_fence.client_pid_at_base

    def record(connection, resource_base):
        pid = original(connection, resource_base)
        observed.append({
            "worker_pid": os.getpid(),
            "observer_resource_base": connection.display.info.resource_id_base,
            "target_resource_base": resource_base,
            "observed_pid": pid,
        })
        return pid

    xres_client_fence.client_pid_at_base = record
    ready.send({"pid": os.getpid(), "connected_to_x": False})
    request = request_recv.recv()
    outcome = x11_cancel_worker(request)
    result.send({"outcome": outcome, "xres_observations": observed})


def _scenario(display_name: str, include_replacement: bool) -> dict:
    context = multiprocessing.get_context("spawn")
    from Xlib.display import Display

    keepers = [Display(display_name), Display(display_name)]
    keepers_before = [
        display.display.info.resource_id_base for display in keepers
    ]
    owner_ready_recv, owner_ready_send = context.Pipe(duplex=False)
    owner_hold = context.Event()
    owner = context.Process(
        target=_owner,
        args=(display_name, owner_ready_send, owner_hold),
        name="resource-base-owner",
    )

    worker_ready_recv, worker_ready_send = context.Pipe(duplex=False)
    worker_request_recv, worker_request_send = context.Pipe(duplex=False)
    worker_result_recv, worker_result_send = context.Pipe(duplex=False)
    worker = context.Process(
        target=_cancel_worker,
        args=(
            display_name,
            worker_request_recv,
            worker_ready_send,
            worker_result_send,
        ),
        name="prestarted-cancel-observer",
    )
    # Start the helper before the owner, as in the prestarted path. It does not
    # open an X connection until the cancellation request is released.
    worker.start()
    worker_ready = worker_ready_recv.recv()
    owner.start()
    owner_identity = owner_ready_recv.recv()
    owner_ready_recv.close()
    owner.terminate()
    owner.join(2)
    owner_retired = not owner.is_alive()

    replacement_identity = None
    replacement = None
    replacement_hold = None
    if include_replacement:
        replacement_ready_recv, replacement_ready_send = context.Pipe(
            duplex=False
        )
        replacement_hold = context.Event()
        replacement = context.Process(
            target=_replacement,
            args=(display_name, replacement_ready_send, replacement_hold),
            name="resource-base-replacement",
        )
        replacement.start()
        replacement_identity = replacement_ready_recv.recv()
        replacement_ready_recv.close()

    request = {
        "operation_id": uuid.uuid4().hex,
        "session_id": uuid.uuid4().hex,
        "deadline_monotonic_ns": time.monotonic_ns() + 5_000_000_000,
        "x_resource_base": owner_identity["resource_base"],
        "owner_pid": owner_identity["pid"],
        "display_name": display_name,
        "keys": {},
        "buttons": [],
        "binding_revision": 0,
        "owner_generation": {
            "session_id": None,
            "child_pid": owner_identity["pid"],
            "x_resource_base": owner_identity["resource_base"],
            "binding_revision": 0,
        },
    }
    request["owner_generation"]["session_id"] = request["session_id"]
    # The worker was started before the owner; send the identity only after
    # the owner has retired. The process runs a single exact worker invocation.
    worker_request_send.send(request)
    worker_request_send.close()
    worker.join(5)
    if worker.is_alive():
        worker.terminate()
        worker.join(1)
    worker_outcome = (
        worker_result_recv.recv() if worker_result_recv.poll(1) else None
    )

    if replacement is not None:
        replacement_hold.set()
        replacement.join(2)
        if replacement.is_alive():
            replacement.terminate()
            replacement.join(1)
    for display in keepers:
        display.close()
    return {
        "display": display_name,
        "include_replacement": include_replacement,
        "keepers_resource_bases": keepers_before,
        "owner": owner_identity,
        "owner_retired": owner_retired,
        "worker_ready": worker_ready,
        "worker_pid": worker.pid,
        "replacement": replacement_identity,
        "worker_outcome": worker_outcome,
        "worker_exitcode": worker.exitcode,
    }


def main() -> None:
    report = {
        "schema": "agent-interface/xres-base-reuse-diagnostic-v1",
        "scope": (
            "Private Xvfb, no input events; use current x11_cancel_worker "
            "with empty obligations only to identify observed XRes client."
        ),
        "scenarios": [
            _scenario(":89", include_replacement=False),
            _scenario(":90", include_replacement=True),
        ],
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
