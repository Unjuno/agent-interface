import unittest
from unittest.mock import Mock

from runtime.backends.win32_v1.backend import Win32Backend, Win32ExecutionError


class TargetGenerationExecutionGuardTests(unittest.TestCase):
    def backend(self, generations):
        backend = object.__new__(Win32Backend)
        backend.targets = {"fixture": 42}
        backend.target_generation = Mock(side_effect=generations)
        backend.preflight = Mock()
        backend.focus = Mock()
        backend.text = Mock()
        backend.key_chord = Mock()
        backend.release_all = Mock(return_value={
            "verified": True, "keys_down": [], "buttons_down": [],
            "keys_unknown": [], "buttons_unknown": [],
        })
        backend.emissions = 0
        return backend

    @staticmethod
    def program():
        return {
            "source": {"target_generations": {"fixture": "a" * 64}},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "text", "text": "owned-fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"},
            ],
        }

    def execute_error(self, backend):
        with self.assertRaises(Win32ExecutionError) as raised:
            backend.execute(self.program())
        self.assertIn("TARGET_GENERATION_CHANGED", str(raised.exception))
        self.assertTrue(raised.exception.release_receipt["verified"])
        self.assertEqual(backend.release_all.call_count, 1)

    def test_generation_change_before_focus_refuses_focus_and_input(self):
        backend = self.backend(["b" * 64])
        self.execute_error(backend)
        backend.focus.assert_not_called()
        backend.text.assert_not_called()
        backend.key_chord.assert_not_called()

    def test_generation_change_during_focus_refuses_before_first_input(self):
        backend = self.backend(["a" * 64, "b" * 64])
        self.execute_error(backend)
        backend.focus.assert_called_once_with("fixture")
        backend.text.assert_not_called()
        backend.key_chord.assert_not_called()

    def test_generation_change_between_effect_operations_stops_later_input(self):
        backend = self.backend(["a" * 64, "a" * 64, "a" * 64, "b" * 64])
        self.execute_error(backend)
        backend.focus.assert_called_once_with("fixture")
        backend.text.assert_called_once_with("owned-fixture")
        backend.key_chord.assert_not_called()

    def test_matching_generation_allows_effect_and_final_release(self):
        backend = self.backend(["a" * 64] * 4)
        result = backend.execute(self.program())
        self.assertTrue(result["releases"][-1]["verified"])
        backend.focus.assert_called_once_with("fixture")
        backend.text.assert_called_once_with("owned-fixture")
        backend.key_chord.assert_called_once_with(["CTRL", "S"])
        backend.release_all.assert_called_once()

    def test_legacy_program_without_generation_map_keeps_backend_behavior(self):
        backend = self.backend([])
        program = self.program()
        program["source"] = {}
        backend.execute(program)
        backend.target_generation.assert_not_called()
        backend.text.assert_called_once_with("owned-fixture")


if __name__ == "__main__":
    unittest.main()
