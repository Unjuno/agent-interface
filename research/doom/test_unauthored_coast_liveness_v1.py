import unittest

from unauthored_coast_liveness_v1 import (
    UnauthoredCoastMonitor, invalidation_handoff_sequence,
    wait_for_fresh_observation)


def source_signal(value=85):
    return {"status": "observed", "signal_id": "health", "value": value,
            "sequence": 10, "capture_ns": 1_000_000_000,
            "binding": {"pid": 7, "window": "map01"}}


def typed_event(sequence, value, *, status="observed"):
    binding = {"pid": 7, "window": "map01"}
    health = {"signal_id": "health", "status": status,
              "value": value if status == "observed" else None,
              "sequence": sequence, "capture_ns": 1_000_000_000 + sequence * 1_000_000,
              "binding": binding}
    return {"event": "typed_observation", "schema": "doom-typed-observation-v1",
            "sequence": sequence, "capture_ns": health["capture_ns"],
            "pointer_binding": binding, "signals": {"health": health},
            "artifact_published": False, "grants_input_authority": False}


class UnauthoredCoastLivenessTests(unittest.TestCase):
    def test_typed_health_crossing_invalidates_without_granting_authority(self):
        monitor = UnauthoredCoastMonitor(source_signal(), 2)
        event = monitor.observe(typed_event(11, 79))
        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")
        self.assertTrue(event["outcome"]["requires_new_decision"])
        self.assertFalse(event["outcome"]["grants_input_authority"])
        self.assertEqual(monitor.event_types, frozenset({"typed_observation"}))

    def test_small_health_change_coalesces_without_interrupt(self):
        monitor = UnauthoredCoastMonitor(source_signal(), 2)
        self.assertIsNone(monitor.observe(typed_event(11, 82)))
        self.assertEqual(monitor.soft_event_count, 1)

    def test_unknown_health_fails_closed(self):
        monitor = UnauthoredCoastMonitor(source_signal(), 2)
        event = monitor.observe(typed_event(11, None, status="unknown"))
        self.assertEqual(event["outcome"]["status"], "UNKNOWN")
        self.assertTrue(event["outcome"]["requires_new_decision"])

    def test_waits_for_matching_or_newer_image_before_replan(self):
        events = iter([
            {"event": "observation", "sequence": 10, "image": "stale"},
            {"event": "observation", "sequence": 11, "image": "paired"},
        ])

        def wait(predicate):
            while True:
                row = next(events)
                if predicate(row):
                    return row

        self.assertEqual(wait_for_fresh_observation(wait, 11)["image"], "paired")

    def test_uses_fresh_image_already_drained_while_waiting_for_release(self):
        current = {"event": "observation", "sequence": 11, "image": "paired"}
        self.assertIs(wait_for_fresh_observation(
            lambda _predicate: self.fail("must not wait after image was drained"),
            11, latest_observation=lambda: current), current)

    def test_boolean_sequence_is_rejected(self):
        with self.assertRaises(ValueError):
            wait_for_fresh_observation(lambda _predicate: None, True)

    def test_malformed_invalidation_sequence_waits_for_next_frame(self):
        latest = {"event": "observation", "sequence": 10}
        self.assertEqual(invalidation_handoff_sequence(True, latest), 11)
        self.assertEqual(invalidation_handoff_sequence(12, latest), 12)


if __name__ == "__main__":
    unittest.main()

