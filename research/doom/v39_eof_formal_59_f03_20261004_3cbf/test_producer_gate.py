"""A missing ready handshake must stop the producer, not merely fail audit."""
import copy
import json
from pathlib import Path
import unittest
from runner import expected


class ProducerGateControls(unittest.TestCase):
    def row(self):
        lines = (Path(__file__).parent / 'methods/RUNNER-CONSTRUCTION.log').read_text().splitlines()
        return next(json.loads(line) for line in lines if line.startswith('{')
                    and json.loads(line).get('case') == 'candidate_events_eof')

    def test_valid_handshake(self):
        self.assertTrue(expected('candidate_events_eof', self.row()))

    def test_missing_live_handshake_stops(self):
        for field, value in [('reader_alive_after_ready', False),
                             ('ready', {'event': 'terminal'}), ('terminal', None)]:
            row = copy.deepcopy(self.row()); row[field] = value
            with self.subTest(field=field):
                self.assertFalse(expected('candidate_events_eof', row))
