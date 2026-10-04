"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


class Map01V39CoastTests(unittest.TestCase):
    def test_rejected_action_followup_keeps_model_turn_alive_on_damage(self):
        previous = {"iteration": 1, "model_action_discarded": True,
                    "action": {"state": "active", "next_cover": [
                        {"action": "strafe_left", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}
        commands, validity, source = controller.reusable_cover([previous])
        self.assertEqual((commands, validity, source), ([], None, None))
        default_receipt = {"authored": None, "effective": {
            "hard_minimum": 85, "maximum_health_loss": 0}}
        selected, receipt = controller.select_cover_monitor(
            object(), default_receipt, commands, source)
        self.assertIsInstance(selected, controller.UnauthoredCoastMonitor)
        self.assertEqual(receipt["monitor_mode"], "unauthored_coast_no_policy")
        self.assertEqual(selected.event_types, frozenset())
        self.assertEqual(selected.soft_event_count, 0)
        self.assertIsNone(selected.latest_soft_event)
        # The exact frame still updates latest in the caller, while the
        # unauthored coast publishes no policy event that can interrupt.
        self.assertEqual(default_receipt["effective"]["hard_minimum"], 85)

    def test_authored_cover_still_uses_original_guard(self):
        guard = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        selected, receipt = controller.select_cover_monitor(
            guard, {"authored": authored},
            [{"action": "strafe_left", "extent": "short"}], 0)
        self.assertIs(selected, guard)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")
        self.assertEqual(receipt["authored"], authored)

    def test_cover_acceptance_wait_monitors_observations_before_planning(self):
        monitor = object()
        invalidation = {"reason": "health_below_floor"}
        calls = []

        def wait(predicate, observation_monitor):
            calls.append(observation_monitor)
            return {"event": "policy_invalidation", "invalidation": invalidation}

        result = controller.wait_for_cover_acceptance(wait, "cover-0", monitor)
        self.assertIs(calls[0], monitor)
        self.assertEqual(result["invalidation"], invalidation)

    def test_preplanning_invalidation_cancels_and_verifies_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass

        class Process:
            def __init__(self): self.stdin = Stdin()

        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        process = Process()
        result = controller.cancel_unplanned_invalidated_cover(
            process, lambda predicate: terminal, "cover-0")
        self.assertIs(result, terminal)
        self.assertIn('"op": "cancel"', process.stdin.writes[0])

    def test_running_renewal_invalidation_interrupts_and_verifies_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass

        class Process:
            def __init__(self): self.stdin = Stdin()

        class Planner:
            def __init__(self): self.interrupted = []
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}

        terminal = {"event": "terminal", "id": "cover-1", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        process, planner, handle = Process(), Planner(), object()
        planner_interrupt, observed = controller.cancel_invalidated_cover(
            planner, handle, process, lambda predicate: terminal, "cover-1")
        self.assertEqual(planner.interrupted, [handle])
        self.assertIs(observed, terminal)
        self.assertEqual(planner_interrupt, {"status": "interrupted"})
        self.assertIn('"op": "cancel"', process.stdin.writes[0])


if __name__ == "__main__":
    unittest.main()
