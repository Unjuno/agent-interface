import copy
import json
import unittest
from pathlib import Path

from audit import audit


class AvailabilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(Path('/in/HOST_STATE.json').read_text(encoding='utf-8'))

    def test_captured_host_stops_before_any_model_or_task_call(self):
        result = audit(self.base)
        self.assertEqual(result, {
            'status': 'STOP_ROUTE_UNAVAILABLE',
            'servers': ['codex_app', 'cua_repl', 'node_repl'],
            'errors': [],
        })

    def test_presence_summary_corruption_rejected(self):
        changed = copy.deepcopy(self.base)
        changed['agent_interface_server_listed'] = True
        self.assertIn('presence_summary_mismatch', audit(changed)['errors'])

    def test_merely_configured_server_is_not_matched_model_pass(self):
        changed = copy.deepcopy(self.base)
        changed['servers'].append({
            'name': 'agent_interface_integration',
            'status': 'enabled',
            'auth': 'Supported',
        })
        changed['agent_interface_server_listed'] = True
        self.assertEqual(audit(changed)['status'], 'HOLD_MODEL_VISIBILITY_UNPROVEN')

    def test_unreported_model_call_is_rejected(self):
        changed = copy.deepcopy(self.base)
        changed['model_calls'] = 1
        self.assertIn('unexpected_call', audit(changed)['errors'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
