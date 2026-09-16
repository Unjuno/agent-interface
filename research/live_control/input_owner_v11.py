"""Telemetry-only InputOwner v11: timestamp ordinary key-up call boundaries.

v10 remains the authority implementation. This wrapper does not change the owner
thread, focus/lease checks, cancellation, expiry, or X11 injection semantics.
For ``up`` only, it records a caller-side request time and a caller-side return
time. Because v10 returns from ``up`` only after its owner thread has issued
KeyRelease and completed ``d.sync()``, ``release_ack_ns`` is a conservative
post-sync acknowledgement boundary, not the exact server-side transition time.
"""
import time

from input_owner_v10 import InputOwner as Previous


class InputOwner(Previous):
    @staticmethod
    def _interruption_snapshot(lease):
        if lease is None or not hasattr(lease, 'interruption_snapshot'):
            return None
        return lease.interruption_snapshot()

    def call(self, operation, lease=None, key=None):
        if operation != 'up':
            return super().call(operation, lease, key)

        # Timestamp immediately before delegation; do not add a pre-release
        # owner/state query that would delay the release being measured.
        requested_ns = time.perf_counter_ns()
        result = super().call(operation, lease, key)
        ack_ns = time.perf_counter_ns()
        after = self._interruption_snapshot(lease)

        # v10 deliberately returned None for ordinary up. A different return
        # contract would mean this wrapper is no longer a telemetry-only delta.
        if result is not None:
            raise AssertionError('InputOwner v10 up contract changed')

        interruption = after
        inner = (interruption.get('record') if isinstance(interruption, dict) and
                 isinstance(interruption.get('record'), dict) else interruption)
        interruption_verified_ns = (inner.get('verified_ns')
                                    if isinstance(inner, dict) else None)
        if interruption is None:
            attribution = 'ordinary_up'
        elif (type(interruption_verified_ns) is int and
              interruption_verified_ns <= requested_ns):
            attribution = 'superseded_before_request'
        else:
            attribution = 'raced_owner_release'

        record = dict(
            event='input_release_ack',
            key=key,
            release_requested_ns=requested_ns,
            release_ack_ns=ack_ns,
            release_attribution=attribution,
            owner_id=self.owner_id,
            valid_until_ns=getattr(lease, 'deadline', None),
            grants_input_authority=False,
        )
        if isinstance(inner, dict):
            record['interruption_reason'] = inner.get('reason')
            record['interruption_verified_ns'] = inner.get('verified_ns')
        return record
