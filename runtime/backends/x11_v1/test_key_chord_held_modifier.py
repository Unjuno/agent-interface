"""A chord must not release a modifier held by an earlier operation."""
import unittest

from runtime.backends.x11_v1.backend import X11Backend


class HeldModifierChordTests(unittest.TestCase):
    def backend_with_held_shift(self):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = {"SHIFT": 50}
        backend.emissions = 0
        keycodes = {"SHIFT": 50, "Shift_L": 50, "b": 56}
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
