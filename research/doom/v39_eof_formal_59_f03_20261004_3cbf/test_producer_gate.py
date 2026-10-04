"""A missing ready handshake must stop the producer, not merely fail audit."""
import copy
import json
from pathlib import Path
import unittest
import signal
import threading
from runner import sigint_blocked_reader
import tempfile
import runner
from runner import expected


class ProducerGateControls(unittest.TestCase):
    def test_reader_worker_blocks_sigint_during_cleanup(self):
        observed = []
        thread = threading.Thread(target=lambda: sigint_blocked_reader(
            lambda: observed.append(signal.SIGINT in signal.pthread_sigmask(signal.SIG_BLOCK, set()))))
        thread.start(); thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(observed, [True])

    def row(self):
        lines = (Path(__file__).parent / 'methods/RUNNER-CONSTRUCTION.log').read_text().splitlines()
        row = next(json.loads(line) for line in lines if line.startswith('{')
                    and json.loads(line).get('case') == 'candidate_events_eof')
        row.update(cleanup_child_alive=False, cleanup_reader_alive=False)
        return row

    def test_live_cleanup_cannot_pass_producer(self):
        row = self.row(); row['cleanup_reader_alive'] = True
        self.assertFalse(expected('candidate_events_eof', row))

    def test_valid_handshake(self):
        self.assertTrue(expected('candidate_events_eof', self.row()))

    def test_missing_source_records_stop_without_cells(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            original = runner.PACKAGES
            try:
                runner.PACKAGES = root
                try:
                    result = runner.run(root / 'output')
                except FileNotFoundError:
                    self.fail('preflight source failure escaped without a saved STOP')
                self.assertEqual(result, 1)
            finally:
                runner.PACKAGES = original
            files = list((root / 'output').iterdir())
            self.assertEqual([path.name for path in files], ['SUMMARY.json'])
            summary = json.loads(files[0].read_text())
            self.assertEqual(summary['verdict'], 'STOP_PREFLIGHT_SOURCE')
            self.assertEqual(summary['cases'], [])
            self.assertEqual(summary['error_type'], 'FileNotFoundError')

    def test_missing_live_handshake_stops(self):
        for field, value in [('reader_alive_after_ready', False),
                             ('ready', {'event': 'terminal'}), ('terminal', None)]:
            row = copy.deepcopy(self.row()); row[field] = value
            with self.subTest(field=field):
                self.assertFalse(expected('candidate_events_eof', row))
