"""Compile, but never send, a sequence-bound target click request."""

from __future__ import annotations


class DispatchStop(RuntimeError):
    """Fail-closed refusal to compile stale or malformed pointer input."""


def compile_pointer_click(locator: dict, clock: dict, task_id: str,
                          target: str, lifetime_ns: int = 5_000_000_000) -> dict:
    """Return one click+release-observation socket command; performs no I/O.

    A caller must get a fresh visual observation, revalidate its locator, read
    the socket clock, and dispatch this command only if the sequence is still
    identical. The returned structure is not itself an admission or receipt.
    """
    if type(locator) is not dict or locator.get("authority") != (
            "locator only; explicit caller action still required"):
        raise DispatchStop("non-authorizing target locator required")
    if target not in {"palette_point", "target_point"}:
        raise DispatchStop("unsupported target point")
    sequence = locator.get("validated_sequence")
    if type(sequence) is not int or sequence < 0:
        raise DispatchStop("validated observation sequence required")
    if type(clock) is not dict or type(clock.get("sequence")) is not int:
        raise DispatchStop("socket clock sequence required")
    if clock["sequence"] != sequence:
        raise DispatchStop("socket sequence advanced after locator validation")
    runtime_ns = clock.get("runtime_ns")
    if type(runtime_ns) is not int or runtime_ns < 0:
        raise DispatchStop("monotonic socket clock required")
    if type(lifetime_ns) is not int or lifetime_ns <= 0:
        raise DispatchStop("positive input validity lifetime required")
    point = locator.get(target)
    if (type(point) is not list or len(point) != 2
            or any(type(value) is not int or value < 0 for value in point)):
        raise DispatchStop("validated integer target point required")
    if not isinstance(task_id, str) or task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise DispatchStop("unknown preregistered task id")
    action = "select-conveyor" if target == "palette_point" else "place-conveyor"
    steps = [
        {"op": "pointer_click", "x": point[0], "y": point[1],
         "duration_ms": 40},
        {"op": "pointer_move", "x": 900, "y": 400},
    ]
    if target == "palette_point":
        steps.append({"op": "settle", "quiet_ms": 100, "timeout_ms": 1200})
    steps.append({"op": "observe"})
    return {
        "op": "submit",
        "id": f"{task_id}-{action}",
        "expected_sequence": sequence,
        "valid_until_ns": runtime_ns + lifetime_ns,
        "steps": steps,
        "authority": "compiled request only; not dispatched or admitted",
    }
