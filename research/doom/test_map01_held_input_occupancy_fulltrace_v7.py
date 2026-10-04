from __future__ import annotations

import unittest

import analyze_map01_held_input_occupancy_fulltrace_v7 as v6


def completed_hold_with_early_release() -> list[dict]:
    ms = 1_000_000
    return [
        {"event": "command", "received_ns": ms,
         "command": {"op": "submit", "id": "early-release",
                     "steps": [{"op": "hold", "keys": ["a"], "duration_ms": 100}]}},
        {"event": "step_started", "id": "early-release", "step": 0,
         "operation": "hold", "issued_ns": 10 * ms},
        {"event": "input_admission", "id": "early-release", "step": 0,
         "key": "a", "admitted_ns": 11 * ms, "input_ack_ns": 12 * ms},
        {"event": "keys_held", "id": "early-release", "step": 0,
         "keys": ["a"], "input_ack_ns": 12 * ms},
        {"event": "observation", "id": "early-release", "step": 0,
         "capture_ns": 30 * ms},
        {"event": "input_released", "id": "early-release",
         "owner_release": {"verified": True, "keys_down": [],
                           "verified_ns": 40 * ms, "reason": "focus_changed"}},
        {"event": "observation", "id": "early-release", "step": 0,
         "capture_ns": 80 * ms},
        {"event": "observation", "id": "early-release", "step": 0,
         "capture_ns": 90 * ms},
        {"event": "step_completed", "id": "early-release", "step": 0,
         "completed_ns": 100 * ms},
        {"event": "terminal", "id": "early-release", "status": "completed",
         "release": {"verified": True, "keys_down": [], "verified_ns": 95 * ms}},
    ]


class EarlyReleaseBoundsTest(unittest.TestCase):
    def test_completed_hold_bounds_stop_at_verified_early_release(self) -> None:
        hold = v6.reconstruct_holds(completed_hold_with_early_release())[0]
        self.assertEqual(hold["confirmed_any_key_held_until_ns"], 30_000_000)
        self.assertEqual(hold["released_by_ns"], 40_000_000)
        self.assertEqual(hold["release_reason"], "focus_changed")
        self.assertEqual(hold["physical_any_key_occupancy_lower_ms"], 18.0)
        self.assertEqual(hold["physical_any_key_occupancy_upper_ms"], 29.0)


if __name__ == "__main__":
    unittest.main()
