import os
import unittest

from runtime.backends.x11_v1.backend import X11Backend


@unittest.skipUnless(os.environ.get("DISPLAY"), "requires X11 DISPLAY")
class PortableKeyNamesTest(unittest.TestCase):
    def test_portable_names_match_native_x11_keysyms(self):
        backend = X11Backend(os.environ["DISPLAY"], {})
        self.addCleanup(backend.close)
        for portable, native in (("HOME", "Home"), ("END", "End"),
                                 ("LEFT", "Left"), ("RIGHT", "Right"),
                                 ("UP", "Up"), ("DOWN", "Down"),
                                 ("BACKSPACE", "BackSpace"), ("DELETE", "Delete"),
                                 ("INSERT", "Insert")):
            with self.subTest(portable=portable):
                self.assertEqual(backend._keycode(portable), backend._keycode(native))
    def test_uppercase_home_chord_releases_physical_keys(self):
        backend = X11Backend(os.environ["DISPLAY"], {})
        self.addCleanup(backend.close)
        backend.key_chord(["CTRL", "HOME"])
        state = backend.release_all()
        self.assertTrue(state["verified"])
        self.assertEqual(state["keys_down"], [])
        self.assertEqual(state["buttons_down"], [])