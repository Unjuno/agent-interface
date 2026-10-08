import unittest
from policy import lower


class PolicyTests(unittest.TestCase):
    def test_scalar_conversion_after_supplementary_character(self):
        self.assertEqual(lower('😀ABCDZ', '😀ABCDZ', [3, 5], 'unicode_scalar'), [4, 6])

    def test_direction_survives_conversion(self):
        self.assertEqual(lower('😀ABCDZ', '😀ABCDZ', [5, 3], 'unicode_scalar'), [6, 4])

    def test_native_unit_is_not_double_converted(self):
        self.assertEqual(lower('😀ABCDZ', '😀ABCDZ', [4, 6], 'utf16'), [4, 6])

    def test_unknown_stale_and_non_integer_are_refused(self):
        for old, current, span, unit in [('ABC', 'QABC', [1, 2], 'unicode_scalar'),
                                       ('ABC', 'ABC', [1, 2], 'unknown'),
                                       ('ABC', 'ABC', [True, 2], 'unicode_scalar'),
                                       ('ABC', 'ABC', [1.0, 2], 'unicode_scalar')]:
            with self.subTest(span=span, unit=unit), self.assertRaises(ValueError):
                lower(old, current, span, unit)

    def test_half_surrogate_and_out_of_range_are_refused(self):
        for span, unit in [([1, 2], 'utf16'), ([0, 9], 'unicode_scalar')]:
            with self.subTest(span=span), self.assertRaises(ValueError):
                lower('😀A', '😀A', span, unit)


if __name__ == '__main__':
    unittest.main()
