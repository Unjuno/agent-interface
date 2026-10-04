"""Typed effect evidence cannot predate the execution it reports on."""
from __future__ import annotations

import unittest

from runtime.kernel import (
    Action, ActionKind, AuthorityLease, ContractError, EffectOccurrence,
    EffectReceipt, EffectStatus, ExecutionReceipt, ExecutionRequest,
    InputTransition, InputTransitionReceipt, Observation, ReleaseReceipt,
    RequestLifecycle, Stage, TargetBinding,
)

H = "a" * 64
M = "b" * 64
B = "c" * 64
E = "d" * 64


def executed_flow():
    flow = RequestLifecycle()
    observation = Observation(7, 100, "surface", H, 10, 10, "rgb24")
    binding = TargetBinding("target", 7, "surface", B)
    lease = AuthorityLease("lease", 7, "surface", 1000, frozenset({ActionKind.KEY}))
    request = ExecutionRequest("command", M, binding, lease,
                               (Action("action", ActionKind.KEY, "press-release"),))
    flow.record_observation(observation)
    flow.bind(binding)
    flow.authorize(lease, now_ns=200)
    flow.begin_execution(request, now_ns=400)
    flow.record_execution(ExecutionReceipt(
        "command", "backend", M, "lease", 7, "surface", 600, 800, 1,
        EffectOccurrence.OBSERVED, ReleaseReceipt(900, True),
        (InputTransitionReceipt("action", "Return", InputTransition.DOWN, 610, 611),
         InputTransitionReceipt("action", "Return", InputTransition.UP, 700, 701)),
    ))
    return flow


class EffectStartEpochTests(unittest.TestCase):
    def test_key_action_without_transition_timestamps_is_refused(self):
        flow = RequestLifecycle()
        observation = Observation(7, 100, "surface", H, 10, 10, "rgb24")
        binding = TargetBinding("target", 7, "surface", B)
        lease = AuthorityLease("lease", 7, "surface", 1000, frozenset({ActionKind.KEY}))
        request = ExecutionRequest("command", M, binding, lease,
                                   (Action("action", ActionKind.KEY, "press-release"),))
        flow.record_observation(observation)
        flow.bind(binding)
        flow.authorize(lease, now_ns=200)
        flow.begin_execution(request, now_ns=400)
        receipt = ExecutionReceipt(
            "command", "backend", M, "lease", 7, "surface", 600, 800, 1,
            EffectOccurrence.NONE, ReleaseReceipt(900, True),
        )
        with self.assertRaisesRegex(ContractError, "requires per-control transition evidence"):
            flow.record_execution(receipt)
        self.assertIsNone(flow.execution)

    def test_pre_start_observation_refused_for_every_status(self):
        # Omitting the new guard must admit these typed stale receipts.
        for status in EffectStatus:
            for ns in (0, 400, 599):
                with self.subTest(status=status.value, ns=ns):
                    flow = executed_flow()
                    with self.assertRaises(ContractError):
                        flow.record_effect(EffectReceipt("command", M, ns, status, E))

    def test_rejection_preserves_execution_and_allows_valid_effect(self):
        flow = executed_flow()
        original_request = flow.request
        original_execution = flow.execution
        with self.assertRaises(ContractError):
            flow.record_effect(EffectReceipt("command", M, 599, EffectStatus.VERIFIED, E))
        self.assertEqual(flow.stage, Stage.EXECUTED)
        self.assertIsNone(flow.effect)
        self.assertIs(flow.request, original_request)
        self.assertIs(flow.execution, original_execution)
        self.assertEqual(flow.execution_started_ns, 400)
        flow.record_effect(EffectReceipt("command", M, 600, EffectStatus.VERIFIED, E))
        result = flow.outcome()
        self.assertEqual(result.command_id, "command")
        self.assertTrue(result.effect_occurred)
        self.assertTrue(result.effect_verified)
        self.assertTrue(result.release_verified)

    def test_recorded_start_not_only_accepted_begin_is_the_floor(self):
        # A wrong comparison to accepted begin=400 would admit observed=500.
        flow = executed_flow()
        with self.assertRaises(ContractError):
            flow.record_effect(EffectReceipt("command", M, 500, EffectStatus.VERIFIED, E))
        self.assertEqual(flow.stage, Stage.EXECUTED)
        self.assertIsNone(flow.effect)

    def test_equal_recorded_start_keeps_each_terminal_status(self):
        for status, stage, verified in (
            (EffectStatus.VERIFIED, Stage.VERIFIED, True),
            (EffectStatus.CONTRADICTED, Stage.CONTRADICTED, False),
            (EffectStatus.UNAVAILABLE, Stage.UNAVAILABLE, False),
        ):
            with self.subTest(status=status.value):
                flow = executed_flow()
                receipt = EffectReceipt("command", M, 600, status, E)
                flow.record_effect(receipt)
                self.assertIs(flow.effect, receipt)
                result = flow.outcome()
                self.assertEqual(result.stage, stage)
                self.assertEqual(result.effect_verified, verified)
                self.assertTrue(result.effect_occurred)
                self.assertTrue(result.release_verified)

    def test_during_execution_and_late_delivery_remain_representable(self):
        # An ended_ns or lease-expiry floor/ceiling would wrongly refuse controls.
        for ns in (700, 799, 800, 900, 1000, 2000):
            with self.subTest(ns=ns):
                flow = executed_flow()
                flow.record_effect(EffectReceipt("command", M, ns, EffectStatus.VERIFIED, E))
                self.assertTrue(flow.outcome().effect_verified)

    def test_wrong_command_or_manifest_remains_refused(self):
        for command, manifest in (("other", M), ("command", H)):
            for ns in (599, 600):
                with self.subTest(command=command, ns=ns):
                    flow = executed_flow()
                    original_execution = flow.execution
                    with self.assertRaises(ContractError):
                        flow.record_effect(EffectReceipt(command, manifest, ns, EffectStatus.VERIFIED, E))
                    self.assertEqual(flow.stage, Stage.EXECUTED)
                    self.assertIsNone(flow.effect)
                    self.assertIs(flow.execution, original_execution)


if __name__ == "__main__":
    unittest.main()
