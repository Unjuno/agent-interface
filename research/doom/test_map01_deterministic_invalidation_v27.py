from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v27 as controller


class Map01DeterministicInvalidationV27Tests(unittest.TestCase):
    def test_discarded_injected_turn_cannot_supply_following_cover(self):
        decisions = [{
            "iteration": 0,
            "action": None,
            "model_action_discarded": True,
            "policy_invalidation": {
                "outcome": {"status": "INJECTED_INVALIDATION",
                            "grants_input_authority": False}},
        }]
        self.assertEqual(controller.reusable_cover(decisions), ([], None))
        coast = controller.compile_cover([])
        self.assertEqual(sum(row["duration_ms"] for row in coast), 10000)
        self.assertTrue(all(row["op"] == "coast" for row in coast))

    def test_injection_module_is_present_but_normal_command_has_no_test_flag(self):
        command = controller.app_server_command()
        self.assertNotIn("--inject-invalidation-iteration", command)
        self.assertNotIn("--inject-after-observations", command)
        self.assertEqual(command.count("app-server"), 1)


if __name__ == "__main__":
    unittest.main()
