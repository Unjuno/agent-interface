"""Replay a saved patch into a private index only; never run its postimages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/integration/semantic_endpoint_browser_5442_01a0ff58_review_transport'
PACKET = ROOT / REL
SOURCE = 'ea62e29074f8d65d134f9767b07c527c19d080af'


class ArchiveTests(unittest.TestCase):
    def test_four_original_files_and_transport_bindings(self):
        names = {'.gitattributes', 'SOURCE-TRANSPORT.json',
                 'changed-blobs.canonical.json', 'retained-windows.patch.txt'}
        self.assertEqual({p.name for p in PACKET.iterdir()}, names)
        for name in names:
            self.assertEqual((PACKET / name).read_bytes(), subprocess.check_output(
                ['git', 'show', SOURCE + ':' + REL + '/' + name], cwd=ROOT))
        pins = json.loads((PACKET / 'SOURCE-TRANSPORT.json').read_bytes())
        patch = (PACKET / 'retained-windows.patch.txt').read_bytes()
        self.assertEqual(len(patch), pins['original_diff_bytes'])
        self.assertEqual(hashlib.sha256(patch).hexdigest(), pins['original_diff_sha256'])
        self.assertEqual(hashlib.sha256((PACKET / 'changed-blobs.canonical.json').read_bytes()).hexdigest(),
                         pins['portable_changed_blob_sha256'])
        self.assertTrue(pins['no_primary_replay'])
        self.assertTrue(pins['no_PR_head_change'])

    def test_exact_patch_postimages_in_exclusive_private_index(self):
        rows = json.loads((PACKET / 'changed-blobs.canonical.json').read_bytes())
        self.assertEqual(len(rows), 61)
        self.assertEqual(len({r['path'] for r in rows}), 61)
        pins = json.loads((PACKET / 'SOURCE-TRANSPORT.json').read_bytes())
        with tempfile.TemporaryDirectory(prefix='browser-transport-index-') as temp:
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / 'index'))
            subprocess.run(['git', 'read-tree', '--empty'], cwd=ROOT, env=env, check=True)
            subprocess.run(['git', 'apply', '--cached', '--whitespace=nowarn',
                            str(PACKET / 'retained-windows.patch.txt')], cwd=ROOT, env=env, check=True)
            staged = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT, env=env)
            entries = {}
            for record in staged.decode().rstrip('\0').split('\0'):
                metadata, path = record.split('\t', 1)
                mode, oid, stage = metadata.split()
                self.assertEqual(stage, '0')
                entries[path] = (mode, oid)
            self.assertEqual(len(entries), 61)
            for row in rows:
                self.assertEqual(row['status'], 'A')
                self.assertEqual(entries[row['path']], (row['new_mode'], row['new_blob']))
                data = subprocess.check_output(['git', 'cat-file', 'blob', row['new_blob']], cwd=ROOT)
                self.assertEqual(len(data), row['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
                for tree in (pins['approved_source_head_unchanged'], 'HEAD'):
                    oid = subprocess.check_output(['git', 'rev-parse', tree + ':' + row['path']], cwd=ROOT).decode().strip()
                    self.assertEqual(oid, row['new_blob'])


if __name__ == '__main__':
    unittest.main()
