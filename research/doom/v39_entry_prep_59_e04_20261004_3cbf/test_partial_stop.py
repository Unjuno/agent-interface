"""Catch fabricated successful or exposed histories being accepted as STOP."""
import copy
import unittest
from partial_stop import classify_partial_stop


ROW = {'case': 'original_fault', 'id': 'e04-original_fault', 'child_exit': 1,
       'start_ns': 100, 'end_ns': 200, 'release_gate': False,
       'outcome_gate': False, 'cleanup_faults': [], 'unhandled': [],
       'fatal': 'RuntimeError: session exited before expected event',
       'pid': 8, 'command': ['python3', '-B', '/experiment/session_entry.py']}
STDERR = b'Traceback:\nModuleNotFoundError: No module named example\n'


class PartialStopControls(unittest.TestCase):
    def test_valid_record_preserves_stop_not_science_pass(self):
        self.assertEqual(classify_partial_stop(ROW, b'', STDERR, False),
            {'saved_disposition': 'VERIFIED_PARTIAL_STARTUP_STOP',
             'scientific_pass': False, 'exposure': 'NOT_ESTABLISHED'})

    def test_refuses_imported_or_nonempty_stdout(self):
        for output, present in [(b'', True), (b'{"event":"ready"}\n', False)]:
            with self.subTest(output=output, imports=present), self.assertRaises(ValueError):
                classify_partial_stop(ROW, output, STDERR, present)

    def test_refuses_unknown_or_successful_terminal_and_cleanup(self):
        for field, value in [('child_exit', 0), ('child_exit', True),
                ('child_exit', None), ('cleanup_faults', ['kill']), ('unhandled', ['error'])]:
            row = copy.deepcopy(ROW); row[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                classify_partial_stop(row, b'', STDERR, False)

    def test_refuses_truthy_gate_aliases(self):
        for field in ['release_gate', 'outcome_gate']:
            for value in [True, 0, None]:
                row = copy.deepcopy(ROW); row[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    classify_partial_stop(row, b'', STDERR, False)

    def test_refuses_any_exposure_fields_even_null(self):
        for field in ['ready', 'before', 'held', 'accepted', 'injected_ns',
                      'wait_outcome', 'cancel', 'released', 'terminal', 'after']:
            row = copy.deepcopy(ROW); row[field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                classify_partial_stop(row, b'', STDERR, False)

    def test_refuses_unrecognized_and_other_producer_exposure_fields(self):
        for field in ['submit', 'after_notification', 'wait_start_ns', 'initial', 'future_field']:
            row = copy.deepcopy(ROW); row[field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                classify_partial_stop(row, b'', STDERR, False)

    def test_refuses_missing_failure_identity_and_chronology(self):
        for field, value in [('fatal', ''), ('case', ''), ('id', ''), ('pid', True),
                ('command', []), ('start_ns', True), ('end_ns', 99), ('end_ns', 100)]:
            row = copy.deepcopy(ROW); row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                classify_partial_stop(row, b'', STDERR, False)
        with self.assertRaises(ValueError):
            classify_partial_stop(ROW, b'', b'', False)


if __name__ == '__main__':
    unittest.main()
