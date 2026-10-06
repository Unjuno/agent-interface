"""Immutable patch/blob custody only; never load Quartz or native APIs."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/integration/quartz_release_fault_57_20261003_01a0ff52_review_transport'
PACKET = ROOT / REL
SOURCE = '29f916ae850139dae1f768be97a8226800c7bda8'

def run(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

class ArchiveTests(unittest.TestCase):
    def test_original_git_payload_and_exact_regenerated_patch(self):
        paths = run('ls-tree', '-r', '--name-only', SOURCE, '--', REL).decode().splitlines()
        self.assertEqual(len(paths), 3)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), run('show', SOURCE + ':' + path))
        descriptor = json.loads((PACKET / 'SOURCE-TRANSPORT.json').read_bytes())
        for name, item in descriptor['payloads'].items():
            data = (PACKET / name).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (item['bytes'], item['sha256']))
        regenerated = run(*descriptor['patch_command'][1:])
        self.assertEqual(regenerated, (PACKET / 'retained-full-index.patch.txt').read_bytes())

    def test_all_original_changed_postimages_and_preimages(self):
        descriptor = json.loads((PACKET / 'SOURCE-TRANSPORT.json').read_bytes())
        entries = json.loads((PACKET / 'changed-blobs.canonical.json').read_bytes())
        self.assertEqual(len(entries), 29)
        changed = run('diff', '--name-only', '--no-renames', descriptor['approved_base'], descriptor['approved_head']).decode().splitlines()
        self.assertEqual({item['path'] for item in entries}, set(changed))
        for item in entries:
            path = item['path']
            data = run('show', descriptor['approved_head'] + ':' + path)
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (item['bytes'], item['sha256']))
            self.assertEqual(run('rev-parse', descriptor['approved_head'] + ':' + path).decode().strip(), item['new_blob'])
            self.assertEqual(run('ls-tree', descriptor['approved_head'], '--', path).decode().split()[0], item['new_mode'])
            if item['old_mode'] != '000000':
                self.assertEqual(run('rev-parse', descriptor['approved_base'] + ':' + path).decode().strip(), item['old_blob'])
                self.assertEqual(run('ls-tree', descriptor['approved_base'], '--', path).decode().split()[0], item['old_mode'])

if __name__ == '__main__':
    unittest.main()
