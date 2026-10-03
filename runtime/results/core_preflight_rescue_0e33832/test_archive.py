"""Read-only historical evidence checks; never execute the retained helpers."""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/reviews/current_core_composition_6866_45e9'
SOURCE = '0e3383247855afbfef6013db50bd74763260d4de'


class ArchiveTests(unittest.TestCase):
    def test_complete_original_manifest(self):
        entries = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
        self.assertEqual(len(entries), 14)
        self.assertEqual(set(entries), {p.name for p in PACKET.iterdir()} - {'SHA256SUMS'})
        for name, digest in entries.items():
            data = (PACKET / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)
            original = subprocess.check_output(['git', 'show', SOURCE + ':' +
                'research/reviews/current_core_composition_6866_45e9/' + name], cwd=ROOT)
            self.assertEqual(data, original, name)

    def test_frozen_blob_readback(self):
        freeze = json.loads((PACKET / 'FREEZE.json').read_bytes())
        self.assertEqual(len(freeze['blobs']), 24)
        self.assertEqual(len({i['path'] for i in freeze['blobs']}), 24)
        for item in freeze['blobs']:
            data = subprocess.check_output(['git', 'cat-file', 'blob', item['blob_oid']], cwd=ROOT)
            self.assertEqual(len(data), item['bytes'], item['path'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'], item['path'])
            self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest(), item['blob_oid'])
            if item['path'] == 'runtime/core_v1/contract.py':
                self.assertEqual(data, (PACKET / 'combined_contract.py.txt').read_bytes())

    def test_historical_outcomes_and_helper_failure(self):
        result = json.loads((PACKET / 'RESULT.json').read_bytes())
        freeze_hash = hashlib.sha256((PACKET / 'FREEZE.json').read_bytes()).hexdigest()
        for name in ('core-current', 'sessions-current'):
            receipt = json.loads((PACKET / (name + '.receipt.json')).read_bytes())
            self.assertEqual(receipt, result['check_receipts'][name])
            self.assertEqual(receipt['exit_code'], 0)
            self.assertEqual(receipt['source_freeze_sha256'], freeze_hash)
            self.assertLess(receipt['started_utc'], receipt['ended_utc'])
        stderr = (PACKET / 'core-current.stderr.txt').read_text()
        self.assertIn('Ran 84 tests', stderr)
        self.assertTrue(stderr.rstrip().endswith('OK'))
        raw = json.loads((PACKET / 'sessions-current.stdout.txt').read_bytes())
        rows = raw['rows']
        labels = ('valid', 'expired', 'nan_clock', 'negative_clock', 'bool_clock', 'bool_sequence', 'float_revision')
        self.assertEqual(len(rows), 21)
        self.assertEqual({(r['route'], r['case']) for r in rows},
                         set(itertools.product(('win32_v1', 'x11_v1', 'quartz_v1'), labels)))
        for row in rows:
            valid = row['case'] == 'valid'
            self.assertIs(type(row['spy_execution_count']), int)
            self.assertEqual(row['spy_execution_count'], 1 if valid else 0)
            self.assertEqual(row['status'], 'completed' if valid else 'refused')
            self.assertEqual(row['calls'], ['clock', 'preflight', 'execute'] if valid else ['clock'])
            self.assertEqual(row['error'], None if valid else
                             ('LEASE_EXPIRED' if row['case'] == 'expired' else 'INVALID_PROGRAM'))
        self.assertEqual(result['core_tests'], 84)
        self.assertEqual(result['session_spy_cases'], 21)
        self.assertEqual(result['valid_inert_executions'], 3)
        self.assertEqual(result['refused_cases_without_preflight_or_execute'], 18)
        failure = json.loads((PACKET / 'first-helper-result.json').read_bytes())
        self.assertEqual(failure['observed_exit_code'], 1)
        self.assertEqual(failure['actual_first_row'], rows[0])
        self.assertIn("'ok'", failure['failed_assertion'])
        self.assertIn('not a separately captured original stderr', failure['qualification'])
        self.assertFalse(result['main_send_attempted'])
        self.assertFalse(result['head_changed'])


if __name__ == '__main__':
    unittest.main()
