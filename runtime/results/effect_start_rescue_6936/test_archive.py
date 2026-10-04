"""Read-only source and retained-matrix verification; never invoke producers."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'runtime/results/kernel-effect-start-5156'
PACKET = ROOT / REL
SOURCE = '1de9e07946a75ccc1c81d54147776d6795711920'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name):
    return json.loads((PACKET / name).read_bytes())

class ArchiveTests(unittest.TestCase):
    def test_all_git_images_manifest_sources_and_public_derivatives(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 67)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT), path)
        entries = load('MANIFEST.json')['entries']
        self.assertEqual({item['path'] for item in entries}, {p[len(REL) + 1:] for p in paths} - {'MANIFEST.json'})
        self.assertEqual(len(entries), 66)
        for item in entries:
            data = (PACKET / item['path']).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
        source = load('SOURCE.json')
        self.assertEqual(len(source['source']), 11)
        for path, item in source['source'].items():
            data = (PACKET / item['retained']).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', source['base'] + ':' + path], cwd=ROOT))
            self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
            if 'baseline_working_retained' in item:
                self.assertEqual(sha((PACKET / item['baseline_working_retained']).read_bytes()), item['baseline_working_after_run_sha256'])
        for item in load('CAPTURES.json')['entries']:
            data = (PACKET / item['public_path']).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['public_bytes'], item['public_sha256']))

    def test_full_retained_matrix_and_eight_effective_controls(self):
        spec = importlib.util.spec_from_file_location('retained_effect_audit', PACKET / 'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        freeze, fixture, raw, recorded = load('MATRIX_FREEZE.json'), load('fixture.json'), load('raw.json'), load('audit.json')
        for name, digest in freeze['inputs_sha256'].items():
            self.assertEqual(sha((PACKET / name).read_bytes()), digest)
        self.assertEqual(len(raw['rows']), 180)
        self.assertEqual(auditor.check(raw, fixture, freeze), recorded['counts'])
        self.assertEqual(sha((PACKET / 'raw.json').read_bytes()), recorded['raw_sha256'])
        mutations = [
            lambda d: d['rows'][0].update(observed_ns=False),
            lambda d: d['rows'][0].update(observed_ns=0.0),
            lambda d: d['rows'][0].update(accepted=False),
            lambda d: d['rows'][1]['after'].update(execution=None),
            lambda d: d['rows'][0]['outcome'].update(effect_verified=False),
            lambda d: d['rows'].pop(),
            lambda d: d['source_sha256']['baseline'].update(lifecycle='0' * 64),
            lambda d: d['rows'][0]['before'].update(extra=None),
        ]
        for mutate, expected in zip(mutations, recorded['controls'], strict=True):
            changed = copy.deepcopy(raw)
            mutate(changed)
            self.assertFalse(auditor.same(raw, changed))
            self.assertTrue(expected['refused'])
            with self.assertRaises(ValueError) as error:
                auditor.check(changed, fixture, freeze)
            self.assertEqual(str(error.exception), expected['reason'])

if __name__ == '__main__':
    unittest.main()
