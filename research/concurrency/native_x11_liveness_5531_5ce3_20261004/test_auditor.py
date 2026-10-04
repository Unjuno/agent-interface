"""Explicit synthetic audit schema fixtures, never native evidence."""
import copy, unittest
from auditor import check, negatives

def fixture():
    rows = []
    for repeat in range(3):
        for mode in ('healthy_fast', 'healthy_server_blocked', 'killed_server_blocked', 'invalid_response'):
            blocked = mode.endswith('server_blocked'); killed = mode == 'killed_server_blocked'; invalid = mode == 'invalid_response'
            ident = {'pid': 100+len(rows), 'start_ticks': 40, 'nonce': 'a'*36}
            ready = {'kind': 'READY', **ident}
            messages = [{'kind': 'QUERY_STARTED', **ident, 'query_started_ns': 1100000}]
            if not killed: messages.append({'kind': 'RESULT', **ident, 'focus': 1000+int(invalid), 'native_focus': 1000, 'query_finished_ns': 110000000 if blocked else 2000000})
            state = 'FAILED' if killed else ('SUSPECTED_UNAVAILABLE' if blocked else ('EVIDENCE_INVALID' if invalid else 'RESPONSIVE_SCOPED'))
            rows.append({'mode': mode, 'repeat': repeat, 'authority': False, 'input_emissions': 0, 'ready': ready, 'messages': messages, 'parent_observed_pid': ident['pid'], 'parent_start_ticks': 40, 'go_ns': 1000000, 'query_start_received_ns': 1200000, 'budget_observed_ns': 32000000, 'expected_focus': 1000, 'fixture_focus': 1000, 'oracle_focus_after': 1000, 'worker_exit': -9 if killed else 0, 'cleanup': {'worker_exit': -9 if killed else 0, 'server_exit': 0, 'keymap_empty': True, 'observed_buttons_1_to_3_neutral': True, 'controller_closed': True}, 'grab_confirmed_ns': 500000, 'ungrab_ns': 102000000, 'result_available_at_budget': not blocked, 'kill_ns': 12000000, 'terminal_at_budget': -9 if killed else (None if blocked else 0), 'response_valid': None if killed else not invalid, 'response_received_ns': 111000000 if blocked else 32000000, 'waitpid_observed_ns': 112000000, 'at_budget': state, 'final': 'FAILED' if killed else ('EVIDENCE_INVALID' if invalid else 'RESPONSIVE_SCOPED'), 'baseline_at_budget': 'FAILED' if blocked else state})
    return rows

class AuditTests(unittest.TestCase):
    def test_complete_synthetic_fixture(self):
        self.assertEqual(check(fixture()), 'SUPPORTED_NATIVE_LIVENESS_BOUNDARY_SCOPED')
    def test_eight_controls_are_effective_and_reject(self):
        self.assertEqual(len(negatives(fixture())), 8)
    def test_partial_rejected(self):
        with self.assertRaises(AssertionError): check(fixture()[:-1])
    def test_fast_finished_after_nominal_budget_holds(self):
        rows = fixture(); rows[0]['messages'][1]['query_finished_ns'] = 31500000
        self.assertEqual(check(rows), 'HOLD_CLOCK_BOUNDARY')
    def test_same_generation_required(self):
        rows = fixture(); rows[1]['messages'][1]['start_ticks'] = 41
        with self.assertRaises(AssertionError): check(rows)
    def test_late_reply_before_release_rejected(self):
        rows = fixture(); rows[1]['messages'][1]['query_finished_ns'] = 90000000
        with self.assertRaises(AssertionError): check(rows)

if __name__ == '__main__': unittest.main()
