"""Successful verifier metadata must not silently authorize graph progress."""
import unittest

from runtime.core_v1.test_compiled_gui import Driver


class SuccessEvidenceTests(unittest.TestCase):
    def test_malformed_success_reference_stops_before_next_action_or_completion(self):
        # Removing the success-reference validation allows graph progress.
        for value in (None, '', 0, True, False, 1.0, [], {}, 'x' * 65):
            for stage in (1, 2):
                with self.subTest(value=value, stage=stage):
                    driver = Driver()
                    original = driver.verify

                    def verify(payload):
                        result = original(payload)
                        if len(driver.calls['verify_effect']) == stage:
                            result['evidence_ref'] = value
                        return result

                    driver.verify = verify
                    with self.assertRaises(ValueError):
                        driver.run()
                    self.assertEqual(len(driver.calls['execute']), stage)
                    self.assertEqual(len(driver.calls['verify_effect']), stage)
                    terminals = [e for e in driver.calls['journal']
                                 if e['event'] == 'action_terminal']
                    self.assertEqual(len(terminals), stage)
                    self.assertTrue(all(e['release_verified'] is True for e in terminals))
                    effects = [e for e in driver.calls['journal'] if e['event'] == 'effect_checked']
                    self.assertEqual(len(effects), stage - 1)
                    self.assertFalse(any(e['event'] == 'runtime_finished' for e in driver.calls['journal']))

    def test_bounded_distinct_success_reference_keeps_completion(self):
        for value in ('w', 'independent-witness', 'x' * 64):
            with self.subTest(value=value):
                driver = Driver()
                original = driver.verify

                def verify(payload):
                    result = original(payload)
                    result['evidence_ref'] = value
                    return result

                driver.verify = verify
                result = driver.run()
                self.assertEqual(result['outcome'], 'TASK_SUCCEEDED')
                self.assertEqual(result['completed_transitions'], 2)
                self.assertEqual([e['evidence_ref'] for e in result['critical_events']
                                  if e['event'] == 'effect_checked'], [value, value])

    def test_absent_reference_on_negative_verdict_keeps_safe_yield(self):
        for status, reason in (('failed', 'effect_failed'), ('unavailable', 'effect_unavailable')):
            with self.subTest(status=status):
                driver = Driver()
                original = driver.verify

                def verify(payload):
                    original(payload)
                    return {'status': status, 'evidence_ref': None}

                driver.verify = verify
                result = driver.run()
                self.assertEqual((result['outcome'], result['reason']), ('SAFE_YIELD', reason))
                self.assertEqual(result['completed_transitions'], 1)
                self.assertEqual(len(driver.calls['execute']), 1)
                self.assertEqual(result['pending_effect']['action'], 'enter')


if __name__ == '__main__':
    unittest.main()
