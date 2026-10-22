"""Malformed admission sequence must never reach the compiled executor."""
import unittest

from runtime.core_v1.test_compiled_gui import Driver


class AdmissionSequenceTests(unittest.TestCase):
    def test_equal_boolean_or_float_is_rejected_before_first_dispatch(self):
        for value in (True, 1.0):
            with self.subTest(value=value, kind=type(value).__name__):
                driver = Driver()
                original = driver.admit
                driver.admit = lambda payload: dict(
                    original(payload), expected_sequence=value)
                with self.assertRaises(ValueError):
                    driver.run()
                self.assertEqual(driver.calls['execute'], [])
                self.assertEqual(driver.calls['verify_effect'], [])

    def test_false_cannot_alias_zero_observation_sequence(self):
        driver = Driver()
        observe = driver.observe
        driver.observe = lambda payload: dict(observe(payload), sequence=0)
        admit = driver.admit
        driver.admit = lambda payload: dict(admit(payload), expected_sequence=False)
        with self.assertRaises(ValueError):
            driver.run()
        self.assertEqual(driver.calls['execute'], [])

    def test_malformed_second_admission_keeps_verified_prefix(self):
        driver = Driver()
        admit = driver.admit

        def malformed(payload):
            result = admit(payload)
            if len(driver.calls['admit']) == 2:
                result['expected_sequence'] = 2.0
            return result

        driver.admit = malformed
        with self.assertRaises(ValueError):
            driver.run()
        self.assertEqual(len(driver.calls['execute']), 1)
        self.assertEqual(len(driver.calls['verify_effect']), 1)
        terminal = [row for row in driver.calls['journal']
                    if row['event'] == 'action_terminal']
        self.assertEqual(len(terminal), 1)
        self.assertIs(terminal[0]['release_verified'], True)

    def test_matching_integer_sequences_keep_normal_completion(self):
        driver = Driver()
        result = driver.run()
        self.assertEqual(result['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(result['completed_transitions'], 2)
        self.assertEqual([row['expected_sequence'] for row in driver.calls['execute']], [1, 2])

    def test_mismatched_sequence_still_prevents_dispatch(self):
        for value in (0, 2, None, '1'):
            with self.subTest(value=value):
                driver = Driver()
                admit = driver.admit
                driver.admit = lambda payload: dict(admit(payload), expected_sequence=value)
                with self.assertRaises(ValueError):
                    driver.run()
                self.assertEqual(driver.calls['execute'], [])

    def test_ineligible_admission_keeps_refusal_precedence(self):
        driver = Driver()
        admit = driver.admit
        driver.admit = lambda payload: dict(
            admit(payload), eligible=False, status='stale',
            authorization=None, expected_sequence=True)
        result = driver.run()
        self.assertEqual((result['outcome'], result['reason']), ('SAFE_YIELD', 'stale_symbol'))
        self.assertEqual(driver.calls['execute'], [])


if __name__ == '__main__':
    unittest.main()
