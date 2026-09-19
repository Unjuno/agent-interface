import unittest
from unittest import mock
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError


class TextPlanTests(unittest.TestCase):
    def backend(self):
        backend = object.__new__(X11Backend)
        backend._keycode = mock.Mock(return_value=1)
        backend.key_chord = mock.Mock()
        return backend

    def test_supported_punctuation_uses_x_keysym_names_and_shift(self):
        backend = self.backend()
        backend.text("a-._ A")
        self.assertEqual(backend.key_chord.call_args_list,
                         [mock.call(keys) for keys in (["a"], ["minus"], ["period"],
                                                       ["SHIFT", "minus"], ["SPACE"], ["SHIFT", "a"])])

    def test_unmapped_late_character_emits_no_prefix(self):
        backend = self.backend()
        def keycode(name):
            if name == "minus":
                raise X11BackendError("missing minus")
            return 1
        backend._keycode.side_effect = keycode
        with self.assertRaises(X11BackendError):
            backend.text("abc-")
        backend.key_chord.assert_not_called()

    def test_url_symbols_follow_live_keymap_levels(self):
        backend = self.backend()
        backend.d = mock.Mock()
        backend._keycode.side_effect = lambda name: {"colon": 47, "slash": 61}.get(name, 50)
        backend.d.keycode_to_keysym.side_effect = lambda code, level: {
            (47, 0): ord(";"), (47, 1): ord(":"), (61, 0): ord("/")}[code, level]
        backend.text(":/")
        self.assertEqual(backend.key_chord.call_args_list,
                         [mock.call(["SHIFT", "colon"]), mock.call(["slash"])])

    def test_url_symbol_in_unsupported_group_emits_no_prefix(self):
        backend = self.backend()
        backend.d = mock.Mock()
        backend.d.keycode_to_keysym.return_value = 0
        with self.assertRaises(X11BackendError):
            backend.text("http:")
        backend.key_chord.assert_not_called()


if __name__ == '__main__':
    unittest.main()
