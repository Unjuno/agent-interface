"""Malformed post-execute release containers must never prove neutrality.

These ordinary finite regressions add prefix and uncertain-return evidence;
they do not replay7772's producer or establish physical input release.
"""
import unittest
from runtime.core_v1.test_compiled_gui import Driver

class UnsafeList(list):
    def __eq__(self, other):
        raise AssertionError('user equality hook invoked')
    def __len__(self):
        raise AssertionError('user length hook invoked')
    def __deepcopy__(self, memo):
        raise AssertionError('user copy hook invoked')

class EqualityLie(list):
    def __eq__(self, other): return True

class ReleaseRecoveryTests(unittest.TestCase):
    def drive(self, bad, *, at=1, refused=False, field='keys_down', opaque_ref=False):
        driver = Driver()
        base = driver.execute
        def execute(payload):
            terminal = base(payload)
            if len(driver.calls['execute']) == at:
                terminal['release'][field] = bad
                if refused:
                    terminal.update(status='refused', input_dispatched=False)
                    terminal['release']['verified'] = False
                if opaque_ref: terminal['effect_ref'] = object()
            return terminal
        driver.execute = execute
        return driver, driver.run()

    def check_stop(self, driver, receipt, completed):
        self.assertEqual((receipt['outcome'], receipt['reason']), ('RUNTIME_FAILED', 'execution_failed'))
        self.assertEqual(receipt['completed_transitions'], completed)
        self.assertEqual(len(driver.calls['execute']), completed + 1)
        self.assertEqual(len(driver.calls['verify_effect']), completed)
        terminal = [e for e in receipt['critical_events'] if e['event'] == 'action_terminal'][-1]
        self.assertIs(terminal['release_verified'], False)
        unresolved = receipt['unresolved_execution']
        self.assertEqual(unresolved['action'], 'save' if completed else 'enter')
        self.assertEqual(unresolved['reason'], 'malformed_release_container')
        self.assertIs(unresolved['release_verified'], False)
        self.assertEqual(receipt['critical_events'][-1]['outcome'], 'RUNTIME_FAILED')

    def test_equality_lie_cannot_complete_either_release_field(self):
        for field in ('keys_down', 'buttons_down'):
            with self.subTest(field=field):
                d, r = self.drive(EqualityLie(['held']), field=field)
                self.check_stop(d, r, 0)
                self.assertEqual(r['unresolved_execution']['effect_ref'], 'effect')

    def test_user_hooks_are_not_called_during_rejection_or_receipt(self):
        d, r = self.drive(UnsafeList(['held']))
        self.check_stop(d, r, 0)

    def test_malformed_no_input_refusal_cannot_hide_nonempty_metadata(self):
        d, r = self.drive(EqualityLie(['held']), refused=True)
        self.check_stop(d, r, 0)
        self.assertIs(r['unresolved_execution']['input_dispatched'], False)

    def test_second_invalid_return_preserves_verified_completed_prefix(self):
        d, r = self.drive(UnsafeList(['held']), at=2)
        self.check_stop(d, r, 1)
        self.assertEqual(r['transitions'][0]['action'], 'enter')
        self.assertEqual(r['unresolved_execution']['action_id'], '2')

    def test_nonlist_and_opaque_reference_return_conservative_evidence(self):
        for bad in ((), None, {'key': 'held'}):
            with self.subTest(type=type(bad).__name__):
                d, r = self.drive(bad, opaque_ref=True)
                self.check_stop(d, r, 0)
                self.assertIsNone(r['unresolved_execution']['effect_ref'])

    def test_healthy_completion_and_plain_held_failure_keep_existing_receipt_shape(self):
        for bad, expected in (([], 'TASK_SUCCEEDED'), (['held'], 'RUNTIME_FAILED')):
            with self.subTest(expected=expected):
                d, r = self.drive(bad)
                self.assertEqual(r['outcome'], expected)
                self.assertNotIn('unresolved_execution', r)

if __name__ == '__main__': unittest.main()
