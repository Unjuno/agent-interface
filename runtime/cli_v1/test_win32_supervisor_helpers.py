import unittest
import os
from tempfile import TemporaryDirectory

from runtime.cli_v1.win32_supervisor_helpers import _observe, _parse_obligations, _recover


GENERATION = "a" * 64


class FakeBackend:
    def __init__(self, targets, generation=GENERATION, states=None,
                 release_verified=True):
        self.targets = targets
        self.generation = generation
        self.states = dict(states or {})
        self.release_verified = release_verified
        self.held_keys = {}
        self.held_key_targets = {}
        self.held_buttons = set()
        self.held_button_targets = {}
        self.pending_unicode_ups = set()
        self.release_calls = 0
        self.release_snapshot = None
        self.closed = False

    def target_generation(self, target):
        if target not in self.targets:
            raise RuntimeError("unknown target")
        return self.generation

    def release_all(self):
        self.release_calls += 1
        self.release_snapshot = (dict(self.held_keys), set(self.held_buttons),
                                 set(self.pending_unicode_ups))
        self.held_keys.clear()
        self.held_key_targets.clear()
        self.held_buttons.clear()
        self.held_button_targets.clear()
        self.pending_unicode_ups.clear()
        return {"verified": self.release_verified,
                "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "buttons_unknown": []}

    def _key_down_state(self, vk, target):
        return self.states.get((vk, target), False)

    def close(self):
        self.closed = True


class NativeWin32SupervisorHelperTests(unittest.TestCase):
    def request(self, **changes):
        request = {"operation_id": "1" * 32,
            "target_generation": GENERATION, "recovery_id": "2" * 32,
            "request_id": "2" * 32, "deadline_ns": 100,
            "obligations": ["key:fixture:CTRL", "button:fixture:left",
                            "unicode:0041"]}
        request.update(changes)
        return request

    def test_parse_obligations_retains_each_input_domain(self):
        result = _parse_obligations(self.request()["obligations"])
        self.assertEqual(result, {"keys": [("fixture", "CTRL")],
            "buttons": [("fixture", "left")], "unicode": [0x41]})

    def test_recovery_releases_only_frozen_obligations_after_generation_check(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets)
            instances.append(backend)
            return backend
        result = _recover(self.request(), backend_factory=factory,
                          clock_ns=lambda: 10,
                          configured_targets={"fixture": 44})
        self.assertIs(result["release_accepted"], True)
        self.assertEqual(result["operation_id"], "1" * 32)
        self.assertEqual(instances[0].release_snapshot,
            ({"CTRL": 0x11}, {"left"}, {0x41}))
        self.assertEqual(instances[0].release_calls, 1)
        self.assertTrue(instances[0].closed)

    def test_recovery_generation_mismatch_sends_no_up(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets, generation="b" * 64)
            instances.append(backend)
            return backend
        with self.assertRaisesRegex(RuntimeError, "TARGET_GENERATION_CHANGED"):
            _recover(self.request(), backend_factory=factory,
                clock_ns=lambda: 10, configured_targets={"fixture": 44})
        self.assertEqual(instances[0].release_calls, 0)
        self.assertTrue(instances[0].closed)

    def test_recovery_refuses_before_opening_backend_after_deadline(self):
        opened = []
        with self.assertRaises(TimeoutError):
            _recover(self.request(), backend_factory=lambda targets: opened.append(targets),
                clock_ns=lambda: 100, configured_targets={"fixture": 44})
        self.assertEqual(opened, [])

    def test_unicode_only_recovery_uses_configured_single_target(self):
        instances = []
        def factory(targets):
            backend = FakeBackend(targets)
            instances.append(backend)
            return backend
        result = _recover(self.request(obligations=["unicode:0041"]),
            backend_factory=factory, clock_ns=lambda: 10,
            configured_targets={"fixture": 44})
        self.assertTrue(result["release_accepted"])
        self.assertEqual(instances[0].release_snapshot,
            ({}, set(), {0x41}))

    def test_unicode_only_observer_binds_readback_to_configured_generation(self):
        backend = FakeBackend({"fixture": 44})
        result = _observe(self.request(obligations=["unicode:0041"]),
            backend_factory=lambda _targets: backend, clock_ns=lambda: 50,
            configured_targets={"fixture": 44})
        self.assertTrue(result["neutral"])
        self.assertEqual(result["unicode_event_units"], 1)

    def test_observer_requires_neutral_known_key_and_button_states(self):
        backend = FakeBackend({"fixture": 44})
        result = _observe(self.request(), backend_factory=lambda _targets: backend,
            clock_ns=lambda: 50, configured_targets={"fixture": 44})
        self.assertTrue(result["neutral"])
        self.assertEqual(result["unicode_event_units"], 1)
        self.assertTrue(backend.closed)

    def test_observer_unknown_state_is_not_neutral(self):
        backend = FakeBackend({"fixture": 44}, states={(0x11, "fixture"): None})
        result = _observe(self.request(), backend_factory=lambda _targets: backend,
            clock_ns=lambda: 50, configured_targets={"fixture": 44})
        self.assertFalse(result["neutral"])

    @unittest.skipUnless(os.name == "nt", "native helper startup is Windows-only")
    def test_native_components_start_helpers_before_any_operation(self):
        from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components
        with TemporaryDirectory() as output:
            owner, producer = create_native_win32_components(
                {"fixture": 1}, output)
            try:
                self.assertEqual(owner.mode, "supervised-win32")
                self.assertFalse(owner.synthetic_only)
                self.assertEqual(owner.list_results(), [])
            finally:
                self.assertEqual(owner.close()["status"], "closed")
        self.assertIsNotNone(producer)


if __name__ == "__main__":
    unittest.main()
