import unittest

from research.live_control.deterministic_invalidation_injector_v1 import (
    CompositeInvalidationMonitor, OneShotInvalidationInjector,
)


class Natural:
    def __init__(self, result=None):
        self.result = result
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        return self.result


class DeterministicInvalidationInjectorTests(unittest.TestCase):
    def test_fires_once_on_selected_iteration_and_never_grants_input(self):
        ticks = iter([900])
        owner = OneShotInvalidationInjector(
            target_iteration=2, after_observations=2, clock=lambda: next(ticks))
        wrong = owner.bind(iteration=1, source_sequence=10)
        self.assertIsNone(wrong.observe({"sequence": 11, "capture_ns": 100}))
        bound = owner.bind(iteration=2, source_sequence=20)
        self.assertIsNone(bound.observe({"sequence": 21, "capture_ns": 200}))
        hit = bound.observe({"sequence": 22, "capture_ns": 300, "image": "22.png"})
        self.assertEqual(hit["outcome"]["status"], "INJECTED_INVALIDATION")
        self.assertFalse(hit["outcome"]["grants_input_authority"])
        self.assertEqual(hit["injection"]["observations_seen"], 2)
        self.assertIsNone(bound.observe({"sequence": 23, "capture_ns": 400}))

    def test_natural_invalidation_has_priority(self):
        natural_hit = {"outcome": {"status": "INVALIDATED"}}
        natural = Natural(natural_hit)
        owner = OneShotInvalidationInjector(target_iteration=0, after_observations=1)
        composite = CompositeInvalidationMonitor(
            natural, owner.bind(iteration=0, source_sequence=1))
        self.assertIs(composite.observe({"sequence": 2}), natural_hit)
        self.assertFalse(owner.fired)

    def test_nonadvancing_sequence_and_invalid_configuration_fail_closed(self):
        with self.assertRaises(ValueError):
            OneShotInvalidationInjector(target_iteration=-1, after_observations=1)
        with self.assertRaises(ValueError):
            OneShotInvalidationInjector(target_iteration=0, after_observations=0)
        bound = OneShotInvalidationInjector(
            target_iteration=0, after_observations=1).bind(iteration=0, source_sequence=5)
        with self.assertRaises(ValueError):
            bound.observe({"sequence": 5})


if __name__ == "__main__":
    unittest.main()
