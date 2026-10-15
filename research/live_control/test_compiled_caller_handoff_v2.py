"""Actual core/compiler/caller handoff, with inert input/effect adapters."""
import copy
import importlib
import os
import time
import unittest

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    compile_form_method, EXPECTED_METHOD_CONTRACT,
)

ROWS = []


class OwnedStop(BaseException):
    pass


STOP = OwnedStop('owned inert stop')


def cell(case='healthy', effect='succeeded', mutate_sink=False, journal_fault=None):
    module = importlib.import_module(os.environ.get('COMPILED_CALLER_MODULE',
        'research.live_control.integrated_efficiency_compiled_execution_v2'))
    legacy = module.__name__.endswith('_v1')
    state = {'sequence': 0, 'execute': [], 'verify': 0, 'sink': 0}
    raw, events = [], []
    interface = compile_form_method(interface_id='inert-v3-interface',
        session_scope='inert-v3-scope', surface='inert', field_handle='field',
        submit_handle='submit', method_contract=EXPECTED_METHOD_CONTRACT)

    def observe(_):
        state['sequence'] += 1
        n = len(state['execute'])
        return dict(sequence=state['sequence'], captured_ns=time.perf_counter_ns(),
            surface='inert', predicates=dict(field_pixels_changed=n > 0,
                field_value_matches_task=n > 0, field_target_present=True,
                submit_target_present=True, submission_pixels_changed=n > 1),
            evidence_ref='inert-frame-' + str(state['sequence']),
            evidence_digest='inert-digest-' + str(state['sequence']))

    def admit(payload):
        return dict(eligible=case != 'admission_refused',
            status='missing' if case == 'admission_refused' else 'revalidated',
            authorization=None if case == 'admission_refused' else 'INERT_NO_AUTHORITY',
            expected_sequence=payload['observation']['sequence'],
            valid_until_ns=time.perf_counter_ns() + 1_000_000_000)

    def execute(payload):
        state['execute'].append(copy.deepcopy(payload))
        n = len(state['execute'])
        if case == 'execute_throws' and n == 2:
            raise OSError('inert execute failure without returned core receipt')
        unknown = case == 'release_first' and n == 1 or case in ('release_second', 'sink_release') and n == 2
        refused = case == 'preinput_refusal'
        terminal = dict(status='refused' if refused else 'failed' if case == 'unknown_delivery' else 'completed',
            action_id=None if refused else 'inert-action-' + str(n),
            effect_ref=None if refused else 'inert-effect-' + str(n),
            release=dict(verified=not unknown and not refused,
                keys_down=['inert-held'] if unknown else [], buttons_down=[]))
        if case != 'unknown_delivery':
            terminal['input_dispatched'] = not refused
        return terminal

    def sink(receipt):
        state['sink'] += 1
        raw.append(copy.deepcopy(receipt))
        if mutate_sink:
            receipt.clear()
        if case in ('sink_failure', 'sink_release'):
            raise OSError('inert receipt sink failure')
        if case == 'sink_stop':
            raise STOP

    def verify(_):
        state['verify'] += 1
        return dict(status=effect, evidence_ref='inert-independent-reference')

    def journal(event):
        events.append(copy.deepcopy(event))
        if journal_fault == event['event']:
            raise OSError('inert caller journal failure')

    spec = dict(target='inert form', route='reuse', coarse_origin='caller_provided',
        provided_coarse=None, cached_target={'id': 'inert'}, repair_on=[], session_id='inert')
    if not legacy:
        spec['local_repair_on'] = []
    try:
        result = module.run_compiled_interface_in_caller(spec,
            {'reuse_revalidate': lambda _: {'status': 'revalidated'},
             'final_revalidate': lambda _: {'status': 'revalidated'},
             'verify_effect': verify, 'journal': journal}, interface,
            dict(observe=observe, admit=admit, execute=execute,
                verify_effect=lambda _: {'status': 'succeeded', 'evidence_ref': 'inert-core-effect'},
                cancelled=lambda: False), on_receipt=sink)
    except Exception as error:
        raise AssertionError('ordinary handoff failure escaped instead of returning a receipt') from error
    row = dict(case=case, effect=effect, mutate_sink=mutate_sink,
        journal_fault=journal_fault, result=result, state=state, raw=raw, events=events)
    ROWS.append(copy.deepcopy(row))
    return row


class CompiledCallerHandoffTests(unittest.TestCase):
    def test_unverified_outer_effect_retains_completed_execution_and_evidence(self):
        for effect in ('failed', 'unavailable'):
            with self.subTest(effect=effect):
                row = cell(effect=effect); r = row['result']
                self.assertEqual(r['execution_progress'], {'status': 'completed'})
                self.assertEqual(r['outcome'], 'TASK_NOT_VERIFIED')
                self.assertEqual(r['effect_receipt'], {'status': effect, 'evidence_ref': 'inert-independent-reference'})
                self.assertEqual(r['compiled_execution_receipt']['completed_transitions'], 2)

    def test_sink_failure_retains_known_completion_and_original_failure(self):
        row = cell('sink_failure'); r = row['result']
        self.assertEqual(r['execution_progress'], {'status': 'completed'})
        self.assertEqual(r['delivery'], 'confirmed')
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertIsNone(r['task_effect'])
        self.assertEqual(row['state']['verify'], 0)
        self.assertEqual(r['compiled_receipt_publication_error']['type'], 'OSError')
        self.assertIn('inert receipt sink failure', r['reason'])
        self.assertEqual(r['compiled_execution_receipt']['completed_transitions'], 2)

    def test_unknown_release_retains_prefix_and_uncertain_current_input(self):
        for case, prefix in (('release_first', 0), ('release_second', 1)):
            with self.subTest(case=case):
                row = cell(case); r = row['result']
                self.assertEqual(r['execution_progress'], {'status': 'safe_yield',
                    'reason': 'execution_failed', 'completed_actions': prefix, 'input_dispatched': True})
                self.assertEqual(r['delivery'], 'delivery_uncertain')
                self.assertEqual(r['outcome'], 'EXECUTION_INCOMPLETE')
                self.assertEqual(row['state']['verify'], 0)
                self.assertEqual(len(row['state']['execute']), prefix + 1)
                self.assertEqual(r['compiled_execution_receipt']['outcome'], 'RUNTIME_FAILED')

    def test_sink_cannot_mutate_retained_receipt_or_decision(self):
        row = cell(mutate_sink=True); r = row['result']
        self.assertEqual(r['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(r.get('compiled_execution_receipt'), row['raw'][0])
        self.assertEqual(r['compiled_execution_receipt']['completed_transitions'], 2)

    def test_sink_failure_after_unknown_release_keeps_both_facts(self):
        row = cell('sink_release', mutate_sink=True); r = row['result']
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertEqual((r['execution_progress'] or {}).get('completed_actions'), 1)
        self.assertEqual(r['delivery'], 'delivery_uncertain')
        self.assertEqual(r['compiled_execution_receipt'], row['raw'][0])
        self.assertEqual(row['state']['verify'], 0)

    def test_explicit_no_input_refusal_and_admission_refusal(self):
        for case in ('preinput_refusal', 'admission_refused'):
            with self.subTest(case=case):
                row = cell(case); r = row['result']
                self.assertIs(r['execution_progress'].get('input_dispatched'), False)
                self.assertEqual(r['delivery'], 'not_attempted')
                self.assertEqual(r['input_authority'], 'none')
                self.assertEqual(row['state']['verify'], 0)

    def test_unknown_delivery_does_not_invent_no_input(self):
        row = cell('unknown_delivery'); r = row['result']
        self.assertEqual(r['delivery'], 'delivery_uncertain')
        self.assertNotIn('input_dispatched', r['execution_progress'])
        self.assertEqual(row['state']['verify'], 0)

    def test_journal_failures_do_not_erase_sink_failure_progress(self):
        for fault in ('stage_failed', 'adaptive_route_finished'):
            with self.subTest(fault=fault):
                row = cell('sink_failure', journal_fault=fault); r = row['result']
                self.assertEqual(r['execution_progress'], {'status': 'completed'})
                self.assertEqual(r['delivery'], 'confirmed')
                self.assertEqual(r['outcome'], 'CALLER_FAILED')
                self.assertEqual(r['compiled_receipt_publication_error']['type'], 'OSError')
                self.assertEqual(row['state']['verify'], 0)

    def test_unreturned_core_receipt_stays_uncertain_without_prefix_invention(self):
        row = cell('execute_throws'); r = row['result']
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertEqual(r['delivery'], 'delivery_uncertain')
        self.assertIsNone(r['execution_progress'])
        self.assertIsNone(r['compiled_execution_receipt'])
        self.assertEqual(len(row['state']['execute']), 2)
        self.assertEqual(row['state']['sink'], 0)
        self.assertEqual(row['state']['verify'], 0)

    def test_non_exception_sink_stop_propagates_original(self):
        with self.assertRaises(OwnedStop) as raised:
            cell('sink_stop')
        self.assertIs(raised.exception, STOP)

    def test_typed_execution_receipt_is_detached_and_validated(self):
        from research.live_control.adaptive_acquisition_caller_v3 import ExecutionReceiptError
        decision = {'status': 'completed'}
        error = ExecutionReceiptError(decision, OSError('inert cause'))
        decision.clear()
        error.execution_progress.clear()
        self.assertEqual(error.execution_progress, {'status': 'completed'})
        with self.assertRaises(ValueError):
            ExecutionReceiptError({'status': 'safe_yield', 'reason': 'cancelled',
                'completed_actions': 1, 'input_dispatched': False}, OSError('inert'))

    def test_receipt_exception_is_accepted_only_at_execute_and_ordinary_attributes_are_ignored(self):
        from research.live_control import adaptive_acquisition_caller_v3 as caller
        for stage, typed in (('execute', True), ('execute', False), ('final_revalidate', True)):
            with self.subTest(stage=stage, typed=typed):
                error = (caller.ExecutionReceiptError({'status': 'completed'}, OSError('inert'))
                         if typed else RuntimeError('ordinary inert error'))
                if not typed:
                    error.execution_progress = {'status': 'completed'}
                def fail(_):
                    raise error
                adapters = {'reuse_revalidate': lambda _: {'status': 'revalidated'},
                    'final_revalidate': lambda _: {'status': 'revalidated'},
                    'execute': lambda _: {'status': 'completed'}}
                adapters[stage] = fail
                result = caller.run(dict(target='inert', route='reuse',
                    coarse_origin='caller_provided', provided_coarse=None,
                    cached_target={'id': 'inert'}, local_repair_on=[], repair_on=[],
                    session_id='inert'), adapters)
                self.assertEqual(result['outcome'], 'CALLER_FAILED')
                self.assertEqual(result['execution_progress'], {'status': 'completed'}
                                 if typed and stage == 'execute' else None)
                self.assertIsNone(result['task_effect'])


if __name__ == '__main__':
    unittest.main()
