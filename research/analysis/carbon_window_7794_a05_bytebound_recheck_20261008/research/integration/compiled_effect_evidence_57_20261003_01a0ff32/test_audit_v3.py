"""Retained-raw prefix corruptions, with --legacy exposing the v2 coverage gap."""
import copy
import importlib
import json
from pathlib import Path
import sys
import unittest

legacy = '--legacy' in sys.argv
if legacy:
    sys.argv.remove('--legacy')
auditor = importlib.import_module('audit' if legacy else 'audit_v3')

def mutations():
    changes = [('terminal_status', 'delivery_uncertain'), ('terminal_status', 'failed'),
               ('terminal_status', True), ('terminal_action', 'save'),
               ('terminal_id', 1), ('terminal_release', 1),
               ('execute_action', 'save'), ('execute_operation', 'save'),
               ('execute_authorization', 'other'), ('execute_sequence', True),
               ('execute_deadline', 10000001), ('transition_action', 'save'),
               ('effect_action', 'save'), ('branch_action', 'save'),
               ('observe_state', 'done'), ('verify_action', 'save')]
    return changes

def corrupt(record, kind, value):
    altered = copy.deepcopy(record)
    row = next(row for row in altered['rows'] if row['id'] == 'succeeded-9-1')
    if kind.startswith('terminal_') or kind in ('effect_action', 'branch_action'):
        event_name = {'effect_action': 'effect_checked', 'branch_action': 'branch_selected'}.get(kind, 'action_terminal')
        field = {'terminal_status': 'status', 'terminal_action': 'action',
                 'terminal_id': 'action_id', 'terminal_release': 'release_verified',
                 'effect_action': 'action', 'branch_action': 'action'}[kind]
        for events in (row['events'], row['result']['critical_events']):
            next(event for event in events if event['event'] == event_name)[field] = value
    elif kind.startswith('execute_'):
        field = {'execute_action': 'action', 'execute_operation': 'operation',
                 'execute_authorization': 'authorization', 'execute_sequence': 'expected_sequence',
                 'execute_deadline': 'valid_until_ns'}[kind]
        row['calls']['execute'][0][field] = value
    elif kind == 'transition_action':
        row['result']['transitions'][0]['action'] = value
    elif kind == 'observe_state':
        row['calls']['observe'][0]['state'] = value
    elif kind == 'verify_action':
        row['calls']['verify_effect'][0]['action'] = value
    else:
        raise ValueError(kind)
    return altered

class PrefixOracleTests(unittest.TestCase):
    def test_retained_rows_remain_reconciled(self):
        for filename in ('before.json', 'after.json'):
            with self.subTest(filename=filename):
                raw = json.loads(Path(__file__).with_name(filename).read_bytes())
                result = auditor.audit(raw)
                self.assertEqual(result['errors'], [])
                self.assertEqual(len(result['contract_violations']), 18 if filename == 'before.json' else 0)

    def test_impossible_prefixes_are_refused_in_both_arms(self):
        for filename in ('before.json', 'after.json'):
            raw = json.loads(Path(__file__).with_name(filename).read_bytes())
            for kind, value in mutations():
                with self.subTest(filename=filename, kind=kind, value=value):
                    self.assertTrue(auditor.audit(corrupt(raw, kind, value))['errors'])

if __name__ == '__main__':
    unittest.main()
