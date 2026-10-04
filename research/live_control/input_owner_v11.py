"""Telemetry wrapper for InputOwner v10 ordinary release RPCs.

Legacy v10 ``up`` and ``button_up`` calls return ``None`` and can be no-ops
when the owner has no matching held input. This version uses the additive
receipt call path so the owner thread reports resolved key identity and
whether it issued a release request followed by ``d.sync()``. The caller still
brackets that call with ``perf_counter_ns``. Applied releases carry a censored
transition interval; no-op receipts carry only the caller interval and do not
claim a transition. Neither form proves hardware state or application
consumption.
"""
from __future__ import annotations

import time

from input_owner_v10 import InputOwner as Previous


RELEASE_OPS = frozenset({"up", "button_up"})


class InputOwner(Previous):
    """V10 semantics plus interval-censored ordinary release receipts."""

    def call(self, operation, lease=None, key=None):
        if operation not in RELEASE_OPS:
            return super().call(operation, lease, key)

        call_started_ns = time.perf_counter_ns()
        # Important: if the underlying owner raises, no receipt is fabricated.
        result = super().call_release_with_receipt(operation, lease, key)
        call_returned_ns = time.perf_counter_ns()
        if (type(result) is not dict or result.get("event") != "input_release_result"
                or result.get("operation") != operation
                or type(result.get("release_applied")) is not bool
                or type(result.get("x11_release_request_issued")) is not bool
                or type(result.get("x11_sync_completed")) is not bool
                or result["release_applied"] != result["x11_release_request_issued"]
                or result["release_applied"] != result["x11_sync_completed"]):
            raise RuntimeError("v10 ordinary release result was malformed")
        if operation == "up" and type(result.get("keycode")) is not int:
            raise RuntimeError("v10 key release omitted resolved keycode")
        if operation == "button_up" and result.get("button") != key:
            raise RuntimeError("v10 button release identity mismatch")
        if call_returned_ns < call_started_ns:
            raise RuntimeError("release telemetry clock moved backwards")

        return {
            "event": "input_release_rpc",
            "operation": operation,
            "payload": key,
            "owner_id": self.owner_id,
            "intent_token": getattr(lease, "intent_token", None),
            "call_started_ns": call_started_ns,
            "call_returned_ns": call_returned_ns,
            "call_interval_ns": [call_started_ns, call_returned_ns],
            "call_interval_width_ns": call_returned_ns - call_started_ns,
            "release_transition_interval_ns": ([call_started_ns, call_returned_ns]
                                             if result["release_applied"] else None),
            "interval_width_ns": (call_returned_ns - call_started_ns
                                  if result["release_applied"] else None),
            "valid_until_ns": getattr(lease, "deadline", None),
            "release_applied": result["release_applied"],
            "keycode": result.get("keycode"),
            "button": result.get("button"),
            "x11_release_request_issued": result["x11_release_request_issued"],
            "x11_sync_completed_before_return": result["x11_sync_completed"],
            "x11_release_and_sync_completed_before_return": result["release_applied"],
            "continuous_physical_state_sampled": False,
            "application_consumption_observed": False,
            "grants_input_authority": False,
        }
