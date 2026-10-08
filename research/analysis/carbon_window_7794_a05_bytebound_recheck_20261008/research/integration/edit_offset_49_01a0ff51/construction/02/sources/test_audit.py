import unittest
from audit import jint, native_replace, same


class AuditTests(unittest.TestCase):
    def test_native_oracle_is_unit_sensitive(self):
        self.assertEqual(native_replace('😀ABCDZ', [3, 5]), '😀AXDZ')
        self.assertEqual(native_replace('😀ABCDZ', [4, 6]), '😀ABXZ')

    def test_native_oracle_preserves_direction(self):
        self.assertEqual(native_replace('😀ABCDZ', [6, 4]), '😀ABXZ')

    def test_scalar_types_do_not_alias(self):
        self.assertFalse(jint(False)); self.assertFalse(jint(0.0))
        self.assertFalse(same([1], [True])); self.assertFalse(same([1], [1.0]))


if __name__ == '__main__':
    unittest.main()
