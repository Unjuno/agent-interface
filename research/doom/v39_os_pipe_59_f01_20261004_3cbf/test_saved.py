import copy
import json
from pathlib import Path
import unittest
import shutil
import tempfile
from verify_saved import validate, check


class SavedBoundary(unittest.TestCase):
    def test_check_rejects_modified_summary_missing_cell_and_changed_copy(self):
        for mutation in ('summary', 'missing', 'copy'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(Path(__file__).parent / 'raw', root / 'raw')
                self.assertEqual(check(root), 'PASS_PARSER_NOTIFICATION_EOF_UNRESOLVED')
                if mutation == 'missing':
                    (root / 'raw/candidate_fault.json').unlink()
                elif mutation == 'summary':
                    with (root / 'raw/SUMMARY.json').open('ab') as handle:
                        handle.write(b' ')
                else:
                    row = json.loads((root / 'raw/candidate_fault.json').read_text())
                    row['child_alive'] = False
                    (root / 'raw/candidate_fault.json').write_text(json.dumps(row))
                with self.assertRaises(ValueError):
                    check(root)

    def record(self):
        return json.loads((Path(__file__).parent / 'raw/SUMMARY.json').read_text())

    def test_exact_saved_outcomes(self):
        self.assertEqual(validate(self.record()), 'PASS_PARSER_NOTIFICATION_EOF_UNRESOLVED')

    def test_rejects_changed_source_outcome_or_child_liveness(self):
        for field, value in [('source_sha256', 'bad'), ('outcome', 'ready'),
                             ('child_alive', False), ('reader_alive', True),
                             ('cause', None), ('cleanup_child_exit', 0)]:
            with self.subTest(field=field):
                record = copy.deepcopy(self.record())
                record['rows'][1][field] = value
                with self.assertRaises(ValueError):
                    validate(record)

    def test_rejects_clock_and_retry_aliases(self):
        for field, value in [('wait_start_ns', True), ('wait_end_ns', 0), ('end_ns', -1)]:
            record = copy.deepcopy(self.record())
            record['rows'][0][field] = value
            with self.assertRaises(ValueError):
                validate(record)
        record = self.record(); record['retries'] = True
        with self.assertRaises(ValueError):
            validate(record)
