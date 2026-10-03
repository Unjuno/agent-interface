import copy
import json
import unittest
from pathlib import Path

import audit_v2


class PlannerMetadataTypeTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).parent
        self.root = base / 'formal/01/candidate'
        self.packet = json.loads((self.root / 'raw.json').read_text())
        self.oracle = json.loads((base / 'oracle.json').read_text())

    def test_unchanged_formal_saved_packet_still_reconciles(self):
        errors, _ = audit_v2.verify(self.packet, self.oracle, self.root)
        self.assertEqual(errors, [])

    def test_planner_epoch_scalar_types_are_not_python_numeric_equality(self):
        for value in (True, 1.0):
            with self.subTest(value=value):
                changed = copy.deepcopy(self.packet)
                changed['rows'][0]['planner_metadata']['generation'] = value
                errors, _ = audit_v2.verify(changed, self.oracle, self.root)
                self.assertIn('C01:planner_scalar_type', errors)


if __name__ == '__main__':
    unittest.main()
