"""A chord must not release a modifier held by an earlier operation."""
import unittest
from types import SimpleNamespace

from runtime.backends.x11_v1.backend import X11Backend, X11BackendError


class HeldModifierChordTests(unittest.TestCase):
    def backend_with_held_shift(self):
        return self.backend_with_held_keys(
            {"SHIFT": 50}, {"SHIFT": 50, "Shift_L": 50, "a": 38, "b": 56})

    def backend_with_held_keys(self, held_keycodes, keycodes):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = dict(held_keycodes)
        backend.emissions = 0
        modifier_codes = {50}
        backend.d = SimpleNamespace(get_modifier_mapping=lambda: [
            [50] if code == 50 else [] for code in modifier_codes
        ] + [[] for _ in range(8 - len(modifier_codes))])
        backend._keycode = keycodes.__getitem__
        events = []

        def key_state(key, down):
            events.append((key, down))
            if down:
                backend.held_keycodes[key] = keycodes[key]
            else:
                backend.held_keycodes.pop(key, None)

        backend.key_state = key_state
        return backend, events

    def test_chord_refuses_preheld_nonmodifier_without_input(self):
        backend, events = self.backend_with_held_keys({"a": 38}, {"a": 38})

        with self.assertRaisesRegex(X11BackendError, "already-held nonmodifier"):
            backend.key_chord(["a"])

        self.assertEqual(events, [])
        self.assertEqual(backend.held_keycodes, {"a": 38})

    def test_text_refuses_held_character_before_emitting_any_prefix(self):
        backend, events = self.backend_with_held_keys(
            {"a": 38}, {"SHIFT": 50, "a": 38, "b": 56})

        with self.assertRaisesRegex(X11BackendError, "already-held nonmodifier"):
            backend.text("ba")

        self.assertEqual(events, [])
        self.assertEqual(backend.held_keycodes, {"a": 38})

    def test_text_can_type_uppercase_while_preserving_held_shift(self):
        backend, events = self.backend_with_held_shift()

        backend.text("A")

        self.assertEqual(events, [("a", True), ("a", False)])
        self.assertEqual(backend.held_keycodes, {"SHIFT": 50})

    def test_chord_preserves_same_named_preheld_modifier(self):
        backend, events = self.backend_with_held_shift()

        backend.key_chord(["SHIFT", "b"])

        self.assertEqual(events, [("b", True), ("b", False)])
        self.assertEqual(backend.held_keycodes, {"SHIFT": 50})

    def test_chord_preserves_preheld_modifier_through_keysym_alias(self):
        backend, events = self.backend_with_held_shift()

        backend.key_chord(["Shift_L", "b"])

        self.assertEqual(events, [("b", True), ("b", False)])
        self.assertEqual(backend.held_keycodes, {"SHIFT": 50})

    def test_chord_reuses_original_code_for_same_named_preheld_modifier(self):
        backend, events = self.backend_with_held_shift()
        backend._keycode = {"b": 56}.__getitem__

        backend.key_chord(["SHIFT", "b"])

        self.assertEqual(events, [("b", True), ("b", False)])
        self.assertEqual(backend.held_keycodes, {"SHIFT": 50})

    def test_unheld_modifier_chord_keeps_balanced_press_release_order(self):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = {}
        keycodes = {"SHIFT": 50, "b": 56}
        backend._keycode = keycodes.__getitem__
        events = []

        def key_state(key, down):
            events.append((key, down))
            if down:
                backend.held_keycodes[key] = keycodes[key]
            else:
                backend.held_keycodes.pop(key, None)

        backend.key_state = key_state

        backend.key_chord(["SHIFT", "b"])

        self.assertEqual(events, [("SHIFT", True), ("b", True),
                                  ("b", False), ("SHIFT", False)])
        self.assertEqual(backend.held_keycodes, {})


if __name__ == "__main__":
    unittest.main()
