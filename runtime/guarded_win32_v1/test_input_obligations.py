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
            "key:fixture:A:virtual_key",
            "key:fixture:CTRL:virtual_key",
            "key:fixture:S:virtual_key",
            "unicode:0041",
            "unicode:D83D",
            "unicode:DE00",
        ])

    def test_preserves_scan_code_encoding_for_orphan_release(self):
        program = {"ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "key_state", "key": "W", "down": True,
             "encoding": "scan_code"},
            {"op": "release_all"},
        ]}

        self.assertEqual(self.derive(program), [
            "key:fixture:W:scan_code",
        ])

    def test_rejects_unknown_or_falsey_key_encodings_before_admission(self):
        for encoding in ("", "hardware", False, 0):
            with self.subTest(encoding=encoding):
                with self.assertRaisesRegex(ValueError,
                        "unsupported key encoding"):
                    self.derive({"ops": [
                        {"op": "focus", "target": "fixture"},
                        {"op": "key_state", "key": "W", "down": True,
                         "encoding": encoding},
                    ]})

    def test_explicit_null_encoding_matches_backend_default(self):
        self.assertEqual(self.derive({"ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "key_state", "key": "W", "down": True,
             "encoding": None},
        ]}), ["key:fixture:W:virtual_key"])

    def test_refuses_a_focused_input_without_a_target(self):
        with self.assertRaisesRegex(ValueError, "focused target"):
            self.derive({"ops": [
                {"op": "key_state", "key": "CTRL", "down": True},
            ]})


if __name__ == "__main__":
    unittest.main()
