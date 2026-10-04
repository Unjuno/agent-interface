"""Telemetry-only wrapper for InputOwner v10 ordinary release RPCs.

V10 keeps returning None for ordinary release calls. For explicit key-up only,
this wrapper passes a string-compatible telemetry key so the owner thread can
record the existing KeyRelease-to-XSync interval without another sync. The
caller-side interval remains available for queue plus owner latency. Neither
interval is a hardware-state timestamp or proof of application consumption.
"""
from __future__ import annotations

import time

from input_owner_v10 import InputOwner as Previous, _OwnerReleaseTimingKey


RELEASE_OPS = frozenset({"up", "button_up"})



class InputOwner(Previous):
    """V10 semantics plus interval-censored ordinary release receipts."""

    def call(self, operation, lease=None, key=None):
        if operation not in RELEASE_OPS:
            return super().call(operation, lease, key)

        measured_key = _OwnerReleaseTimingKey(key) if operation == "up" else key
        call_started_ns = time.perf_counter_ns()
        # Important: if the underlying owner raises, no receipt is fabricated.
        result = super().call(operation, lease, measured_key)
        call_returned_ns = time.perf_counter_ns()
        if result is not None:
            raise RuntimeError("v10 ordinary release unexpectedly returned a payload")
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
            "release_transition_interval_ns": [call_started_ns, call_returned_ns],
            "owner_thread_release_interval_ns": (
                measured_key.owner_release_interval_ns if operation == "up" else None
            ),
            "interval_width_ns": call_returned_ns - call_started_ns,
            "valid_until_ns": getattr(lease, "deadline", None),
            "x11_release_and_sync_completed_before_return": True,
            "continuous_physical_state_sampled": False,
            "application_consumption_observed": False,
            "grants_input_authority": False,
        }
