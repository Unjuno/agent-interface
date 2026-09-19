"""Telemetry-only wrapper for InputOwner v10 ordinary release RPCs.

The v10 owner performs X11 KeyRelease/ButtonRelease followed by ``d.sync()`` for
ordinary ``up`` / ``button_up`` operations, but returns ``None``.  This version
keeps v10's owner thread and authority semantics unchanged and brackets those
existing calls on the caller's ``perf_counter_ns`` clock.

The resulting receipt proves only that the v10 owner call containing X11 release
and sync completed somewhere inside ``[call_started_ns, call_returned_ns]``.  It
is not a hardware-state timestamp and does not prove application consumption.
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
        result = super().call(operation, lease, key)
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
            "interval_width_ns": call_returned_ns - call_started_ns,
            "valid_until_ns": getattr(lease, "deadline", None),
            "x11_release_and_sync_completed_before_return": True,
            "continuous_physical_state_sampled": False,
            "application_consumption_observed": False,
            "grants_input_authority": False,
        }
