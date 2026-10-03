import hashlib
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).resolve().parent


class ArchivedMaterialTests(unittest.TestCase):
    def test_all_original_manifest_entries_and_six_frozen_sources(self):
        rows = (PACKAGE / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(rows), 33)
        for row in rows:
            digest, relative = row.split('  ', 1)
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest(), digest)
        frozen = json.loads((PACKAGE / 'FREEZE.json').read_text())
        self.assertEqual(len(frozen['source_sha256']), 6)
        for relative, digest in frozen['source_sha256'].items():
            self.assertEqual(hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest(), digest)

    def test_retained_image_fixture_and_nonidentifiable_pair(self):
        fixture = json.loads((PACKAGE / 'fixture.json').read_text())
        cases = {row['case_id']: row for row in fixture['cases']}
        self.assertEqual(len(cases), 12)
        self.assertEqual(len(list((PACKAGE / 'images').glob('*.pgm'))), 24)
        for key in ('frame0', 'frame1'):
            self.assertEqual((PACKAGE / cases['k11'][key]).read_bytes(), (PACKAGE / cases['k12'][key]).read_bytes())
        frozen = json.loads((PACKAGE / 'FREEZE.json').read_text())
        self.assertEqual(frozen['allocation_id'], 'LOOMING-VISUAL-ASSUMPTION-GATE-5905-S05-WSLC-20261003-01')
        self.assertEqual(frozen['main_sha'], 'fc1c09294458d3b2744fa05432d4cf8a19583f18')
        self.assertEqual(frozen['budget']['retries'], 0)


if __name__ == '__main__':
    unittest.main()
