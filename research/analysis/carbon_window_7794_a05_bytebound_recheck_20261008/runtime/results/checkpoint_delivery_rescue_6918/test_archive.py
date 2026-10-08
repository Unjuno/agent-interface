"""Read-only archive verification; never invoke matrix or retained candidate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/analysis/checkpoint_delivery_6089_20261003_01a0ff59'
SOURCE = '5e02b30977dc8412c715aa22dab718630906f4ad'


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_and_original_tree(self):
        entries = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
        files = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(len(entries), 44)
        self.assertEqual(set(entries), files - {'SHA256SUMS'})
        for name in files:
            data = (PACKET / name).read_bytes()
            original = subprocess.check_output(['git', 'show', SOURCE + ':' +
                'research/analysis/checkpoint_delivery_6089_20261003_01a0ff59/' + name], cwd=ROOT)
            self.assertEqual(data, original, name)
            if name in entries:
                self.assertEqual(hashlib.sha256(data).hexdigest(), entries[name], name)
        source_map = json.loads((PACKET / 'SOURCE_MAP.json').read_bytes())
        self.assertEqual(len(source_map['sources']), 6)
        for path, pin in source_map['sources'].items():
            data = (PACKET / pin['snapshot']).read_bytes()
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), pin['sha256'])
            self.assertEqual(data, subprocess.check_output(['git', 'show',
                source_map['base_main'] + ':' + path], cwd=ROOT))

    def test_raw_only_audit_exact_historical_outcome(self):
        historical = json.loads((PACKET / 'audit.json').read_bytes())
        for flags in (['-B'], ['-O', '-B']):
            actual = json.loads(subprocess.check_output([sys.executable, *flags,
                str(PACKET / 'audit.py'), str(PACKET / 'raw.json')], cwd=ROOT))
            self.assertEqual(actual, historical)
            self.assertEqual(actual['rows'], 24)
            self.assertEqual(len(actual['legacy_contract_mismatches']), 3)
            self.assertEqual(actual['normalized_contract_mismatches'], 0)
            self.assertEqual(actual['nonempty_case_pairs_unchanged'], 9)
            self.assertEqual(len(actual['copied_raw_controls']), 8)
            self.assertTrue(all(c['rejected'] is True for c in actual['copied_raw_controls']))
            self.assertTrue(actual['not_a_physical_safety_or_live_result'])


if __name__ == '__main__':
    unittest.main()
