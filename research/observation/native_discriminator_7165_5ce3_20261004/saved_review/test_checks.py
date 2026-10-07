import copy, json, unittest
from pathlib import Path
from checks import check_rows
ROOT = Path(__file__).resolve().parents[1]

class SavedChecks(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(s) for s in (ROOT/'runs/candidate/raw.jsonl').read_text().splitlines()]
    def test_actual_saved_call_sequence_and_clocks(self):
        self.assertTrue(check_rows(self.rows))
    def test_before_mutation_control_is_accepted_by_original(self):
        from run_saved_checks import before_mutation, check
        truth = [json.loads(s) for s in (ROOT/'runs/candidate/oracle.jsonl').read_text().splitlines()]
        before_mutation(self.rows)
        check(self.rows, truth)
    def test_invented_operations_rejected(self):
        for row in self.rows:
            for a in [row['acquisition'], *row['arms'].values()]:
                for c in a['calls']: c['op'] = 'Invented'
        with self.assertRaises(AssertionError): check_rows(self.rows)
    def test_replaced_source_windows_rejected(self):
        for row in self.rows:
            for a in [row['acquisition'], *row['arms'].values()]:
                for c in a['calls']: c['window'] = 999999
        with self.assertRaises(AssertionError): check_rows(self.rows)
    def test_reversed_acquisition_clocks_rejected(self):
        self.rows[0]['acquisition']['calls'][0].update(start_ns=-1, end_ns=-2)
        with self.assertRaises(AssertionError): check_rows(self.rows)
    def test_reacquisition_before_mutation_rejected(self):
        row = next(r for r in self.rows if r['mode'] == 'STALE_HINT')
        t = row['fixture_mutation_started_ns']-1000000
        for a in row['arms'].values():
            for c in a['calls']: c.update(start_ns=t, end_ns=t+1); t += 2
        with self.assertRaises(AssertionError): check_rows(self.rows)
    def test_zero_elapsed_with_nonzero_span_rejected(self):
        for row in self.rows:
            for a in [row['acquisition'], *row['arms'].values()]: a['elapsed_ns'] = 0
        with self.assertRaises(AssertionError): check_rows(self.rows)

if __name__ == '__main__': unittest.main()
