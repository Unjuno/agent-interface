"""Historical input-only checks: no candidate or original auditor execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/integration/publication_interval_6526_20261003_01a0ff35'
SOURCE = '20ff74d5284245a81ea09f1134e18381f23c7958'


class ArchiveTests(unittest.TestCase):
    def test_exact_original_manifest(self):
        entries = json.loads((PACKET / 'MANIFEST.json').read_bytes())['files']
        files = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()}
        self.assertEqual(len(entries), 53)
        self.assertEqual(set(entries), files - {'MANIFEST.json'})
        for name in files:
            data = (PACKET / name).read_bytes()
            original = subprocess.check_output(['git', 'show', SOURCE + ':' +
                'research/integration/publication_interval_6526_20261003_01a0ff35/' + name], cwd=ROOT)
            self.assertEqual(data, original, name)
            if name in entries:
                self.assertEqual(len(data), entries[name]['bytes'], name)
                self.assertEqual(hashlib.sha256(data).hexdigest(), entries[name]['sha256'], name)

    def test_independent_raw_reconstruction_and_corruptions(self):
        with tempfile.TemporaryDirectory(prefix='publication-archive-') as temp:
            inputs = str(Path(temp) / 'inputs')
            materialized = json.loads(subprocess.check_output([sys.executable, '-B',
                str(PACKET / 'materialize_inputs.py'), str(ROOT), inputs], cwd=ROOT))
            self.assertEqual(materialized['exported'], 370)
            self.assertEqual(materialized['bytes'], 735510)
            args = [inputs, str(PACKET / 'INPUTS.json'), str(PACKET / 'FREEZE.json'),
                    str(PACKET / 'evidence/interval-result.json')]
            for flags in (['-B'], ['-O', '-B']):
                checked = json.loads(subprocess.check_output([sys.executable, *flags,
                    str(PACKET / 'independent_check_v2.py'), *args], cwd=ROOT))
                self.assertEqual(checked, {'status': 'INDEPENDENT_RAW_CHECK_PASS',
                    'source_files': 370, 'rows': 180, 'possible_time_fixtures': 196,
                    'result_sha256': '9bd9703e314912124031d3e0604f750f3ce8bdace16f91b8531ab01d6515d1f3'})
                controls = json.loads(subprocess.check_output([sys.executable, *flags,
                    str(PACKET / 'custody_controls.py'), *args,
                    str(PACKET / 'independent_check_v2.py')], cwd=ROOT))
                self.assertEqual(controls['original_manifest_selected_matches'], 364)
                self.assertEqual(controls['accepted_result_corruption_count'], 0)
                for field, count in [('custody_corruptions', 8), ('result_corruptions', 7)]:
                    self.assertEqual(len(controls[field]), count)
                    self.assertTrue(all(c['rejected'] is True for c in controls[field]))


if __name__ == '__main__':
    unittest.main()
