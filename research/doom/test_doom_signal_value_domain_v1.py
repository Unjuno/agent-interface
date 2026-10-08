import unittest

from doom_signal_value_domain_v1 import (
    SIGNAL_VALUE_RANGES,
    signal_value_in_domain,
)


class DoomSignalValueDomainTests(unittest.TestCase):
    def test_every_integer_in_and_around_each_domain(self):
        for signal_id, (minimum, maximum) in SIGNAL_VALUE_RANGES.items():
            for value in range(-1, 1002):
                with self.subTest(signal_id=signal_id, value=value):
                    self.assertEqual(
                        signal_value_in_domain(signal_id, value),
                        minimum <= value <= maximum)

    def test_noninteger_and_unknown_signal_ids_are_rejected(self):
        for value in (True, False, 1.0, "1", None):
            with self.subTest(value=value):
                self.assertFalse(signal_value_in_domain("health", value))
                self.assertFalse(signal_value_in_domain("ammo", value))
        self.assertFalse(signal_value_in_domain("enemy_visible", 1))

    def test_domain_table_cannot_be_mutated_at_runtime(self):
        with self.assertRaises(TypeError):
            SIGNAL_VALUE_RANGES["health"] = (0, 999)


if __name__ == "__main__":
    unittest.main()
