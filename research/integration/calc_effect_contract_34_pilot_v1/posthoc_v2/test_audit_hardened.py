from __future__ import annotations

import unittest

from audit_hardened import visibility_errors


class VisibilityGateTests(unittest.TestCase):
    def test_missing_field_stops(self):
        self.assertTrue(visibility_errors({}))

    def test_null_stops(self):
        self.assertTrue(visibility_errors({"visible_calc_window_ids": None}))

    def test_empty_list_stops(self):
        self.assertTrue(visibility_errors({"visible_calc_window_ids": []}))

    def test_wrong_type_stops(self):
        self.assertTrue(visibility_errors({"visible_calc_window_ids": "0x123"}))

    def test_malformed_id_stops(self):
        self.assertTrue(visibility_errors({"visible_calc_window_ids": [""]}))

    def test_nonempty_hex_id_is_accepted(self):
        self.assertEqual(visibility_errors({"visible_calc_window_ids": ["0x123"]}), [])


if __name__ == "__main__":
    unittest.main()
