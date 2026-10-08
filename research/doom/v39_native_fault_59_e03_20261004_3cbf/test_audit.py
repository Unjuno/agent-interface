import copy
import unittest
from audit import semantic_check


class AuditControls(unittest.TestCase):
    def fixture(self):
        events = [
            {'event': 'accepted', 'id': 'p', 'intent_token': 't', 'emit_ns': 10},
            {'event': 'cancel_requested', 'id': 'p', 'matched': True, 'emit_ns': 20},
            {'event': 'input_released', 'id': 'p', 'intent_token': 't', 'emit_ns': 30,
             'owner_release': {'reason': 'cancelled', 'verified': True, 'keys_down': [], 'buttons_down': []}},
            {'event': 'terminal', 'id': 'p', 'status': 'cancelled', 'emit_ns': 40,
             'interruption': {'intent_token': 't', 'record': {'reason': 'cancelled', 'verified': True, 'keys_down': [], 'buttons_down': []}},
             'release': {'verified': True, 'keys_down': [], 'buttons_down': []}},
        ]
        row = {'id': 'p', 'accepted': events[0], 'cancel': events[1], 'released': events[2],
               'terminal': events[3], 'expected_token': 't', 'right_code': 114,
               'before': {'keys': [], 'buttons': []}, 'held': {'keys': [114], 'buttons': []},
               'after': {'keys': [], 'buttons': []}, 'after_ns': 50,
               'child_exit': 0, 'cleanup_faults': [], 'fatal': None}
        return copy.deepcopy(row), copy.deepcopy(events)

    def test_accepts_hand_checked_cancelled_empty_trace(self):
        row, events = self.fixture(); self.assertTrue(semantic_check(row, events))

    def test_rejects_raw_order_and_custody_controls(self):
        for mode in ('duplicate', 'swapped', 'missing', 'token', 'id', 'truthy', 'held', 'completed', 'truthy_interruption'):
            with self.subTest(mode=mode):
                row, events = self.fixture()
                if mode == 'duplicate': events.append(events[2])
                elif mode == 'swapped': events[2], events[3] = events[3], events[2]
                elif mode == 'missing': events.pop(2)
                elif mode == 'token': events[2]['intent_token'] = 'alien'
                elif mode == 'id': events[3]['id'] = 'alien'
                elif mode == 'truthy': events[2]['owner_release']['verified'] = 1
                elif mode == 'held': row['after']['keys'] = [114]
                elif mode == 'completed': events[3]['status'] = 'completed'
                elif mode == 'truthy_interruption':
                    events[3]['interruption']['record']['verified'] = 1
                    row['terminal']['interruption']['record']['verified'] = 1
                self.assertFalse(semantic_check(row, events))


if __name__ == '__main__':
    unittest.main()
