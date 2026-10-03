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
        self.assertEqual(check_rows(self.rows(), historical=True), 'VERIFIED_HISTORICAL_CONSTRUCTION_ROWS')

    def directory(self, root):
        rows = self.rows()
        for row in rows:
            # New-schema synthetic fixture; never change retained old raw rows.
            row.update(cleanup_child_alive=False, cleanup_reader_alive=False)
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
                root = Path(name) / 'data'; root.mkdir(); self.directory(root)
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
                    target.rename(root.parent / 'outside.json')
                    target.symlink_to(root.parent / 'outside.json')
                with self.assertRaises(ValueError):
                    check_directory(root)

    def test_rejects_bad_clock_missing_handshake_and_source(self):
        for field, value in [('start_ns', True), ('reader_alive_after_ready', False),
                             ('ready', {'event': 'terminal'}), ('pins', {}), ('child_alive', 1)]:
            rows = copy.deepcopy(self.rows()); rows[2][field] = value
            for row in rows:
                row.update(cleanup_child_alive=False, cleanup_reader_alive=False)
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_rows(rows)

    def test_rejects_missing_reordered_or_duplicate_cells(self):
        rows = self.rows()
        for changed in (rows[:3], rows[::-1], [rows[0], rows[0], rows[2], rows[3]]):
            with self.assertRaises(ValueError):
                check_rows(changed)

    def test_rejects_missing_or_live_cleanup_state(self):
        for value in (True, None):
            rows = self.rows()
            for row in rows:
                row.update(cleanup_child_alive=False, cleanup_reader_alive=False)
            rows[2]['cleanup_child_alive'] = value
            with self.assertRaises(ValueError):
                check_rows(rows)

    def test_rejects_overlapping_cells(self):
        rows = self.rows()
        for row in rows:
            row.update(cleanup_child_alive=False, cleanup_reader_alive=False)
            shift = row['start_ns'] - rows[0]['start_ns']
            row['start_ns'] -= shift; row['end_ns'] -= shift
            for wait in row['waits']:
                wait['start_ns'] -= shift; wait['end_ns'] -= shift
        with self.assertRaises(ValueError):
            check_rows(rows)
