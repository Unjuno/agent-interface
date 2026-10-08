"""Original review custody and retained outcomes; no producer or callback run."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'runtime/results/review-compiled-literal-unknown-01a0ff2d'
PACKET = ROOT / REL
SOURCE = '8aa2e501348e28d331947f137fcfd311b3da12c8'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name):
    return json.loads((PACKET / name).read_bytes())

class ArchiveTests(unittest.TestCase):
    def test_original_git_manifest_publication_and_diff(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 38)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
        items = load('MANIFEST.json')['files']
        self.assertEqual(len(items), 37)
        self.assertEqual({item['path'] for item in items}, {p[len(REL) + 1:] for p in paths} - {'MANIFEST.json'})
        for item in items:
            data = (PACKET / item['path']).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
        for item in load('PUBLICATION.json')['mapped_files']:
            data = (PACKET / item['path']).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['published_bytes'], item['published_sha256']))
        identity = load('diff-identity.json')
        data = subprocess.check_output(identity['recipe'], cwd=ROOT)
        self.assertEqual((len(data), sha(data)), (identity['bytes'], identity['sha256']))

    def test_four_original_receipts_and_45_saved_histories(self):
        projection = {item['path']: item for item in load('PUBLICATION.json')['mapped_files']}
        result = load('INDEPENDENT_RESULT.json')
        self.assertEqual(result['freeze_sha256'], projection['INDEPENDENT_FREEZE.json']['original_sha256'])
        expected = [('baseline-one', 1, 1, 1), ('candidate-eight', 0, 8, 13),
                    ('candidate-eight-optimized', 0, 8, 13), ('composed-nine', 0, 9, 18)]
        self.assertEqual(len(result['receipts']), 4)
        for saved, (label, exit_code, methods, histories) in zip(result['receipts'], expected, strict=True):
            receipt = load('checks/' + label + '.receipt.json')
            self.assertEqual(saved, receipt)
            self.assertEqual((receipt['exit_code'], receipt['expected_methods']), (exit_code, methods))
            data = load('checks/' + label + '.raw.json')
            self.assertEqual(len(data['rows']), histories)
            for suffix, key in [('raw.json', 'raw_sha256'), ('stdout.txt', 'stdout_sha256'), ('stderr.txt', 'stderr_sha256')]:
                path = 'checks/' + label + '.' + suffix
                actual_hash = sha((PACKET / path).read_bytes())
                self.assertEqual(receipt[key], projection[path]['original_sha256'] if path in projection else actual_hash)
            text = (PACKET / ('checks/' + label + '.stderr.txt')).read_text()
            self.assertIn('Ran ' + str(methods) + ' test', text)
            self.assertIn('FAILED (failures=1)' if exit_code else '\nOK\n', text)
        baseline = load('checks/baseline-one.raw.json')['rows'][0]
        self.assertEqual(baseline['result']['reason'], 'effect_unavailable')

if __name__ == '__main__':
    unittest.main()
