"""Verify public derivatives and reconstruct sources without old runners."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'runtime/results/kernel-n-u-current-context-01a0ff2d'
PACKET = ROOT / REL
SOURCE = 'c1bb1cb775803037fd005d6237dbe99aa4329e87'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((PACKET / name).read_bytes())


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


class ArchiveTests(unittest.TestCase):
    def test_exact_original_git_manifest_and_joint_sources(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 28)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), git_bytes(SOURCE, path), path)
        manifest = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, manifest)
            manifest[name] = digest
            self.assertEqual(sha((PACKET / name).read_bytes()), digest, name)
        self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'SHA256SUMS'})
        freeze, source = load('FREEZE.json'), load('SOURCE.json')
        for path, digest in freeze['nominal_source_workflow_pins'].items():
            self.assertEqual(sha(git_bytes(freeze['nominal_head'], path)), digest, path)
        snapshots = {'lifecycle.py', 'test_kernel.py', 'test_nominal_types.py', 'test_nominal_cancel_effect.py'}
        for path, digest in source['joint_exact_file_sha256'].items():
            name = Path(path).name
            data = (PACKET / (name + '.txt')).read_bytes() if name in snapshots else git_bytes('316ac44b24d4ac29c1942d2fee51f1c0599855b1', path)
            self.assertEqual(sha(data), digest, path)
        self.assertEqual(source['joint_exact_file_sha256'], freeze['source_sha256']['joint'])

    def test_retained_logs_receipts_publication_and_first_failures(self):
        publication = {item['path']: item for item in load('PUBLICATION.json')['transformations']}
        for path, item in publication.items():
            data = (PACKET / path).read_bytes()
            self.assertEqual(sha(data), item['public_sha256'], path)
            self.assertEqual(len(data), item['public_bytes'], path)
        verification = load('VERIFICATION.json')
        self.assertEqual(verification['freeze_sha256'], publication['FREEZE.json']['original_sha256'])
        self.assertEqual(verification['plan_sha256'], sha((PACKET / 'PLAN.md').read_bytes()))
        expected = {'nominal_only': (1, 1, 1), 'uncertainty_only': (1, 1, 1), 'joint': (56, 0, 0), 'joint_optimized': (56, 0, 0)}
        self.assertEqual(len(verification['commands']), 4)
        for record in verification['commands']:
            label = record['label']
            self.assertEqual(load('checks/' + label + '/receipt.json'), record)
            methods, failures, exit_code = expected[label]
            self.assertEqual((record['actual_methods'], record['actual_failures'], record['exit_code']), (methods, failures, exit_code))
            self.assertEqual(record['actual_errors'], 0)
            for stream in ('stdout', 'stderr'):
                path = 'checks/' + label + '/' + stream + '.txt'
                digest = sha((PACKET / path).read_bytes())
                self.assertEqual(record[stream + '_sha256'], publication[path]['original_sha256'] if path in publication else digest)
            text = (PACKET / ('checks/' + label + '/stderr.txt')).read_text()
            self.assertIn('Ran ' + str(methods) + ' test', text)
            self.assertNotIn('skipped=', text)
            if failures:
                self.assertIn('FAILED (failures=1)', text)
                self.assertIn('AssertionError: False is not true' if label == 'nominal_only' else 'AssertionError: ContractError not raised', text)
            else:
                self.assertRegex(text, r'(?m)^OK$')
            self.assertFalse(record['formal_replayed'])
        self.assertEqual(load('first-construction-error.json')['exit_code'], 1)
        self.assertEqual(load('first-output-parser-error.json')['wrapper_exit_code'], 1)
        self.assertFalse(verification['physical_task_effect_verified'])


if __name__ == '__main__':
    unittest.main()
