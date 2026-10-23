import unittest


class InputObligationTests(unittest.TestCase):
    def setUp(self):
        try:
            from runtime.guarded_win32_v1.input_obligations import derive_input_obligations
        except ModuleNotFoundError:
            self.fail("standard input obligation derivation is missing")
        self.derive = derive_input_obligations

    def test_derives_all_possible_key_button_and_unicode_release_obligations(self):
        program = {"ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "key_state", "key": "A", "down": True},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "text", "text": "A😀"},
            {"op": "release_all"},
        ]}

        self.assertEqual(self.derive(program), [
            "button:fixture:left",
            "key:fixture:A",
            "key:fixture:CTRL",
            "key:fixture:S",
            "unicode:0041",
            "unicode:D83D",
            "unicode:DE00",
        ])

    def test_refuses_a_focused_input_without_a_target(self):
        with self.assertRaisesRegex(ValueError, "focused target"):
            self.derive({"ops": [
                {"op": "key_state", "key": "CTRL", "down": True},
            ]})


if __name__ == "__main__":
    unittest.main()
