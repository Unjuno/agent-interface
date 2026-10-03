import copy
import json
from pathlib import Path
import unittest
import tempfile
from audit import check_rows, check_directory


class AuditControls(unittest.TestCase):
    def rows(self):
        values = [json.loads(line) for line in (Path(__file__).parent / 'methods/RUNNER-CONSTRUCTION.log').read_text().splitlines() if line.startswith('{')]
        return [row for row in values if 'case' in row]

    def test_saved_construction(self):
        self.assertEqual(check_rows(self.rows()), 'VERIFIED_CONSTRUCTION_ROWS')

    def directory(self, root):
        rows = self.rows()
        for row in rows:
            (root / (row['case'] + '.json')).write_text(json.dumps(row))
        (root / 'SUMMARY.json').write_text(json.dumps({
            'cases': [row['case'] for row in rows], 'retries': 0, 'model_calls': 0,
            'verdict': 'PASS_SCOPED_PIPE_NOTIFICATION'}))

    def test_complete_saved_directory(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); self.directory(root)
            self.assertEqual(check_directory(root), 'VERIFIED_SAVED_PIPE_RECORD')

    def test_rejects_incomplete_extra_or_inconsistent_directory(self):
        for defect in ('missing', 'extra', 'summary', 'row_gate', 'symlink'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as name:
                root = Path(name); self.directory(root)
                target = root / 'candidate_eof.json'
                if defect == 'missing':
                    target.unlink()
                elif defect == 'extra':
                    (root / 'extra.json').write_text('{}')
                elif defect == 'summary':
                    (root / 'SUMMARY.json').write_text('{}')
                elif defect == 'row_gate':
                    row = json.loads(target.read_text()); row['gate'] = False
                    target.write_text(json.dumps(row))
                else:
                    target.rename(root / 'outside.json')
                    target.symlink_to(root / 'outside.json')
                with self.assertRaises(ValueError):
                    check_directory(root)

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
