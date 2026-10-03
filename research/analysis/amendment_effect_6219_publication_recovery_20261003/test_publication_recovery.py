import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from recover_publication import EXPECTED_OUTPUTS, SOURCE, hash_bound_restore, inverse_prefix

PACKAGE = Path(__file__).resolve().parent


class PublicationRecoveryTests(unittest.TestCase):
    def test_all_original_blob_ids_and_reproducible_derivatives(self):
        manifest = json.loads((PACKAGE / 'RECOVERY_MANIFEST.json').read_text())
        self.assertEqual(len(manifest['files']), 14)
        self.assertEqual(manifest['source_tip'], SOURCE)
        original_freeze = json.loads(inverse_prefix((PACKAGE / 'published_blobs/FREEZE.json.bin').read_bytes()))
        references = dict(original_freeze['sha256'])
        references.update(EXPECTED_OUTPUTS)
        recorded_pr = (PACKAGE / 'PR6644_RECORDED_DISPOSITION.txt').read_text()
        for digest in EXPECTED_OUTPUTS.values():
            self.assertIn(digest, recorded_pr)
        exact = 0
        for row in manifest['files']:
            with self.subTest(path=row['source_path']):
                published = (PACKAGE / row['archived_path']).read_bytes()
                self.assertEqual(hashlib.sha256(published).hexdigest(), row['published_sha256'])
                header = ('blob ' + str(len(published)) + '\0').encode()
                self.assertEqual(hashlib.sha1(header + published).hexdigest(), row['source_git_blob'])
                derivative = (PACKAGE / row['derivative_path']).read_bytes()
                self.assertEqual(hashlib.sha256(derivative).hexdigest(), row['derivative_sha256'])
                if row['expected_sha256']:
                    relative = row['source_path'].split('amendment_effect_6219_t0_20261002/', 1)[1]
                    self.assertEqual(row['expected_sha256'], references[relative])
                    recovered, suffix = hash_bound_restore(published, row['expected_sha256'])
                    self.assertEqual((recovered, suffix), (derivative, row['appended_byte']))
                    exact += 1
                else:
                    self.assertEqual(derivative, inverse_prefix(published))
                    self.assertEqual(row['status'], 'UNBOUND_DECODED_PREFIX_NOT_PROVEN_ORIGINAL_BYTES')
        self.assertEqual(exact, 11)

    def test_unknown_hash_cannot_authorize_reconstructed_bytes(self):
        blob = (PACKAGE / 'published_blobs/candidate.py.bin').read_bytes()
        with self.assertRaises(ValueError):
            hash_bound_restore(blob, '0' * 64)

    def test_saved_raw_replays_exactly_to_historical_method_failure(self):
        root = PACKAGE / 'decoded_material'
        spec = importlib.util.spec_from_file_location('recovered_6219_audit', root / 'audit.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        fixture = json.loads((root / 'fixture_public.json').read_text())
        oracle = json.loads((root / 'oracle_truth.json').read_text())
        raw = json.loads((root / 'results/allocation-01/candidate/candidate_raw.json').read_text())
        saved = json.loads((root / 'results/allocation-01/audit/audit.json').read_text())
        self.assertEqual(checker.audit(fixture, oracle, raw), saved)
        self.assertEqual(saved['status'], 'METHOD_FAIL')
        self.assertEqual(saved['errors'], ['ORACLE_CONTRACT:case_addition'])
        self.assertEqual(saved['rows'], 36)


if __name__ == '__main__':
    unittest.main()
