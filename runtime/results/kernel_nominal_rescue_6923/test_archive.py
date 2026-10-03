"""Pinned archive and current projection checks; old mutants remain inert."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'runtime/results/kernel-nominal-records-01a0ff2d'
PACKET = ROOT / REL
SOURCE = 'b84aa6a1260128bd70e2cbe1598a9c80b55f75ee'


class ArchiveTests(unittest.TestCase):
    def test_original_packet_manifest_and_blobs(self):
        entries = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
        files = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()}
        self.assertEqual(len(entries), 34)
        self.assertEqual(set(entries), files - {'SHA256SUMS'})
        for name in files:
            data = (PACKET / name).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', SOURCE + ':' + REL + '/' + name], cwd=ROOT))
            if name in entries:
                self.assertEqual(hashlib.sha256(data).hexdigest(), entries[name], name)

    def test_entire_current_source_projection_and_historical_failures(self):
        pins = json.loads((PACKET / 'SOURCE.json').read_bytes())['candidate_python_and_workflow_sha256']
        self.assertEqual(len(pins), 11)
        for path, digest in pins.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        self.assertIn('FAILED (failures=5, errors=1)', (PACKET / 'checks/before-types/stdout.txt').read_text())
        for variant in ('normal', 'optimized'):
            output = (PACKET / ('checks/' + variant + '/stdout.txt')).read_text()
            self.assertIn('Ran 50 tests', output)
            self.assertTrue(output.rstrip().endswith('OK'))


if __name__ == '__main__':
    unittest.main()
