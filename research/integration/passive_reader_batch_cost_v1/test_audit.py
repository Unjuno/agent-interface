"""Excluded construction and raw-reconstruction controls, not new measurements."""
import unittest
from pathlib import Path
import audit


class AuditChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.view = audit.read_view(Path(__file__).parent / 'construction-01')
        cls.baseline = audit.audit(cls.view, construction=True)
        cls.changes = audit.controls(cls.view, construction=True)

    def test_baseline(self):
        self.assertEqual(self.baseline['verdict'], 'PASS_CONSTRUCTION')
        self.assertEqual(self.baseline['errors'], [])

    def test_missing_and_duplicate(self):
        self.assertTrue(self.changes['missing_case'])
        self.assertTrue(self.changes['duplicate_case'])

    def test_process_exit(self):
        self.assertTrue(self.changes['wrong_exit'])

    def test_accounting(self):
        self.assertTrue(self.changes['read_byte_count'])
        self.assertTrue(self.changes['hash_byte_count'])

    def test_clock_type(self):
        self.assertTrue(self.changes['clock_bool'])

    def test_cursor(self):
        self.assertTrue(self.changes['cursor'])

    def test_authority(self):
        self.assertTrue(self.changes['authority'])

    def test_rehashed_payload_and_trace(self):
        self.assertTrue(self.changes['returned_record'])
        self.assertTrue(self.changes['trace'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
