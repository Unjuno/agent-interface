"""Compile, but never send, a sequence-bound target click request."""

from __future__ import annotations

from pathlib import Path
import sys

LIVE = Path(__file__).resolve().parents[2] / "live_control"
sys.path.insert(0, str(LIVE))
from receipt_target_admission_v1 import validate as validate_receipt  # noqa: E402


class DispatchStop(RuntimeError):
    """Fail-closed refusal to compile stale or malformed pointer input."""


def compile_pointer_click(locator: dict, clock: dict, task_id: str,
                          target: str, lifetime_ns: int = 5_000_000_000,
                          protocol: str = "mindustry-v1") -> dict:
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
    if protocol not in {"mindustry-v1", "interactive-v27"}:
        raise DispatchStop("unknown submit protocol dialect")
    delivery_id = locator.get("delivery_id")
    if protocol == "interactive-v27" and (type(delivery_id) is not str or not delivery_id):
        raise DispatchStop("successfully flushed observation delivery id required")
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
    request = {
        "op": "submit",
        "id": f"{task_id}-{action}",
        "expected_sequence": sequence,
        "valid_until_ns": runtime_ns + lifetime_ns,
        "steps": steps,
        "authority": "compiled request only; not dispatched or admitted",
    }
    if protocol == "interactive-v27":
        request["decision_evidence"] = {
            "delivery_id": delivery_id,
            "observation_sequence": sequence,
            "producer": "assistant",
        }
        request["authority"] = (
            "compiled request only; decision evidence is caller-declared, not input authority")
    return request


def compile_receipt_target_click(locator: dict, clock: dict, task_id: str,
                                 target: str, receipt: dict,
                                 lifetime_ns: int = 5_000_000_000) -> dict:
    """Compile one Mindustry click through the proven post-model receipt gate.

    The receipt's source observation must be the locator's original image; its
    decision boundary is the fresh locator observation. The task-specific
    backend captures another image after submit and admits a point only when
    every declared pixel dependency still matches.
    """
    if type(locator) is not dict or locator.get("authority") != (
            "locator only; explicit caller action still required"):
        raise DispatchStop("non-authorizing target locator required")
    if target not in {"palette_point", "target_point"}:
        raise DispatchStop("unsupported target point")
    if type(clock) is not dict or type(clock.get("sequence")) is not int:
        raise DispatchStop("socket clock sequence required")
    sequence = locator.get("validated_sequence")
    if type(sequence) is not int or sequence < 1 or clock["sequence"] != sequence:
        raise DispatchStop("socket sequence differs from fresh locator")
    source_sequence = locator.get("source_sequence")
    if type(source_sequence) is not int or source_sequence < 1:
        raise DispatchStop("receipt source observation sequence required")
    point = locator.get(target)
    if (type(point) is not list or len(point) != 2
            or any(type(value) is not int or value < 0 for value in point)):
        raise DispatchStop("validated integer target point required")
    if type(receipt) is not dict:
        raise DispatchStop("receipt target specification required")
    if (receipt.get("point") != point
            or receipt.get("source_sequence") != source_sequence
            or receipt.get("decision_after_sequence") != sequence):
        raise DispatchStop("receipt does not bind this locator and decision boundary")
    try:
        validate_receipt(receipt)
    except ValueError as error:
        raise DispatchStop("invalid receipt target specification: " + str(error)) from error
    runtime_ns = clock.get("runtime_ns")
    if type(runtime_ns) is not int or runtime_ns < 0:
        raise DispatchStop("monotonic socket clock required")
    if type(lifetime_ns) is not int or lifetime_ns <= 0:
        raise DispatchStop("positive input validity lifetime required")
    if type(task_id) is not str or task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise DispatchStop("unknown preregistered task id")
    action = "select-conveyor" if target == "palette_point" else "place-conveyor"
    return {
        "op": "submit",
        "id": f"{task_id}-{action}",
        "expected_sequence": sequence,
        "valid_until_ns": runtime_ns + lifetime_ns,
        "steps": [{"op": "pointer_click_receipt_target", "receipt": receipt,
                   "button": 1, "duration_ms": 40}, {"op": "observe"}],
        "authority": "compiled request only; target receipt is revalidated by runtime",
    }
