"""Read-only regression checks using excluded small construction evidence."""
import unittest
from pathlib import Path
import audit
import controls

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.records=audit.load(Path(__file__).resolve().parent/'construction')
    def test_baseline(self):
        a=audit.analyze(self.records,complete=False)
        self.assertEqual(a['errors'],[]);self.assertEqual(a['unexpected_errors'],[])
    def test_formal_denominator_not_satisfied_by_construction(self):
        a=audit.analyze(self.records,complete=True)
        self.assertIn('complete performance matrix',a['errors'])
    def mutation(self,name):
        a=audit.analyze(controls.changed(self.records,name),complete=False)
        self.assertTrue(a['errors']);self.assertEqual(a['unexpected_errors'],[])
    def test_boolean_count(self):self.mutation('query_boolean_count')
    def test_value(self):self.mutation('wrong_value_claim')
    def test_clock(self):self.mutation('negative_duration')
    def test_readonly(self):self.mutation('readonly_change')
    def test_nonunique(self):self.mutation('unique_index')
    def test_request(self):self.mutation('wrong_request')
    def test_source(self):self.mutation('source_identity')
    def test_exit(self):self.mutation('nonzero_exit')
    def test_sample_count(self):self.mutation('missing_timing_sample')
    def test_unknown_preservation(self):self.mutation('duplicate_record_promoted')

if __name__=='__main__':unittest.main()
