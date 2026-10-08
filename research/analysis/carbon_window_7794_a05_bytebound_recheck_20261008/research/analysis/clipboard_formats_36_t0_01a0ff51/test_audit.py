import copy
import json
import unittest
from pathlib import Path

import audit


class SavedStateAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / 'construction' / '02' / 'run'
        self.packet = json.loads((self.root / 'raw.json').read_text())
        self.oracle = json.loads((Path(__file__).parent / 'oracle.json').read_text())

    def test_actual_qt_saved_state_reconciles(self):
        errors, findings = audit.verify(self.packet, self.oracle, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(len(findings), 12)

    def test_all_controls_fail_for_their_specific_reason(self):
        controls = audit.mutations(self.packet, self.oracle, self.root)
        self.assertEqual(len(controls), 10)
        for control in controls:
            with self.subTest(control=control['name']):
                self.assertTrue(control['rejected'])
                self.assertIn(control['required_error'], control['errors'])

    def test_unrelated_existing_error_does_not_satisfy_a_mutation(self):
        packet = copy.deepcopy(self.packet)
        packet['schema'] = 'bad-schema'
        packet['rows'][0]['observed']['generation'] = 1.0
        errors, _ = audit.verify(packet, self.oracle, self.root)
        self.assertIn('schema_or_platform', errors)
        self.assertIn('C01:observed', errors)
        self.assertNotIn('C05:request_trace', errors)


if __name__ == '__main__':
    unittest.main()
