"""Archive/data-only checks; never execute child, adapters or deck producer."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/doom/scorer_pipe_backpressure_59_20261003_01a0ff33'
PACKET = ROOT / REL
SOURCE = 'c5360b1a80ce0af28c013cc8bdfcfed5ad1e60c9'


class ArchiveTests(unittest.TestCase):
    def test_manifest_original_git_and_six_source_witnesses(self):
        entries = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
        files = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(len(entries), 92)
        self.assertEqual(set(entries), files - {'SHA256SUMS'})
        for name in files:
            data = (PACKET / name).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', SOURCE + ':' + REL + '/' + name], cwd=ROOT))
            if name in entries:
                self.assertEqual(hashlib.sha256(data).hexdigest(), entries[name], name)
        pins = json.loads((PACKET / 'SOURCE.json').read_bytes())
        self.assertEqual(len(pins), 6)
        for pin in pins:
            data = (PACKET / (pin['copy_path'] + '.txt')).read_bytes()
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), pin['sha256'])
            self.assertEqual(data, subprocess.check_output(['git', 'show', pin['commit'] + ':' + pin['repo_path']], cwd=ROOT))

    def test_full_raw_verifier_normal_and_optimized(self):
        for flags in (['-B'], ['-O', '-B']):
            actual = json.loads(subprocess.check_output([sys.executable, *flags,
                str(PACKET / 'verify.py')], cwd=ROOT))
            self.assertEqual(actual, {'disposition': 'PASS_ARCHIVE_RAW_ONLY',
                'summary': {'rows': 20, 'pre_drain_commands': 12,
                            'blocked_direct_rows': 4, 'capacity_refusals': 4},
                'controls_rejected': 8, 'frozen_files': 13, 'native_stream_pairs': 20})


if __name__ == '__main__':
    unittest.main()
