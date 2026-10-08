import copy
import json
import os
from pathlib import Path
import unittest

import adaptive_acquisition_caller_v3 as caller
ROWS = []
SPEC = {'target': 'button', 'route': 'reuse', 'coarse_origin': 'caller_provided',
        'provided_coarse': None, 'cached_target': {'id': 'button'},
        'local_repair_on': [], 'repair_on': [], 'session_id': 'I19-inert'}
UNCERTAIN = {'status': 'safe_yield', 'reason': 'delivery_uncertain',
             'completed_actions': 1, 'input_dispatched': True}
REFUSED = {'status': 'safe_yield', 'reason': 'execution_refused',
           'completed_actions': 0, 'input_dispatched': False}

def cell(receipt, fault='healthy', mutation=None):
    original = copy.deepcopy(receipt)
    state = {'clock': 0, 'execute': 0, 'verify': 0, 'events': []}
    def change():
        original.clear(); original.update(copy.deepcopy(mutation))
    def clock():
        state['clock'] += 1
        if state['clock'] == 6:
            if fault == 'clock_mutate': change()
            if fault == 'clock_raise': raise RuntimeError('end clock failed')
            if fault == 'clock_typed':
                raise caller.ModelFailure('auxiliary failure', typed_status='DEFERRED_UPSTREAM')
        return state['clock']
    def journal(event):
        state['events'].append(copy.deepcopy(event))
        if event['event'] == 'stage_completed' and event['stage'] == 'execute':
            if fault == 'journal_mutate': change()
            if fault == 'journal_raise': raise RuntimeError('completion journal failed')
    def execute(payload):
        state['execute'] += 1
        if fault == 'execute_raise': raise RuntimeError('execute did not return')
        return original
    def verify(payload):
        state['verify'] += 1
        if fault == 'verify_raise': raise RuntimeError('effect verifier failed')
        return {'status': 'succeeded'}
    result = caller.run(copy.deepcopy(SPEC), {
        'reuse_revalidate': lambda payload: {'status': 'revalidated'},
        'final_revalidate': lambda payload: {'status': 'revalidated'},
        'execute': execute, 'verify_effect': verify, 'journal': journal}, clock=clock)
    ROWS.append({'receipt': copy.deepcopy(receipt), 'fault': fault,
                 'mutation': copy.deepcopy(mutation), 'result': result, 'state': state})
    return result, state

class CustodyTests(unittest.TestCase):
    def test_receipt_survives_auxiliary_exceptions(self):
        for receipt, delivery, authority in [
            (UNCERTAIN, 'delivery_uncertain', 'consumed_by_recorded_execute_stage'),
            (REFUSED, 'not_attempted', 'none'),
            ({'status': 'completed'}, 'confirmed', 'consumed_by_recorded_execute_stage'),
            ({'status': 'delivery_uncertain'}, 'delivery_uncertain', 'consumed_by_recorded_execute_stage'),
            ({'status': 'failed'}, 'failed', 'consumed_by_recorded_execute_stage')]:
            for fault in ['clock_raise', 'journal_raise', 'clock_typed']:
                with self.subTest(receipt=receipt, fault=fault):
                    result, state = cell(receipt, fault)
                    self.assertEqual(result['execution_progress'], receipt)
                    self.assertEqual(result['delivery'], delivery)
                    self.assertEqual(result['input_authority'], authority)
                    self.assertIsNone(result['task_effect'])
                    self.assertEqual((state['execute'], state['verify']), (1, 0))
                    self.assertEqual(result['stages']['execute']['status'],
                                     'completed' if fault == 'journal_raise' else 'started')
                    self.assertEqual(result['accounting']['attempted_calls'], 0)

    def test_detached_receipt_drives_control_flow(self):
        for fault in ['clock_mutate', 'journal_mutate']:
            with self.subTest(fault=fault):
                result, state = cell(UNCERTAIN, fault, REFUSED)
                self.assertEqual(result['execution_progress'], UNCERTAIN)
                self.assertEqual(result['delivery'], 'delivery_uncertain')
                self.assertEqual(result['outcome'], 'EXECUTION_INCOMPLETE')
                self.assertEqual(result['input_authority'], 'consumed_by_recorded_execute_stage')
                self.assertEqual((state['execute'], state['verify']), (1, 0))

    def test_malformed_receipt_cannot_be_promoted_by_callback(self):
        invalid = {'status': 'safe_yield', 'reason': 'cancelled',
                   'completed_actions': 1, 'input_dispatched': False}
        for fault in ['healthy', 'clock_mutate', 'journal_mutate', 'clock_raise', 'journal_raise']:
            with self.subTest(fault=fault):
                result, state = cell(invalid, fault, {'status': 'completed'})
                self.assertEqual(result['outcome'], 'CALLER_FAILED')
                self.assertIsNone(result['execution_progress'])
                self.assertEqual(result['delivery'], 'delivery_uncertain')
                self.assertEqual((state['execute'], state['verify']), (1, 0))

    def test_effect_verifier_failure_preserves_delivery_without_success(self):
        result, state = cell({'status': 'completed'}, 'verify_raise')
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        self.assertEqual(result['delivery'], 'confirmed')
        self.assertEqual(result['execution_progress'], {'status': 'completed'})
        self.assertIsNone(result['task_effect'])
        self.assertEqual((state['execute'], state['verify']), (1, 1))

    def test_healthy_and_no_return_controls(self):
        for receipt, outcome, delivery in [(UNCERTAIN, 'EXECUTION_INCOMPLETE', 'delivery_uncertain'),
                                          (REFUSED, 'EXECUTION_INCOMPLETE', 'not_attempted'),
                                          ({'status': 'completed'}, 'TASK_SUCCEEDED', 'confirmed')]:
            with self.subTest(receipt=receipt):
                result, state = cell(receipt)
                self.assertEqual((result['outcome'], result['delivery']), (outcome, delivery))
                self.assertEqual(result['execution_progress'], receipt)
                self.assertEqual((state['execute'], state['verify']), (1, int(receipt['status'] == 'completed')))
        result, state = cell(UNCERTAIN, 'execute_raise')
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        self.assertIsNone(result['execution_progress'])
        self.assertEqual(result['delivery'], 'delivery_uncertain')
        self.assertEqual((state['execute'], state['verify']), (1, 0))

if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        if os.environ.get('ROWS_PATH'):
            Path(os.environ['ROWS_PATH']).write_text(json.dumps(ROWS, sort_keys=True, indent=2), encoding='utf-8')
