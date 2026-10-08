import copy
import json
from pathlib import Path
import unittest
from audit import audit


class RawAuditControls(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((Path(__file__).parent / 'candidate.raw.json').read_text())

    def test_unchanged_raw_passes(self):
        self.assertEqual(audit(self.rows, 'candidate')['errors'], [])

    def test_missing_row_refused(self):
        self.assertTrue(audit(self.rows[:-1], 'candidate')['errors'])

    def test_duplicate_row_refused(self):
        self.rows[0] = copy.deepcopy(self.rows[1])
        self.assertTrue(audit(self.rows, 'candidate')['errors'])

    def test_fabricated_stale_release_refused(self):
        row = next(r for r in self.rows if r['state']=='begun' and r['release_kind']=='empty' and r['release_ns']==0)
        row.update(accepted=True, error=None, release_verified=True)
        row['after'].update(stage='stopped', stop_reason='cancelled')
        self.assertTrue(audit(self.rows, 'candidate')['errors'])

    def test_refusal_mutation_of_lifecycle_refused(self):
        row = next(r for r in self.rows if r['state']=='begun' and r['release_kind']=='empty' and r['release_ns']==0)
        row['after']['stop_reason'] = 'cancelled'
        self.assertTrue(audit(self.rows, 'candidate')['errors'])

    def test_boolean_timestamp_refused(self):
        row = next(r for r in self.rows if r['release_ns']==0)
        row['release_ns'] = False
        self.assertTrue(audit(self.rows, 'candidate')['errors'])


if __name__ == '__main__':
    unittest.main()
