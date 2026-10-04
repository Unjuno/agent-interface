"""Compose the current-locator, receipt compiler, and task socket boundary.

This module performs no observation, model, image, socket, or game I/O itself.
The supplied adapters must return observations, clocks, image-bound receipts,
and terminal input-release receipts from their respective live interfaces.
"""

from __future__ import annotations

from adaptive_route import RouteStop
from target_dispatch import DispatchStop, compile_receipt_target_click


TARGETS = ("palette_point", "target_point")


def dispatch_task_targets(*, coordinator, task_id: str, layout: str,
                          observe, read_clock, build_receipt, submit) -> list[dict]:
    """Dispatch exactly the two frozen points, each from fresh current evidence.

    ``submit`` must block until that compiled request has a terminal execution
    record and all held inputs are released. An exception or ambiguous receipt
    stops the task; this function never retries a target request.
    """
    if (not getattr(coordinator, "pending_resolution", False)
            or getattr(coordinator, "resolved_bundle", None) is None
            or getattr(coordinator.lifecycle.current, "task_id", None) != task_id):
        raise DispatchStop("current coordinated task must be resolved before target input")
    if task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise DispatchStop("unknown preregistered task id")
    if coordinator.target_dispatch_started:
        raise DispatchStop("target-dispatch attempt already consumed; no retry")
    # Consume the task's one dispatch attempt before observation or receipt
    # callbacks. Any uncertainty after this point is terminal for this task.
    coordinator.target_dispatch_started = True

    results: list[dict] = []
    previous_sequence = coordinator.resolved_bundle.source_sequence
    for target in TARGETS:
        observation = observe()
        if (type(observation) is not dict
                or type(observation.get("sequence")) is not int
                or observation["sequence"] <= previous_sequence):
            raise DispatchStop("each target requires a newer visual observation")

        try:
            locator = coordinator.locator_for_input(observation, layout)
        except RouteStop as error:
            raise DispatchStop(str(error)) from error
        sequence = locator.get("validated_sequence")
        if type(sequence) is not int or sequence <= previous_sequence:
            raise DispatchStop("fresh locator sequence did not advance")
        previous_sequence = sequence

        receipt = build_receipt(locator, target)
        if type(receipt) is not dict:
            raise DispatchStop("image-bound target receipt required")
        clock = read_clock()
        request = compile_receipt_target_click(
            locator, clock, task_id, target, receipt)
        execution = submit(request)
        if (type(execution) is not dict
                or set(execution) != {"request_id", "terminal", "released"}
                or execution.get("request_id") != request["id"]
                or execution.get("terminal") is not True
                or execution.get("released") is not True):
            raise DispatchStop("matching terminal release receipt required; task stopped")
        results.append({"target": target, "locator": locator,
                        "request": request, "execution_receipt": execution})
    return results
