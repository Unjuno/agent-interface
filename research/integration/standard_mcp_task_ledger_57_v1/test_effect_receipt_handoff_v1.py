import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import test_recorded_comparison_adapter_v1 as recorded_adapter
from effect_receipt_handoff_v1 import adapt_measured_run
from recorded_comparison_adapter_v1 import build_measured_run
from comparison_measurement_v1 import validate_matched_block
from ledger import LedgerValidationError

class EffectReceiptHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.measured = recorded_adapter.RecordedComparisonAdapterTests.make_run(
            self.root / 'run', 'C', 3)
        self.events = self.measured['task_ledger']['events']
        self.measurement = self.measured['measurement']
        # Extend fixture with a post-action observation and its retained image.
        obs = {'tool_call_id':'observe-after', 'source_sequence':2,
               'captured_ns':173, 'image_sha256':self.measurement['local_observations'][0]['image_sha256']}
        self.events.insert(-1, {'seq':len(self.events), 'kind':'tool_call',
            'call_id':'observe-after','model_attempt_id':'attempt-1',
            'method':'interface_guarded_observe','started_ns':171,'ended_ns':175,
            'result':{'source':{'sequence':2}},'response_status':'matched'})
        self.measurement['local_observations'].append(obs)
        self.events[-1]["seq"] += 1
        self.score = self.events[-1]
        self.receipt_root = self.root / 'run' / 'recorder'
        action = next(e for e in self.events if e.get('method') == 'interface_dispatch')
        body = json.loads(action['result']['result']['content'][0]['text'])
        self.receipt = {'schema':'agent-interface/task-effect-score-receipt-v1',
            'task_id':'fixture-task','lookup_tool_call_id':'lookup-results-1',
            'action_call_id':'a'*32,'action_operation_id':'b'*32,
            'target_generation':'c'*64,'scorer_id':self.score['scorer_id'],'scorer_sha256':'b'*64,
            'task_success':self.score['task_success'],'state_sha256':self.score['state_sha256'],
            'before_task_success':False,'before_state_sha256':'f'*64,
            'before_observation':self.measurement['local_observations'][0],
            'after_observation':obs,'effect_interval_ns':{'lower_ns':144,'upper_ns':145}}
        self.assertEqual(body['operation_id'], self.receipt['action_operation_id'])
        self.write_receipt()
    def tearDown(self): self.tmp.cleanup()
    def write_receipt(self):
        (self.receipt_root/'score.json').write_text(json.dumps(self.receipt,sort_keys=True,separators=(',',':')),encoding='utf8')
    def adapt(self):
        return adapt_measured_run(
            self.measured, receipt_root=self.receipt_root,
            receipt_path='score.json')

    def _build_from_public_caller_receipt(self):
        receipt = recorded_adapter.ProviderAttemptRecorder(
            self.root / 'run' / 'recorder').reconcile()
        image_ref = self.measured['task_ledger']['raw_refs'][-1]
        if image_ref not in receipt['raw_refs']:
            receipt['raw_refs'].append(image_ref)
        metadata = {key: value for key, value in
                    self.measured['task_ledger'].items()
                    if key not in ('events', 'raw_refs', 'native_owner_binding')}
        measurement = {key: value for key, value in self.measurement.items()
                       if key != 'effect_attribution'}
        measurement['native_owner_evidence'] = {
            'lookup_tool_call_id': 'lookup-results-1',
            'action_call_id': self.receipt['action_call_id'],
            'effect_observed_ns': None,
        }
        observation = dict(self.measurement['local_observations'][0])
        observation['captured_ns'] = 125
        measurement['local_observations'] = [observation]
        measured = build_measured_run(
            receipt, recorder_root=self.root / 'run' / 'recorder',
            ledger_metadata=metadata, measurement=measurement)

        return measured

    def test_recorded_public_caller_receipt_flows_through_both_adapters(self):
        measured = self._build_from_public_caller_receipt()
        summary = recorded_adapter.validate_measured_run(measured)
        self.assertTrue(summary['factual_task_success'])
        self.assertEqual(summary['effect_attribution']['effect_timing'],
                         'unknown')
        self.assertEqual(
            measured['task_ledger']['native_owner_binding']['action_call_id'],
            self.receipt['action_call_id'])

    def test_public_caller_handoff_rejects_single_capture_without_after_capture(self):
        measured = self._build_from_public_caller_receipt()
        with self.assertRaisesRegex(
                LedgerValidationError,
                'capture reference is not a unique retained local observation'):
            adapt_measured_run(
                measured, receipt_root=self.receipt_root,
                receipt_path='score.json')

    def test_public_caller_to_effect_handoff_rejects_wrong_action_identity(self):
        measured = self.measured
        self.receipt['action_call_id'] = 'e' * 32
        self.write_receipt()
        with self.assertRaisesRegex(LedgerValidationError,
                                    'public owner receipt belongs to a different action call'):
            adapt_measured_run(
                measured, receipt_root=self.receipt_root,
                receipt_path='score.json')

    def test_timely_score_joins_same_action_and_raw_receipt(self):
        result=self.adapt()
        self.assertEqual(result['timing_status'],'within_authority')
        self.assertTrue(result['factual_task_success']); self.assertTrue(result['eligible_task_success'])
        self.assertEqual(result['measured_run']['task_ledger']['native_owner_binding']['action_call_id'],'a'*32)
        receipt_ref=next(x for x in result['measured_run']['task_ledger']['raw_refs']
                         if x['sha256']==result['receipt_sha256'])
        retained=self.receipt_root/Path(*receipt_ref['path'].split('/'))
        self.assertEqual(hashlib.sha256(retained.read_bytes()).hexdigest(),
                         receipt_ref['sha256'])
        arm_a=recorded_adapter.RecordedComparisonAdapterTests.make_run(
            self.root/'arm-a','A',1)
        arm_b=recorded_adapter.RecordedComparisonAdapterTests.make_run(
            self.root/'arm-b','B',2)
        block=validate_matched_block([arm_a,arm_b,result['measured_run']])
        self.assertTrue(block['arms']['C']['task_success'])
    def test_post_horizon_is_factual_but_not_eligible(self):
        self.receipt['effect_interval_ns']={'lower_ns':161,'upper_ns':165}; self.write_receipt()
        result=self.adapt(); self.assertTrue(result['factual_task_success']); self.assertFalse(result['eligible_task_success'])
    def test_missing_interval_stays_unknown(self):
        self.receipt['effect_interval_ns']=None; self.write_receipt()
        result=self.adapt(); self.assertEqual(result['timing_status'],'unknown'); self.assertIsNone(result['eligible_task_success'])
    def test_interval_crossing_authority_boundary_stays_unknown(self):
        self.receipt['effect_interval_ns']={'lower_ns':149,'upper_ns':151}; self.write_receipt()
        result=self.adapt(); self.assertEqual(result['timing_status'],'ambiguous_boundary'); self.assertIsNone(result['eligible_task_success'])
    def test_stale_action_identity_fails_closed(self):
        self.receipt['action_operation_id']='e'*32; self.write_receipt()
        with self.assertRaises(LedgerValidationError): self.adapt()
    def test_preexisting_success_cannot_be_attributed_to_action(self):
        self.receipt['before_task_success']=True; self.write_receipt()
        with self.assertRaises(LedgerValidationError): self.adapt()
    def test_outside_capture_bracket_fails_closed(self):
        self.receipt['effect_interval_ns']={'lower_ns':120,'upper_ns':121}; self.write_receipt()
        with self.assertRaises(LedgerValidationError): self.adapt()
    def test_capture_pair_must_bracket_action_and_public_result(self):
        self.receipt['before_observation']=self.measurement['local_observations'][1]
        self.receipt['after_observation']=self.measurement['local_observations'][0]
        self.write_receipt()
        with self.assertRaises(LedgerValidationError): self.adapt()
    def test_missing_native_horizon_fails_closed(self):
        owner=next(e for e in self.events if e.get('call_id')=='lookup-results-1')
        original=owner['result']['result']['content'][0]['text']
        body=json.loads(original); body['cancellation']['result']['late_input_horizon_verified']=False
        owner['result']['result']['content'][0]['text']=json.dumps(body,sort_keys=True,separators=(',',':'))
        with self.assertRaises(LedgerValidationError): self.adapt()

if __name__=='__main__': unittest.main()
