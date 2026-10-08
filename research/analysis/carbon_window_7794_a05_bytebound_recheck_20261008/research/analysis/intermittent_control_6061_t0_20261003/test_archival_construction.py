"""Offline tests of saved construction raw; no candidate or container launch."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parent
SAVED = PACKAGE / 'construction/02/candidate_raw.json'


class ArchivedConstructionTests(unittest.TestCase):
    def check_raw(self, raw_path):
        run = subprocess.run([sys.executable, '-B', str(PACKAGE / 'auditor.py'), str(PACKAGE / 'fixture.json'), str(raw_path)], capture_output=True, text=True, timeout=20)
        return run.returncode, json.loads(run.stdout)

    def test_all_original_freeze_hashes_and_duplicate_freeze(self):
        frozen = json.loads((PACKAGE / 'FREEZE.json').read_text())
        hashes = frozen['construction_sha256']
        self.assertEqual(len(hashes), 8)
        for label, expected in hashes.items():
            relative = label.replace('construction-02/', 'construction/02/', 1)
            with self.subTest(path=label):
                self.assertEqual(hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest(), expected.lower())
        self.assertEqual((PACKAGE / 'FREEZE.json').read_bytes(), (PACKAGE / 'FREEZE_V1.json').read_bytes())

    def test_preparation_is_not_promoted_to_formal_result(self):
        frozen = json.loads((PACKAGE / 'FREEZE.json').read_text())
        self.assertEqual(frozen['status'], 'PREPARED_FORMAL_INVOCATIONS_NOT_STARTED')
        self.assertEqual((frozen['formal_candidate'], frozen['formal_auditor'], frozen['retries']), (0, 0, 0))
        receipt = json.loads((PACKAGE / 'construction/02/mutation_stdout.json').read_text())
        self.assertTrue(receipt['all_rejected'])
        self.assertEqual(len(receipt['controls']), 5)

    def test_saved_construction_raw_replays_exactly(self):
        code, replayed = self.check_raw(SAVED)
        saved_receipt = json.loads((PACKAGE / 'construction/02/audit_stdout.txt').read_text())
        self.assertEqual(code, 0)
        self.assertEqual(replayed, saved_receipt)
        self.assertEqual(replayed, {'errors': [], 'rows': 32, 'verdict': 'PASS_METHOD_SCOPED'})

    def test_five_mutated_saved_raw_copies_fail_through_checker(self):
        saved = json.loads(SAVED.read_text())
        mutations = {}
        bad = copy.deepcopy(saved)
        bad['rows'].pop()
        mutations['drop_row'] = bad
        for name, scenario, change in (
            ('false_capture', 'r01', lambda row: row['capture_ticks'].append(1)),
            ('target_loss_continue', 'r03', lambda row: row.update(release='horizon')),
            ('lease_violation', 'r04', lambda row: row['actions'].append({'tick': 3, 'input': 1.0})),
            ('false_effect', 'r02', lambda row: row.update(effect=False)),
        ):
            bad = copy.deepcopy(saved)
            change(next(row for row in bad['rows'] if row['scenario'] == scenario and row['policy'] == 'triggered'))
            mutations[name] = bad
        with tempfile.TemporaryDirectory(prefix='archived-6061-construction-') as temporary:
            for name, bad in mutations.items():
                with self.subTest(control=name):
                    path = Path(temporary) / (name + '.json')
                    path.write_text(json.dumps(bad))
                    code, receipt = self.check_raw(path)
                    self.assertEqual(code, 1)
                    self.assertEqual(receipt['verdict'], 'FAIL_AUDIT')
                    self.assertTrue(receipt['errors'])


if __name__ == '__main__':
    unittest.main()
