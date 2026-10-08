"""Returned verdicts retain their meaning across a later journal callback."""
import unittest

from runtime.core_v1.compiled_gui import run
from runtime.core_v1.test_compiled_gui import Driver, interface


class RetainedVerdictDriver(Driver):
    def __init__(self, status='succeeded', replacement=None, cancel=False, evidence=None):
        super().__init__()
        self.status = status
        self.replacement = replacement
        self.cancel_on_effect = cancel
        self.cancelled = False
        self.evidence = evidence
        self.verdict = None
        self.effect_events = []

    def verify(self, payload):
        self.record('verify_effect', payload)
        first = len(self.calls['verify_effect']) == 1
        self.verdict = {
            'status': self.status if first else 'succeeded',
            'evidence_ref': self.evidence if first and self.evidence is not None else payload['observation']['evidence_ref'],
        }
        return self.verdict

    def journal(self, payload):
        super().journal(payload)
        if payload['event'] == 'effect_checked':
            self.effect_events.append(payload)
            if len(self.effect_events) == 1:
                if self.replacement is not None:
                    self.verdict['status'] = self.replacement
                self.cancelled = self.cancel_on_effect

    def run(self):
        return run(interface(), {'observe': self.observe, 'admit': self.admit,
                   'execute': self.execute, 'verify_effect': self.verify,
                   'journal': self.journal, 'cancelled': lambda: self.cancelled},
                   clock=lambda: self.now)


class EffectReturnCustodyTests(unittest.TestCase):
    def check_failure(self, status, replacement=None):
        driver = RetainedVerdictDriver(status, replacement)
        receipt = driver.run()
        self.assertEqual((receipt['outcome'], receipt['reason']), ('SAFE_YIELD', 'effect_' + status))
        self.assertEqual((receipt['completed_transitions'], len(driver.calls['execute'])), (1, 1))
        self.assertEqual(receipt['pending_effect']['action'], 'enter')
        self.assertTrue(receipt['transitions'][0]['release_verified'])
        self.assertEqual(driver.effect_events[0]['status'], status)

    def test_failed_return_cannot_be_promoted_by_journal(self):
        self.check_failure('failed', 'succeeded')

    def test_unavailable_return_cannot_be_promoted_by_journal(self):
        self.check_failure('unavailable', 'succeeded')

    def test_failed_unchanged_stops_before_second_action(self):
        self.check_failure('failed')

    def test_unavailable_unchanged_stops_before_second_action(self):
        self.check_failure('unavailable')

    def test_successful_return_cannot_be_demoted_by_journal(self):
        driver = RetainedVerdictDriver(replacement='failed')
        receipt = driver.run()
        self.assertEqual((receipt['outcome'], receipt['completed_transitions'], len(driver.calls['execute'])), ('TASK_SUCCEEDED', 2, 2))
        self.assertIsNone(receipt['pending_effect'])
        self.assertEqual(driver.effect_events[0]['status'], 'succeeded')

    def test_healthy_success_is_preserved(self):
        driver = RetainedVerdictDriver()
        receipt = driver.run()
        self.assertEqual((receipt['outcome'], receipt['completed_transitions']), ('TASK_SUCCEEDED', 2))

    def test_real_journal_cancellation_still_blocks_second_action(self):
        driver = RetainedVerdictDriver(cancel=True)
        receipt = driver.run()
        self.assertEqual((receipt['outcome'], receipt['reason'], receipt['completed_transitions']), ('SAFE_YIELD', 'cancelled', 1))
        self.assertEqual(len(driver.calls['execute']), 1)
        self.assertIsNone(receipt['pending_effect'])

    def test_blank_success_reference_is_still_rejected_before_journal(self):
        driver = RetainedVerdictDriver(evidence='')
        with self.assertRaises(ValueError):
            driver.run()
        self.assertEqual(len(driver.calls['execute']), 1)
        self.assertEqual(driver.effect_events, [])


if __name__ == '__main__':
    unittest.main()
