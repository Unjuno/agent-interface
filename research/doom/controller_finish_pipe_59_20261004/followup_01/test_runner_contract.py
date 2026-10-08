"""Exit-code contract for the checked frozen regression wrapper."""
import unittest

from run_regression_checked import expected_exit_code


class CheckedRunnerContractTests(unittest.TestCase):
    def test_red_phase_expects_the_intentional_failure(self):
        self.assertEqual(expected_exit_code("red"), 1)

    def test_green_phase_expects_success(self):
        self.assertEqual(expected_exit_code("green"), 0)

    def test_unknown_phase_is_rejected(self):
        with self.assertRaises(ValueError):
            expected_exit_code("mystery")


if __name__ == "__main__":
    unittest.main()
