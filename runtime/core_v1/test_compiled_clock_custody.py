"""Ordinary inert regression for the execution-return clock boundary."""
import unittest
from runtime.core_v1.compiled_gui import run
from runtime.core_v1.test_compiled_gui import Driver, interface


class ClockCustodyTests(unittest.TestCase):
    def test_clock_cannot_rewrite_returned_terminal_or_release(self):
        for mutation in ('refs', 'status', 'release', 'verified', 'keys', 'buttons'):
            with self.subTest(mutation=mutation):
                driver = Driver()
                original = driver.execute
                retained = []
                changes = []
                def execute(payload):
                    result = original(payload)
                    retained.append(result)
                    return result
                def clock():
                    if len(retained) > len(changes):
                        result = retained[-1]
                        changes.append(mutation)
                        if mutation == 'refs':
                            result.update(action_id='rebound', effect_ref='rebound')
                        elif mutation == 'status':
                            result['status'] = 'delivery_uncertain'
                        elif mutation == 'release':
                            result['release'] = {'verified': False, 'keys_down': ['held'], 'buttons_down': []}
                        elif mutation == 'verified':
                            result['release']['verified'] = False
                        else:
                            result['release'][mutation + '_down'].append('held')
                    return 0
                driver.execute = execute
                receipt = run(interface(), {'observe': driver.observe, 'admit': driver.admit,
                    'execute': driver.execute, 'verify_effect': driver.verify,
                    'cancelled': lambda: False, 'journal': driver.journal}, clock=clock)
                self.assertEqual(receipt['outcome'], 'TASK_SUCCEEDED')
                self.assertEqual(receipt['completed_transitions'], 2)
                self.assertEqual([t['action_id'] for t in receipt['transitions']], ['1', '2'])
                self.assertEqual([t['effect_ref'] for t in receipt['transitions']], ['effect', 'effect'])
                self.assertEqual(changes, [mutation, mutation])


if __name__ == '__main__':
    unittest.main()
