from __future__ import annotations

import hashlib
import unittest

from runtime.kernel import (
    Action, ActionKind, AuthorityLease, BackendInfo, BackendRegistry, Capability,
    ContractError, EffectOccurrence, EffectReceipt, EffectStatus, ExecutionReceipt,
    ExecutionRequest, Observation, ReleaseReceipt, RequestLifecycle, Stage,
    SupportLevel, TargetBinding,
)

H = hashlib.sha256(b"x").hexdigest()
M = hashlib.sha256(b"manifest").hexdigest()
B = hashlib.sha256(b"binding").hexdigest()
E = hashlib.sha256(b"effect").hexdigest()


def observation(sequence=7, surface="surface-a"):
    return Observation(sequence, 100, surface, H, 1280, 800, "rgb24")


def binding(sequence=7, surface="surface-a"):
    return TargetBinding("save-button", sequence, surface, B)


def lease(sequence=7, surface="surface-a", until=1000):
    return AuthorityLease(
        "lease-1", sequence, surface, until,
        frozenset({ActionKind.POINTER, ActionKind.TEXT}),
    )


def request(sequence=7, surface="surface-a"):
    return ExecutionRequest(
        "cmd-1", M, binding(sequence, surface), lease(sequence, surface),
        (Action("a1", ActionKind.POINTER, "click"),),
    )


def released(ns=800):
    return ReleaseReceipt(ns, True, (), ())


def execution(effect=EffectOccurrence.POSSIBLE):
    return ExecutionReceipt(
        "cmd-1", "backend-1", M, "lease-1", 7, "surface-a",
        500, 700, 1, effect, released(),
    )


class ContractTests(unittest.TestCase):
    def test_request_rejects_binding_lease_sequence_mismatch(self):
        with self.assertRaises(ContractError):
            ExecutionRequest(
                "cmd", M, binding(7), lease(8),
                (Action("a", ActionKind.POINTER, "click"),),
            )

    def test_request_rejects_action_outside_lease(self):
        with self.assertRaises(ContractError):
            ExecutionRequest(
                "cmd", M, binding(), lease(),
                (Action("a", ActionKind.KEY, "Return"),),
            )

    def test_verified_release_requires_empty_input(self):
        with self.assertRaises(ContractError):
            ReleaseReceipt(10, True, ("A",), ())

    def test_unavailable_backend_cannot_advertise_capability(self):
        with self.assertRaises(ContractError):
            BackendInfo(
                "none", "darwin", SupportLevel.UNAVAILABLE,
                frozenset({Capability.OBSERVE_SCREEN}),
            )


class LifecycleTests(unittest.TestCase):
    def make_authorized(self):
        flow = RequestLifecycle()
        flow.record_observation(observation())
        flow.bind(binding())
        flow.authorize(lease(), now_ns=200)
        return flow

    def test_happy_path(self):
        flow = self.make_authorized()
        req = request()
        flow.begin_execution(req, now_ns=300)
        flow.record_execution(execution(EffectOccurrence.OBSERVED))
        flow.record_effect(EffectReceipt("cmd-1", M, 900, EffectStatus.VERIFIED, E))
        result = flow.outcome()
        self.assertEqual(result.stage, Stage.VERIFIED)
        self.assertTrue(result.effect_occurred)
        self.assertTrue(result.effect_verified)
        self.assertTrue(result.release_verified)

    def test_contradiction_preserves_effect_occurrence(self):
        flow = self.make_authorized()
        flow.begin_execution(request(), now_ns=300)
        flow.record_execution(execution(EffectOccurrence.OBSERVED))
        flow.record_effect(EffectReceipt("cmd-1", M, 900, EffectStatus.CONTRADICTED, E))
        result = flow.outcome()
        self.assertEqual(result.stage, Stage.CONTRADICTED)
        self.assertTrue(result.effect_occurred)
        self.assertFalse(result.effect_verified)

    def test_stale_binding_refused(self):
        flow = RequestLifecycle()
        flow.record_observation(observation(sequence=8))
        with self.assertRaises(ContractError):
            flow.bind(binding(sequence=7))

    def test_other_surface_binding_refused(self):
        flow = RequestLifecycle()
        flow.record_observation(observation(surface="surface-a"))
        with self.assertRaises(ContractError):
            flow.bind(binding(surface="surface-b"))

    def test_expired_lease_refused(self):
        flow = RequestLifecycle()
        flow.record_observation(observation())
        flow.bind(binding())
        with self.assertRaises(ContractError):
            flow.authorize(lease(until=300), now_ns=300)

    def test_authority_can_expire_between_authorize_and_execute(self):
        flow = RequestLifecycle()
        flow.record_observation(observation())
        flow.bind(binding())
        short = lease(until=300)
        flow.authorize(short, now_ns=200)
        req = ExecutionRequest(
            "cmd-1", M, binding(), short,
            (Action("a1", ActionKind.POINTER, "click"),),
        )
        with self.assertRaises(ContractError):
            flow.begin_execution(req, now_ns=300)

    def test_receipt_manifest_mismatch_refused(self):
        flow = self.make_authorized()
        flow.begin_execution(request(), now_ns=300)
        wrong = ExecutionReceipt(
            "cmd-1", "backend-1", H, "lease-1", 7, "surface-a",
            500, 700, 1, EffectOccurrence.POSSIBLE, released(),
        )
        with self.assertRaises(ContractError):
            flow.record_execution(wrong)

    def test_terminal_execution_requires_release(self):
        flow = self.make_authorized()
        flow.begin_execution(request(), now_ns=300)
        bad_release = ReleaseReceipt(800, False, ("A",), ())
        receipt = ExecutionReceipt(
            "cmd-1", "backend-1", M, "lease-1", 7, "surface-a",
            500, 700, 1, EffectOccurrence.POSSIBLE, bad_release,
        )
        with self.assertRaises(ContractError):
            flow.record_execution(receipt)

    def test_stop_with_active_authority_requires_release(self):
        flow = self.make_authorized()
        with self.assertRaises(ContractError):
            flow.stop("cancelled")
        flow.stop("cancelled", release=released())
        self.assertEqual(flow.outcome().stage, Stage.STOPPED)

    def test_effect_receipt_cross_command_refused(self):
        flow = self.make_authorized()
        flow.begin_execution(request(), now_ns=300)
        flow.record_execution(execution())
        with self.assertRaises(ContractError):
            flow.record_effect(EffectReceipt("other", M, 900, EffectStatus.VERIFIED, E))


class FakeBackend:
    def __init__(self, support=SupportLevel.EXPERIMENTAL):
        self.support = support

    def probe(self):
        caps = frozenset() if self.support is SupportLevel.UNAVAILABLE else frozenset(
            {Capability.OBSERVE_SCREEN, Capability.RELEASE_ALL}
        )
        return BackendInfo("fake", "test", self.support, caps)

    def observe(self):
        return observation()

    def execute(self, request):
        return execution()

    def release_all(self):
        return released()


class RegistryTests(unittest.TestCase):
    def test_registry_selects_without_importing_platform_code(self):
        registry = BackendRegistry()
        registry.register("test", FakeBackend)
        self.assertEqual(registry.registered_platforms(), ("test",))
        self.assertEqual(registry.create("test").probe().backend_name, "fake")

    def test_missing_backend_is_explicit(self):
        registry = BackendRegistry()
        self.assertIsNone(registry.probe("win32"))
        with self.assertRaises(LookupError):
            registry.create("win32")

    def test_unavailable_backend_refuses_creation(self):
        registry = BackendRegistry()
        registry.register("darwin", lambda: FakeBackend(SupportLevel.UNAVAILABLE))
        with self.assertRaises(RuntimeError):
            registry.create("darwin")

    def test_duplicate_registration_refused(self):
        registry = BackendRegistry()
        registry.register("linux", FakeBackend)
        with self.assertRaises(ContractError):
            registry.register("linux", FakeBackend)


if __name__ == "__main__":
    unittest.main()
