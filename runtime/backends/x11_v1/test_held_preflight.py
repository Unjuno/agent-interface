"""Compose text pacing with real preflight/execution at an inert X boundary."""
import unittest
from types import SimpleNamespace
from unittest import mock

from Xlib import X, XK

from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM, validate_program
from runtime.core_v1.sequence import expand_text_gaps


class HeldPreflightTests(unittest.TestCase):
    def setUp(self):
        self.backend = b = object.__new__(X11Backend)
        b.held_keycodes, b.held_buttons = {}, set()
        b.emissions = 0
        b.d, b.root = mock.Mock(), mock.Mock()
        b.targets = {"fixture": mock.Mock()}
        b.focus = mock.Mock()
        b._wait_update = mock.Mock()
        symbols = {"a": 38, "A": 38, "b": 56, "c": 54, "Shift_L": 50}
        self.keycodes = {XK.string_to_keysym(k): v for k, v in symbols.items()}
        b.d.keysym_to_keycode.side_effect = lambda symbol: self.keycodes.get(symbol, 0)
        b.d.pending_events.return_value = 0
        b.d.display.info = SimpleNamespace(min_keycode=8, max_keycode=56)
        b.d.get_keyboard_mapping.return_value = [[0, 0]] * 49
        b.d.get_modifier_mapping.return_value = [[50]] + [[] for _ in range(7)]
        b.root.query_pointer.return_value = SimpleNamespace(mask=0)
        self.physical, self.events = set(), []

        def query_keymap():
            bits = bytearray(32)
            for code in self.physical:
                bits[code // 8] |= 1 << (code % 8)
            return bits

        def emit(display, kind, code):
            self.assertIs(display, b.d)
            self.assertIn(kind, (X.KeyPress, X.KeyRelease))
            self.events.append((kind, code))
            if kind == X.KeyPress:
                self.physical.add(code)
            else:
                self.physical.discard(code)

        b.d.query_keymap.side_effect = query_keymap
        self.enterContext(mock.patch("runtime.backends.x11_v1.backend.xtest.fake_input", side_effect=emit))
        self.enterContext(mock.patch("runtime.backends.x11_v1.backend.display.Display",
                                     side_effect=AssertionError("X connection forbidden")))

    def program(self, ops):
        expanded, _ = expand_text_gaps([
            {"op": "focus", "target": "fixture"}, *ops, {"op": "release_all"}])
        program = dict(schema=SCHEMA_PROGRAM, program_id="held-preflight-test",
                       source=dict(observation_seq=0, binding_revision=0),
                       authority=dict(lease_id="inert-test", expires_at_ns=10**18),
                       terminal=dict(release_all_required=True), ops=expanded)
        validate_program(program)
        return program

    def assert_refused_before_execution(self, program):
        before = dict(self.backend.held_keycodes)
        self.events.clear()
        self.backend.emissions = 0
        self.backend.focus.reset_mock()
        self.backend._wait_update.reset_mock()
        with self.assertRaisesRegex(X11BackendError, "already-held nonmodifier"):
            self.backend.execute(program)
        self.assertEqual(self.events, [])
        self.assertEqual(self.backend.emissions, 0)
        self.assertEqual(self.backend.held_keycodes, before)
        self.backend.focus.assert_not_called()
        self.backend._wait_update.assert_not_called()

    def test_late_overlap_with_preheld_key_refuses_paced_and_unpaced_prefix(self):
        for gap in (0, 20):
            with self.subTest(gap=gap):
                self.backend.held_keycodes = {"a": 38}
                self.physical.add(38)
                self.assert_refused_before_execution(self.program([
                    {"op": "text", "text": "ba", "gap_ms": gap}]))

    def test_late_overlap_with_key_pressed_in_program_refuses_whole_program(self):
        for gap in (0, 20):
            with self.subTest(gap=gap):
                self.assert_refused_before_execution(self.program([
                    {"op": "key_state", "key": "a", "down": True},
                    {"op": "text", "text": "ba", "gap_ms": gap}]))

    def test_late_chord_alias_overlap_refuses_whole_program(self):
        self.assert_refused_before_execution(self.program([
            {"op": "key_state", "key": "a", "down": True},
            {"op": "text", "text": "b"},
            {"op": "key_chord", "keys": ["b", "A"]}]))

    def test_release_before_text_is_valid_without_mutating_preflight_ledger(self):
        self.backend.held_keycodes = {"a": 38}
        self.physical.add(38)
        program = self.program([
            {"op": "key_state", "key": "a", "down": True},
            {"op": "key_state", "key": "a", "down": False},
            {"op": "text", "text": "ba", "gap_ms": 20}])
        ledger = self.backend.held_keycodes
        self.backend.preflight(program)
        self.assertIs(self.backend.held_keycodes, ledger)
        self.assertEqual(ledger, {"a": 38})
        self.assertEqual(self.events, [])
        result = self.backend.execute(program)
        self.assertEqual(self.events, [(X.KeyPress, 38), (X.KeyRelease, 38),
                                      (X.KeyPress, 56), (X.KeyRelease, 56),
                                      (X.KeyPress, 38), (X.KeyRelease, 38)])
        self.assertTrue(result["releases"][-1]["verified"])
        self.assertEqual(self.backend.held_keycodes, {})

    def test_release_keeps_original_physical_code_when_current_mapping_is_missing(self):
        self.backend.held_keycodes = {"a": 38}
        self.physical.add(38)
        del self.keycodes[XK.string_to_keysym("a")]
        self.backend.execute(self.program([
            {"op": "key_state", "key": "a", "down": True},
            {"op": "key_state", "key": "a", "down": False},
            {"op": "text", "text": "b"}]))
        self.assertEqual(self.events, [(X.KeyPress, 38), (X.KeyRelease, 38),
                                      (X.KeyPress, 56), (X.KeyRelease, 56)])

    def test_preflight_does_not_clear_a_hold_when_releasing_another_logical_name(self):
        self.assert_refused_before_execution(self.program([
            {"op": "key_state", "key": "a", "down": True},
            {"op": "key_state", "key": "A", "down": True},
            {"op": "key_state", "key": "A", "down": False},
            {"op": "text", "text": "ba", "gap_ms": 20}]))

    def test_shift_and_unrelated_letter_holds_allow_paced_text(self):
        for key, value, code in (("SHIFT", "AB", 50), ("c", "ba", 54)):
            with self.subTest(key=key):
                self.events.clear()
                result = self.backend.execute(self.program([
                    {"op": "key_state", "key": key, "down": True},
                    {"op": "text", "text": value, "gap_ms": 20},
                    {"op": "key_state", "key": key, "down": False}]))
                taps = [38, 56] if key == "SHIFT" else [56, 38]
                self.assertEqual(self.events, [(X.KeyPress, code),
                    *[(kind, tap) for tap in taps for kind in (X.KeyPress, X.KeyRelease)],
                    (X.KeyRelease, code)])
                self.assertTrue(result["releases"][-1]["verified"])

    def test_session_refusal_cleans_existing_hold_without_typing_prefix(self):
        self.backend.held_keycodes = {"a": 38}
        self.physical.add(38)
        self.backend._activation_supported = mock.Mock(return_value=False)
        session = X11RuntimeSession(self.backend)
        result = session.dispatch(self.program([
            {"op": "text", "text": "ba", "gap_ms": 20}]),
            current_observation_seq=0, current_binding_revision=0, now_ns=0)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["error"], "BACKEND_CONSTRAINT")
        self.assertFalse(result["program_execution_started"])
        self.assertEqual(result["program_emissions"], 0)
        self.assertEqual(self.events, [(X.KeyRelease, 38)])
        self.assertTrue(result["release"]["verified"])
        self.assertFalse(session.recovery_required)
        self.backend.focus.assert_not_called()
        self.backend._wait_update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
