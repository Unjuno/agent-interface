import unittest

import runner


class ConstructionTests(unittest.TestCase):
    def test_frozen_case_ids_and_seven_cases(self):
        self.assertEqual(len(runner.CASES), 7)
        self.assertEqual(len({c["id"] for c in runner.CASES}), 7)

    def test_macro_matches_all_expected_sequences(self):
        for case in runner.CASES:
            self.assertEqual(runner.canonical(runner.deterministic_macro(case)), runner.canonical(case["expected"]), case["id"])

    def test_stale_guard_rejects_without_state_change(self):
        case = runner.CASES[5]
        state = case["initial"].copy()
        result = runner.simulate_action(state, {"name": "set_thermostat", "arguments": {"zone": "kitchen", "target_c": 18}}, case["scope"])
        self.assertEqual(result, "REJECT_STALE_SCOPE")
        self.assertEqual(state, case["initial"])

    def test_forbidden_tool_is_never_simulated(self):
        case = runner.CASES[3]
        state = case["initial"].copy()
        result = runner.simulate_action(state, {"name": "delete_schedule", "arguments": {"name": "Weekday Comfort"}}, case["scope"])
        self.assertEqual(result, "REJECT_FORBIDDEN_TOOL")
        self.assertIn("Weekday Comfort", state["schedules"])

    def test_current_allowed_calls_change_only_synthetic_state(self):
        case = runner.CASES[0]
        state = case["initial"].copy()
        result = runner.simulate_action(state, case["expected"][0], case["scope"])
        self.assertEqual(result, "SIMULATED_EFFECT")
        self.assertEqual(state["lights"]["study"], {"power": "on", "brightness_pct": 40})


if __name__ == "__main__":
    unittest.main(verbosity=2)
