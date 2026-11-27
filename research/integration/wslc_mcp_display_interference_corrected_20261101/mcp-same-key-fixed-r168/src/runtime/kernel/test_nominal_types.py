from dataclasses import fields
from types import SimpleNamespace
import unittest

from runtime.kernel import ContractError, EffectReceipt, EffectStatus, RequestLifecycle
from runtime.kernel.test_kernel import observation, binding, lease, request, execution, released, M, E


def shaped(value, **changes):
    data = {field.name: getattr(value, field.name) for field in fields(value)}
    data.update(changes)
    return SimpleNamespace(**data)


def flow_at(stage):
    flow = RequestLifecycle()
    if stage >= 1:
        flow.record_observation(observation())
    if stage >= 2:
        flow.bind(binding())
    if stage >= 3:
        flow.authorize(lease(), now_ns=200)
    if stage >= 4:
        flow.begin_execution(request(), now_ns=300)
    if stage >= 5:
        flow.record_execution(execution())
    return flow


class TypeBoundaryTests(unittest.TestCase):
    def check_refusal(self, flow, callback):
        before = vars(flow).copy()
        with self.assertRaises(ContractError):
            callback()
        self.assertEqual(vars(flow), before)

    def test_observation_type_control(self):
        flow = flow_at(0)
        self.check_refusal(flow, lambda: flow.record_observation(shaped(observation())))

    def test_binding_shape_cannot_bypass_digest_validation(self):
        flow = flow_at(1)
        self.check_refusal(flow, lambda: flow.bind(shaped(binding(), binding_digest='bad')))

    def test_authority_shape_cannot_bypass_action_validation(self):
        flow = flow_at(2)
        self.check_refusal(flow, lambda: flow.authorize(shaped(lease(), allowed_actions=frozenset()), now_ns=200))

    def test_request_shape_cannot_bypass_nonempty_action_validation(self):
        flow = flow_at(3)
        self.check_refusal(flow, lambda: flow.begin_execution(shaped(request(), actions=()), now_ns=300))

    def test_execution_shape_cannot_bypass_interval_validation(self):
        flow = flow_at(4)
        self.check_refusal(flow, lambda: flow.record_execution(shaped(execution(), ended_ns=0)))

    def test_effect_shape_cannot_bypass_evidence_validation(self):
        flow = flow_at(5)
        effect = EffectReceipt('cmd-1', M, 900, EffectStatus.VERIFIED, E)
        self.check_refusal(flow, lambda: flow.record_effect(shaped(effect, evidence_digest='bad')))

    def test_stop_shape_cannot_assert_verified_release(self):
        flow = flow_at(4)
        self.check_refusal(flow, lambda: flow.stop('cancelled', release=SimpleNamespace(released=True)))


if __name__ == '__main__':
    unittest.main()
