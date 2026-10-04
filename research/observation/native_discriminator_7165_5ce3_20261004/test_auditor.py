"""Excluded native preflight replay and copied controls, not extra formal trials."""
import copy, json, unittest
from pathlib import Path
from auditor import validate_row
ROOT = Path(__file__).resolve().parent

class AuditorTests(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(s) for s in (ROOT/'runs/preflight/raw.jsonl').read_text().splitlines()]
        self.truth = [json.loads(s) for s in (ROOT/'runs/preflight/oracle.jsonl').read_text().splitlines()]
    def test_native_excluded_rows_reconcile(self):
        for r, t in zip(self.rows, self.truth): self.assertTrue(validate_row(r, t))
    def test_stale_packet_epoch_rejects(self):
        r = copy.deepcopy(self.rows[0]); r['arms']['MEMORY_CUE']['packet']['epoch'] = 'stale'
        with self.assertRaises(AssertionError): validate_row(r, self.truth[0])
    def test_source_boolean_identifier_rejects(self):
        r = copy.deepcopy(self.rows[0]); r['arms']['FULL_REACQUIRE']['packet']['records'][0]['id'] = True
        with self.assertRaises(AssertionError): validate_row(r, self.truth[0])
    def test_cleanup_boolean_exit_rejects(self):
        r = copy.deepcopy(self.rows[0]); r['cleanup']['server_exit'] = True
        with self.assertRaises(AssertionError): validate_row(r, self.truth[0])
    def test_false_byte_cost_rejects(self):
        r = copy.deepcopy(self.rows[0]); r['arms']['FRESH_CUE']['canonical_bytes'] = 1
        with self.assertRaises(AssertionError): validate_row(r, self.truth[0])
    def test_wrong_selection_rejects(self):
        r = copy.deepcopy(self.rows[0]); selected = r['arms']['MEMORY_CUE']['selected']; other = next(x['id'] for x in r['arms']['MEMORY_CUE']['packet']['records'] if x['id'] != selected); r['arms']['MEMORY_CUE']['selected'] = other
        with self.assertRaises(AssertionError): validate_row(r, self.truth[0])

if __name__ == '__main__': unittest.main()
