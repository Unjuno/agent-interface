import copy
import json
from pathlib import Path
import unittest
from audit import check_rows


class AuditControls(unittest.TestCase):
    def rows(self):
        values = [json.loads(line) for line in (Path(__file__).parent / 'methods/RUNNER-CONSTRUCTION.log').read_text().splitlines() if line.startswith('{')]
        return [row for row in values if 'case' in row]

    def test_saved_construction(self):
        self.assertEqual(check_rows(self.rows()), 'VERIFIED_CONSTRUCTION_ROWS')

    def test_rejects_bad_clock_missing_handshake_and_source(self):
        for field, value in [('start_ns', True), ('reader_alive_after_ready', False),
                             ('ready', {'event': 'terminal'}), ('pins', {}), ('child_alive', 1)]:
            rows = copy.deepcopy(self.rows()); rows[2][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_rows(rows)

    def test_rejects_missing_reordered_or_duplicate_cells(self):
        rows = self.rows()
        for changed in (rows[:3], rows[::-1], [rows[0], rows[0], rows[2], rows[3]]):
            with self.assertRaises(ValueError):
                check_rows(changed)
