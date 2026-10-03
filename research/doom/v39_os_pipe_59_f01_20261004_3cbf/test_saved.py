import copy
import json
from pathlib import Path
import unittest
from verify_saved import validate


class SavedBoundary(unittest.TestCase):
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
