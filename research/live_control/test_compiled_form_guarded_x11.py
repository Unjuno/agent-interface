"""Exact-value form through the actual guarded X11 adapter, no real display."""
import copy
import unittest

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    compile_form_method, EXPECTED_METHOD_CONTRACT,
)
from runtime.guarded_x11_v1.compiled import run, _Adapter
from runtime.guarded_x11_v1 import test_compiled as fixtures

ROWS = []


def cell(mode='exact'):
    bridge = fixtures.Bridge()
    interface = compile_form_method(interface_id='inert-guarded-form',
        session_scope=bridge.scope, surface='x11-window-20',
        field_handle='field', submit_handle='submit',
        method_contract=EXPECTED_METHOD_CONTRACT)
    def perceive(native, image):
        phase = image.getpixel((0, 0))[0]
        value = phase > 0
        if mode == 'already_exact':
            value = True
        elif phase and mode == 'wrong':
            value = False
        elif phase and mode == 'unknown':
            value = 'unknown'
        return dict(field_pixels_changed=phase > 0, field_value_matches_task=value,
            field_target_present=mode != 'missing_field',
            submit_target_present=not (phase and mode == 'missing_submit'),
            submission_pixels_changed=phase > 1)
    effects = []
    def verify(payload, native, image):
        effects.append(copy.deepcopy(payload))
        return {'status': 'succeeded', 'evidence_ref': payload['observation']['evidence_ref']}
    result = run(bridge, interface,
        {'enter_token': {'interaction': 'click', 'offset': [2, 2],
                         'tail': [{'op': 'text', 'text': 'inert-exact-token'}]},
         'submit_form': {'interaction': 'click', 'offset': [2, 2], 'tail': []}},
        perceive=perceive, verify_effect=verify)
    row = dict(mode=mode, interface=interface, result=result,
        inputs=copy.deepcopy(bridge.inputs), saved=copy.deepcopy(bridge.saved),
        effect_calls=effects, resolution_calls=bridge.store.resolve_point.call_count)
    ROWS.append(row)
    return row


class CompiledFormGuardedX11Tests(unittest.TestCase):
    def test_submit_admission_still_requires_observed_exact_value(self):
        bridge = fixtures.Bridge()
        interface = compile_form_method(interface_id='inert-submit-admission',
            session_scope=bridge.scope, surface='x11-window-20',
            field_handle='field', submit_handle='submit',
            method_contract=EXPECTED_METHOD_CONTRACT)
        adapter = _Adapter(bridge, interface,
            {a: {'interaction': 'click', 'offset': [2, 2], 'tail': []}
             for a in ('enter_token', 'submit_form')},
            lambda native, image: dict(field_pixels_changed=False,
                field_value_matches_task=False, field_target_present=True,
                submit_target_present=True, submission_pixels_changed=False),
            lambda *args: {'status': 'succeeded', 'evidence_ref': 'inert'}, lambda: False)
        observation = adapter.observe({})
        result = adapter.admit(dict(interface_id=interface['interface_id'],
            session_scope=bridge.scope, action='submit_form', operation='activate_submit',
            symbol=interface['symbols']['submit_control'], observation=observation))
        ROWS.append(dict(mode='direct_submit_admission', interface=interface,
            observation=observation, admission=result, inputs=bridge.inputs,
            saved=bridge.saved, resolution_calls=bridge.store.resolve_point.call_count))
        self.assertFalse(result['eligible'])
        self.assertEqual(result['status'], 'missing')
        self.assertEqual(bridge.store.resolve_point.call_count, 0)
        self.assertEqual(bridge.inputs, [])
        self.assertEqual(adapter.authorizations, {})

    def test_missing_value_can_be_entered_then_exact_value_gates_submit(self):
        row = cell(); r = row['result']
        self.assertEqual(r['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(r['completed_transitions'], 2)
        self.assertEqual([v[0] for v in row['inputs']], ['field', 'submit'])
        self.assertEqual([v['predicates']['field_value_matches_task'] for v in r['observations']], [False, True, True])
        self.assertEqual(row['resolution_calls'], 2)
        self.assertEqual(len(row['effect_calls']), 2)
        self.assertTrue(all(v['release_verified'] for v in r['transitions']))

    def test_wrong_value_after_input_cannot_submit(self):
        row = cell('wrong'); r = row['result']
        self.assertEqual((r['outcome'], r['reason']), ('SAFE_YIELD', 'effect_failed'))
        self.assertEqual(r['completed_transitions'], 1)
        self.assertEqual([v[0] for v in row['inputs']], ['field'])
        self.assertEqual(row['effect_calls'], [])

    def test_unknown_value_after_input_cannot_submit(self):
        row = cell('unknown'); r = row['result']
        self.assertEqual((r['outcome'], r['reason']), ('SAFE_YIELD', 'effect_unavailable'))
        self.assertEqual(r['completed_transitions'], 1)
        self.assertEqual([v[0] for v in row['inputs']], ['field'])
        self.assertEqual(row['effect_calls'], [])

    def test_missing_field_cannot_receive_input(self):
        row = cell('missing_field')
        self.assertEqual(row['result']['outcome'], 'SAFE_YIELD')
        self.assertEqual(row['inputs'], [])
        self.assertEqual(row['resolution_calls'], 0)

    def test_missing_submit_after_exact_entry_stops_with_prefix(self):
        row = cell('missing_submit')
        self.assertEqual(row['result']['outcome'], 'SAFE_YIELD')
        self.assertEqual(row['result']['completed_transitions'], 1)
        self.assertEqual([v[0] for v in row['inputs']], ['field'])
        self.assertEqual(row['resolution_calls'], 1)

    def test_already_exact_initial_value_does_not_enter_or_submit(self):
        row = cell('already_exact')
        self.assertEqual(row['result']['outcome'], 'SAFE_YIELD')
        self.assertEqual(row['inputs'], [])


if __name__ == '__main__':
    unittest.main()
