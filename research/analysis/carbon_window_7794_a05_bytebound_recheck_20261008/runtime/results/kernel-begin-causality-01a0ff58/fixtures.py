"""Authored input records. No OS/backend operation is performed."""
from frozen_kernel import (
    Action, ActionKind, AuthorityLease, EffectOccurrence, ExecutionReceipt,
    ExecutionRequest, Observation, ReleaseReceipt, TargetBinding,
)

M = 'a' * 64


def begun(flow_class, begin=3):
    flow = flow_class()
    obs = Observation(1, 0, 'test-surface', 'b' * 64, 1, 1, 'synthetic')
    binding = TargetBinding('test-target', 1, 'test-surface', 'c' * 64)
    lease = AuthorityLease('test-lease', 1, 'test-surface', 10, frozenset({ActionKind.TEXT}))
    req = ExecutionRequest('test-command', M, binding, lease, (Action('a1', ActionKind.TEXT, 'fixture'),))
    flow.record_observation(obs)
    flow.bind(binding)
    flow.authorize(lease, now_ns=0)
    flow.begin_execution(req, now_ns=begin)
    return flow


def receipt(start=3, end=4, matching=True):
    return ExecutionReceipt('test-command', 'fixture-receipt', M if matching else 'd' * 64,
        'test-lease', 1, 'test-surface', start, end, 1,
        EffectOccurrence.POSSIBLE, ReleaseReceipt(max(7, end), True))
