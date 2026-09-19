"""Bounded long-poll wrapper around archived artifact checkpoints."""
import time

from effect_checkpoint_v2 import Checkpoints as Previous, archived_sample


def waiting_sample(path, contract, archive, wait_ms, poll_ms):
    deadline = time.perf_counter_ns() + wait_ms * 1_000_000
    attempts = 0
    first_started_ns = None
    while True:
        evidence = archived_sample(path, contract, archive)
        attempts += 1
        if first_started_ns is None:
            first_started_ns = evidence['started_ns']
        if evidence['status'] == 'VERIFIED' or time.perf_counter_ns() >= deadline:
            result = dict(evidence)
            result.update(
                wait_requested_ms=wait_ms,
                poll_requested_ms=poll_ms,
                sample_attempts=attempts,
                wait_started_ns=first_started_ns,
                wait_finished_ns=time.perf_counter_ns(),
                wait_scope=('bounded verifier-side polling; one caller request; '
                            'not an application event subscription'),
            )
            return result
        time.sleep(min(poll_ms / 1000, max(0, (deadline - time.perf_counter_ns()) / 1e9)))


class Checkpoints(Previous):
    def request(self, path, contract, metadata, verifier=None, *, wait_ms=0, poll_ms=50):
        if type(wait_ms) is not int or not 0 <= wait_ms <= 10_000:
            raise ValueError('wait_ms must be integer 0..10000')
        if type(poll_ms) is not int or not 10 <= poll_ms <= 500:
            raise ValueError('poll_ms must be integer 10..500')
        if wait_ms and poll_ms > wait_ms:
            raise ValueError('poll_ms cannot exceed positive wait_ms')
        if verifier is not None:
            raise ValueError('custom verifier unsupported by bounded wrapper')
        return super().request(
            path, contract, metadata,
            lambda target, expected: waiting_sample(
                target, expected, self.archive, wait_ms, poll_ms))
