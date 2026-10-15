"""Caller -> guarded graph -> real bridge/session, with Fake X transport only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from Xlib import X
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.compiled import _Adapter
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    compile_form_method, EXPECTED_METHOD_CONTRACT,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)

ROWS = []


class CompiledNativeCallerTests(unittest.TestCase):
    def cell(self, fault='healthy', outer='unavailable'):
        fake = FakeX(self)
        initial = Image.frombytes('RGB', (32, 32), fake.raw, 'raw', 'BGRX')
        initial.putpixel((31, 31), (0, 0, 0))
        fake.raw = initial.tobytes('raw', 'BGRX')
        phase = [0]
        emitted = fake.emit
        def emit(display, kind, code):
            emitted(display, kind, code)
            if kind == X.KeyRelease and code == 1:
                phase[0] += 1
                image = Image.frombytes('RGB', (32, 32), fake.raw, 'raw', 'BGRX')
                image.putpixel((31, 31), (phase[0], 0, 0))
                fake.raw = image.tobytes('raw', 'BGRX')
        # FakeX's patched transport calls its original bound method; replace
        # that transport callback, keeping bridge/backend/session untouched.
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='compiled-native-caller-') as td, patch(
                'runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
            bridge = NativeHandleBridge(None, {'app': 20}, 'app', Path(td) / 'bridge', process_identity=True)
            built, outer_checks, core_effects, receipts = [], [], [], []
            try:
                source = bridge.observe()
                offsets = {alias: bridge.mint(alias, source['sequence'], point,
                    region_size=[12, 12]) for alias, point in
                    [('final_field', [8, 8]), ('final_submit', [24, 8])]}
                selected = {'id': 'final', 'field': 'final_field', 'submit': 'final_submit'}
                def perceive(native, image):
                    n = image.getpixel((31, 31))[0]
                    value = n > 0
                    if n and fault == 'wrong': value = False
                    if n and fault == 'unknown': value = 'unknown'
                    return dict(field_target_present=True, submit_target_present=True,
                        field_pixels_changed=n > 0, field_value_matches_task=value,
                        submission_pixels_changed=n > 1)
                def verify_core(payload, native, image):
                    core_effects.append(copy.deepcopy(payload))
                    if fault == 'between' and len(core_effects) == 1:
                        fake.generation = 'b' * 64
                    return dict(status='succeeded', evidence_ref=payload['observation']['evidence_ref'])
                holder = {}
                def build(payload):
                    built.append(copy.deepcopy(payload))
                    target = payload['target']
                    interface = compile_form_method(interface_id='fake-native-caller',
                        session_scope=bridge.scope, surface='x11-window-20',
                        field_handle=target['field'], submit_handle=target['submit'],
                        method_contract=EXPECTED_METHOD_CONTRACT)
                    bindings = {action: dict(interaction='keyboard',
                        offset=offsets[alias], tail=[{'op': 'key_chord', 'keys': ['CTRL', 'a']}])
                        for action, alias in [('enter_token', target['field']),
                                              ('submit_form', target['submit'])]}
                    holder['adapter'] = _Adapter(bridge, interface, bindings,
                        perceive, verify_core, lambda: False)
                    if fault == 'before': fake.generation = 'b' * 64
                    if fault == 'during': fake.flip = True
                    return interface
                def callback(name):
                    return lambda payload: getattr(holder['adapter'], name)(payload)
                def verify_outer(payload):
                    outer_checks.append(copy.deepcopy(payload))
                    return dict(status=outer, evidence_ref='synthetic-outer-check')
                def sink(receipt):
                    receipts.append(copy.deepcopy(receipt))
                    if fault == 'sink': raise OSError('owned synthetic sink failure')
                spec = dict(target='synthetic form', route='reuse', coarse_origin='caller_provided',
                    provided_coarse=None, cached_target={'id': 'old', 'field': 'old_field',
                    'submit': 'old_submit'}, repair_on=[], local_repair_on=[], session_id='fake')
                result = run_compiled_interface_in_caller(spec,
                    dict(reuse_revalidate=lambda _: {'status': 'revalidated'},
                        final_revalidate=lambda _: {'status': 'revalidated', 'target': selected},
                        verify_effect=verify_outer), build,
                    {**{name: callback(name) for name in ('observe', 'admit', 'execute', 'verify_effect')},
                     'cancelled': lambda: False}, on_receipt=sink)
                files = {p.relative_to(td).as_posix(): p.read_bytes().hex()
                    for p in Path(td).rglob('*') if p.is_file()}
                terminals = [json.loads(bytes.fromhex(value)) for name, value in files.items()
                    if name.endswith('-terminal.json')]
                row = dict(fault=fault, outer=outer, result=result, built=built,
                    core_effects=core_effects, outer_checks=outer_checks, receipts=receipts,
                    emissions=copy.deepcopy(fake.emissions), down=sorted(fake.down),
                    generation=fake.generation, identity_queries=fake.identity_queries,
                    native_files_hex=files, terminals=terminals,
                    pending_authorizations=len(holder['adapter'].authorizations),
                    review_required=bridge.review_required)
                ROWS.append(row)
                self.assertEqual(row['down'], [])
                self.assertEqual(row['pending_authorizations'], 0)
                self.assertTrue(all(t['release']['verified'] for t in terminals))
                return row
            finally:
                bridge.close()

    def test_final_target_reaches_native_bridge_without_claiming_task_success(self):
        row = self.cell(); r = row['result']
        self.assertEqual(r['outcome'], 'TASK_NOT_VERIFIED')
        self.assertEqual(r['task_effect'], 'unavailable')
        self.assertEqual(r['compiled_execution_receipt']['completed_transitions'], 2)
        self.assertEqual(row['built'][0]['target'], r['selected_target'])
        self.assertEqual(row['emissions'], [(2, 1), (2, 2), (3, 2), (3, 1)] * 2)
        self.assertEqual(row['down'], [])
        self.assertEqual(len(row['outer_checks']), 1)

    def test_failed_outer_effect_retains_native_completion(self):
        row = self.cell(outer='failed')
        self.assertEqual(row['result']['outcome'], 'TASK_NOT_VERIFIED')
        self.assertEqual(row['result']['execution_progress'], {'status': 'completed'})
        self.assertEqual(row['down'], [])

    def test_changed_generation_before_entry_emits_nothing(self):
        row = self.cell('before')
        self.assertEqual(row['emissions'], [])
        self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'], 0)
        self.assertEqual(row['outer_checks'], [])

    def test_generation_change_during_chord_stops_suffix_and_releases(self):
        row = self.cell('during')
        self.assertEqual(row['emissions'], [(2, 1), (3, 1)])
        self.assertEqual(row['down'], [])
        self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'], 0)
        self.assertNotEqual(row['result']['outcome'], 'TASK_SUCCEEDED')
        self.assertEqual(row['outer_checks'], [])

    def test_generation_change_between_actions_preserves_entry_prefix(self):
        row = self.cell('between')
        self.assertEqual(row['emissions'], [(2, 1), (2, 2), (3, 2), (3, 1)])
        self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'], 1)
        self.assertEqual(row['outer_checks'], [])

    def test_wrong_value_prevents_submit(self):
        row = self.cell('wrong')
        self.assertEqual(row['result']['compiled_execution_receipt']['reason'], 'effect_failed')
        self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'], 1)
        self.assertEqual(len(row['emissions']), 4)
        self.assertEqual(row['outer_checks'], [])

    def test_unknown_value_prevents_submit(self):
        row = self.cell('unknown')
        self.assertEqual(row['result']['compiled_execution_receipt']['reason'], 'effect_unavailable')
        self.assertEqual(len(row['emissions']), 4)
        self.assertEqual(row['outer_checks'], [])

    def test_sink_failure_preserves_native_completion(self):
        row = self.cell('sink'); r = row['result']
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertEqual(r['execution_progress'], {'status': 'completed'})
        self.assertEqual(r['compiled_execution_receipt'], row['receipts'][0])
        self.assertEqual(row['outer_checks'], [])


if __name__ == '__main__':
    unittest.main()
