"""Controller integration regressions for typed unauthored-coast interrupts."""
import io
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v40 as controller


class _Planner:
    def interrupt(self, _handle):
        return {"requested": True}


class _Process:
    def __init__(self):
        self.stdin = io.StringIO()


def _source_signal():
    return {"status": "observed", "signal_id": "health", "value": 85,
            "sequence": 10, "capture_ns": 1_000_000_000,
            "binding": {"pid": 7, "window": "map01"}}


class Map01V40CoastTests(unittest.TestCase):
    def test_only_unauthored_empty_coast_uses_typed_health_monitor(self):
        admission = {"authored": None, "source_signal": _source_signal()}
        monitor, receipt = controller.select_cover_monitor(
            object(), admission, [], None, 2)
        self.assertIsInstance(monitor, controller.UnauthoredCoastMonitor)
        self.assertEqual(monitor.event_types, frozenset({"typed_observation"}))
        self.assertEqual(receipt["monitor_mode"],
                         "unauthored_coast_typed_health_candidate_v1")

    def test_authored_policy_guard_is_preserved(self):
        existing = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        monitor, receipt = controller.select_cover_monitor(
            existing, {"authored": authored}, [{"action": "forward"}], 0, 2)
        self.assertIs(monitor, existing)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")

    def test_cancel_does_not_return_until_fresh_observation_arrives(self):
        rows = iter([
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            {"event": "observation", "sequence": 10, "image": "stale"},
            {"event": "observation", "sequence": 11, "image": "paired"},
        ])
        consumed = []

        def wait(predicate):
            while True:
                row = next(rows)
                consumed.append(row)
                if predicate(row):
                    return row

        result = controller.cancel_invalidated_cover(
            _Planner(), object(), _Process(), wait, "cover-2",
            required_observation_sequence=11)
        self.assertEqual(result[1]["status"], "cancelled")
        self.assertEqual(consumed[-1]["image"], "paired")


if __name__ == "__main__":
    unittest.main()

