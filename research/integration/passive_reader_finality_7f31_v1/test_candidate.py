"""Excluded construction controls; no producer or formal data."""
import copy
import unittest
from candidate import classify


class Controls(unittest.TestCase):
    def test_contract(self):
        seal = {'schema': 'experimental-final-extent-v1', 'stream_id': 'owned',
                'final_size': 20, 'last_sequence': 2, 'sha256': 'a'*64}
        response = {'schema': 'agent-interface/experimental-inbox-read-v1',
                    'authority': 'none', 'acknowledged': False, 'input_dispatched': False,
                    'problem': None, 'records': [], 'tail_state': 'end',
                    'next_cursor': {'schema': 'agent-interface/experimental-read-cursor-v1',
                                    'stream_id': 'owned', 'offset': 20,
                                    'next_sequence': 3, 'prefix_sha256': 'a'*64}}
        self.assertEqual(classify(0, response, seal, 'owned'), 'COMPLETE')
        self.assertEqual(classify(None, response, seal, 'owned'), 'WAIT_PRODUCER')
        self.assertEqual(classify(7, response, seal, 'owned'), 'PRODUCER_FAILED')
        self.assertEqual(classify(0, response, None, 'owned'), 'UNKNOWN')
        self.assertEqual(classify(False, response, seal, 'owned'), 'UNKNOWN')
        bad = copy.deepcopy(response); bad['tail_state'] = 'incomplete'
        self.assertEqual(classify(0, bad, seal, 'owned'), 'INCOMPLETE')
        for key, value in [('final_size', True), ('last_sequence', False),
                           ('stream_id', 'other'), ('sha256', 'b'*64), ('extra', 1)]:
            with self.subTest(seal=key):
                bad = dict(seal); bad[key] = value
                self.assertEqual(classify(0, response, bad, 'owned'), 'UNKNOWN')
        for key, value in [('authority', 'input'), ('acknowledged', True),
                           ('input_dispatched', True), ('records', [{'event': 'late'}])]:
            with self.subTest(response=key):
                bad = copy.deepcopy(response); bad[key] = value
                self.assertEqual(classify(0, bad, seal, 'owned'), 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
