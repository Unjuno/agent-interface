"""Pure synthetic/parser construction checks; starts no X server and sends no events."""
import importlib.util
from pathlib import Path
import unittest

RUNNER = Path(__file__).with_name("runner.py")
spec = importlib.util.spec_from_file_location("issue3764_runner", RUNNER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiagnosticConstructionTests(unittest.TestCase):
    def test_setxkbmap_layout_query_parser(self):
        output = "rules:      evdev\nmodel:      pc105\nlayout:     de\n"
        self.assertTrue(module.layout_matches(output, "de"))
        self.assertFalse(module.layout_matches(output, "us"))
        self.assertFalse(module.layout_matches("layout: de,us\n", "de"))

    def test_core_map_symbol_summary_uses_keycode_and_level(self):
        from Xlib import XK
        rows = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]
        rows[1] = [XK.string_to_keysym("y"), XK.string_to_keysym("Y"), 0]
        rows[2] = [XK.string_to_keysym("z"), XK.string_to_keysym("Z"), 0]
        rows[0] = [XK.string_to_keysym("equal"), XK.string_to_keysym("asterisk"), 0, 0, 0, 0]
        summary = module.summarize_symbols({"min_keycode": 8, "max_keycode": 10, "rows": rows})
        self.assertEqual(summary["y"], [{"keycode": 9, "level": 0,
                                          "keysym": XK.string_to_keysym("y")}])
        self.assertEqual(summary["Z"], [{"keycode": 10, "level": 1,
                                          "keysym": XK.string_to_keysym("Z")}])
        self.assertEqual(summary["equal"], [{"keycode": 8, "level": 0,
                                              "keysym": XK.string_to_keysym("equal")}])
        self.assertEqual(summary["asterisk"], [{"keycode": 8, "level": 1,
                                                 "keysym": XK.string_to_keysym("asterisk")}])

    def test_core_map_fingerprint_is_canonical_and_sensitive(self):
        first = {"min_keycode": 8, "max_keycode": 9, "rows": [[0, 0], [97, 65]]}
        reordered = {"rows": [[0, 0], [97, 65]], "max_keycode": 9, "min_keycode": 8}
        changed = {"min_keycode": 8, "max_keycode": 9, "rows": [[0, 0], [98, 66]]}
        self.assertEqual(module.map_fingerprint(first), module.map_fingerprint(reordered))
        self.assertNotEqual(module.map_fingerprint(first), module.map_fingerprint(changed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
