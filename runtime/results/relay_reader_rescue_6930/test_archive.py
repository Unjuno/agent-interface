"""Byte/provenance checks for the immutable predecessor; no archived execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/integration/relay_reader_error_57_20261003_01a0ff58'
PACKET = ROOT / REL
SOURCE = '575bf53bc449fc3c09b61610e6e51a16dab76e19'


def load(name):
    return json.loads((PACKET / name).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ArchiveTests(unittest.TestCase):
    def test_complete_original_git_manifest_and_publication(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 53)
        manifest = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, manifest)
            manifest[name] = digest
        self.assertEqual(len(manifest), 52)
        self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'SHA256SUMS'})
        for path in paths:
            data = (ROOT / path).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
            name = path[len(REL) + 1:]
            if name in manifest:
                self.assertEqual(sha(data), manifest[name])
        mapping = load('PUBLICATION.json')['mapping']
        self.assertEqual(len(mapping), 47)
        self.assertEqual(len({item['public_path'] for item in mapping}), 47)
        for item in mapping:
            data = (PACKET / item['public_path']).read_bytes()
            self.assertEqual(len(data), item['public_bytes'])
            self.assertEqual(sha(data), item['public_sha256'])
            if item['projection'] == 'exact bytes':
                self.assertEqual(item['public_sha256'], item['original_sha256'])
                self.assertEqual(item['public_bytes'], item['original_bytes'])

    def test_source_witnesses_and_original_command_receipts(self):
        base, source = load('source/BASE.json'), load('SOURCE.json')
        for path, pin in base['source'].items():
            data = subprocess.check_output(['git', 'show', base['base'] + ':' + path], cwd=ROOT)
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(sha(data), pin['sha256'])
        for path, pin in source['source_pins'].items():
            data = subprocess.check_output(['git', 'show', source['source_commit_after_ordinary_tests'] + ':' + path], cwd=ROOT)
            self.assertEqual(sha(data), pin['sha256'])
            self.assertEqual(subprocess.check_output(['git', 'rev-parse', source['source_commit_after_ordinary_tests'] + ':' + path], cwd=ROOT).decode().strip(), pin['git_blob'])
        mapping = {item['public_path']: item for item in load('PUBLICATION.json')['mapping']}
        for phase, exit_code in [('red-01', 1), ('green-01', 1), ('green-02', 0), ('coupled-01', 0)]:
            receipt = load('checks/' + phase + '/receipt.json')
            self.assertEqual(receipt['exit_code'], exit_code)
            for stream in ('stdout', 'stderr'):
                name = 'checks/' + phase + '/' + stream + '.log'
                self.assertEqual(receipt[stream + '_sha256'], mapping[name]['original_sha256'])
            for path, digest in receipt['source'].items():
                name = path.replace('/', '__') if '/' in path and phase == 'green-02' else Path(path).name
                self.assertEqual(sha((PACKET / 'checks' / phase / (name + '.txt')).read_bytes()), digest)


if __name__ == '__main__':
    unittest.main()
