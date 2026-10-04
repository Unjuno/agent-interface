import copy
import unittest
from gate import release_gate


class ReleaseGateTests(unittest.TestCase):
    def sample(self):
        return {
            'id': 'pulse', 'expected_token': 'lease01',
            'accepted': {'event': 'accepted', 'id': 'pulse', 'intent_token': 'lease01'},
            'cancel': {'event': 'cancel_requested', 'id': 'pulse', 'matched': True},
            'released': {'event': 'input_released', 'id': 'pulse', 'intent_token': 'lease01', 'emit_ns': 30,
                         'owner_release': {'reason': 'cancelled', 'verified': True, 'keys_down': [], 'buttons_down': []}},
            'terminal': {'event': 'terminal', 'id': 'pulse', 'status': 'cancelled',
                         'emit_ns': 40,
                         'interruption': {'intent_token': 'lease01', 'record': {'reason': 'cancelled', 'verified': True, 'keys_down': [], 'buttons_down': []}},
                         'release': {'verified': True, 'keys_down': [], 'buttons_down': []}},
            'before': {'keys': [], 'buttons': []},
            'held': {'keys': [114], 'buttons': []},
            'after': {'keys': [], 'buttons': []},
            'right_code': 114, 'child_exit': 0, 'cleanup_faults': [],
        }

    def test_real_semantic_fixture_accepts(self):
        self.assertTrue(release_gate(self.sample()))

    def test_rejects_missing_or_wrong_release_custody(self):
        changes = [
            ('accepted', 'id', 'alien'), ('released', 'intent_token', 'alien'),
            ('cancel', 'matched', False), ('terminal', 'status', 'completed'),
            ('terminal', 'id', 'alien'), ('after', 'keys', [114]),
            ('after', 'buttons', [1]), ('held', 'keys', []),
            ('before', 'keys', [114]),
        ]
        for section, key, value in changes:
            with self.subTest(section=section, key=key, value=value):
                row = copy.deepcopy(self.sample()); row[section][key] = value
                self.assertFalse(release_gate(row))

    def test_rejects_truthy_verification_and_held_release(self):
        for section in ('released', 'terminal'):
            for field, value in [('verified', 1), ('keys_down', [114]), ('buttons_down', [1])]:
                with self.subTest(section=section, field=field):
                    row = self.sample()
                    nested = 'owner_release' if section == 'released' else 'release'
                    row[section][nested][field] = value
                    self.assertFalse(release_gate(row))

    def test_rejects_failed_or_unknown_cleanup(self):
        for key, value in [('child_exit', True), ('child_exit', 1),
                           ('cleanup_faults', ['failure']), ('expected_token', None)]:
            row = self.sample(); row[key] = value
            self.assertFalse(release_gate(row))

    def test_rejects_terminal_interruption_custody_and_release_order(self):
        for mode in ('token', 'record', 'reason', 'order', 'truthy_interruption'):
            row = self.sample()
            if mode == 'token': row['terminal']['interruption']['intent_token'] = 'alien'
            elif mode == 'record': row['terminal']['interruption']['record']['keys_down'] = [114]
            elif mode == 'reason': row['released']['owner_release']['reason'] = 'expired'
            elif mode == 'order': row['released']['emit_ns'] = 50
            elif mode == 'truthy_interruption': row['terminal']['interruption']['record']['verified'] = 1
            with self.subTest(mode=mode):
                self.assertFalse(release_gate(row))


if __name__ == '__main__':
    unittest.main()
