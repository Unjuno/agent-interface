"""Type and platform corruption checks use retained ordinary construction bytes."""
import copy
import json
from pathlib import Path
import unittest
import audit

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'construction/02/run'


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.packet = json.loads((ROOT / 'raw.json').read_text())
        self.cases = json.loads((HERE / 'construction_cases.json').read_text())['cases']

    def check(self, packet):
        return audit.verify(packet, self.cases, ROOT, construction=True)

    def test_original_native_construction_is_reconciled(self):
        errors, findings = self.check(self.packet)
        self.assertEqual(errors, [])
        self.assertEqual(len(findings), 1)

    def test_boolean_zero_is_not_a_process_exit_receipt(self):
        changed = copy.deepcopy(self.packet)
        changed['rows'][0]['exits']['consumer'] = False
        self.assertIn('P00:cleanup', self.check(changed)[0])

    def test_integral_float_is_not_an_x_owner_identity(self):
        changed = copy.deepcopy(self.packet)
        changed['rows'][0]['before']['clipboard_owner'] = float(changed['rows'][0]['before']['clipboard_owner'])
        self.assertIn('P00:owner', self.check(changed)[0])

    def test_offscreen_record_cannot_close_native_transfer(self):
        changed = copy.deepcopy(self.packet)
        changed['rows'][0]['consumer_ready']['platform'] = 'offscreen'
        self.assertIn('P00:platform', self.check(changed)[0])


if __name__ == '__main__':
    unittest.main()
