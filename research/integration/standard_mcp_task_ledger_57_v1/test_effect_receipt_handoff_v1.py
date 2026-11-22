import asyncio
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import test_recorded_comparison_adapter_v1 as recorded_adapter
from effect_receipt_handoff_v1 import adapt_measured_run
from recorded_comparison_adapter_v1 import build_measured_run
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from comparison_measurement_v1 import validate_matched_block
from ledger import LedgerValidationError
from runtime.cli_v1.mcp_relay import Relay

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

    def _install_public_capture_pair(self):
        png = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9WQAAAAASUVORK5CYII=')
        image_digest = hashlib.sha256(png).hexdigest()
        image_path = self.receipt_root / 'raw' / 'public-capture.png'
        image_path.write_bytes(png)
        self.measured['task_ledger']['raw_refs'].append({
            'path': 'raw/public-capture.png', 'sha256': image_digest})

        captures = []
        for call_id, observation_id, capture_start, capture_end in (
                ('observe-1', '1' * 32, 122, 125),
                ('observe-after', '2' * 32, 172, 174)):
            row = {
                'tool_call_id': call_id,
                'observation_id': observation_id,
                'target_generation': self.receipt['target_generation'],
                'capture_started_ns': capture_start,
                'capture_ended_ns': capture_end,
                'image_sha256': image_digest,
            }
            body = {
                'schema': 'agent-interface/runtime-observation-v1',
                'status': 'returned', 'observation_id': observation_id,
                'side_effect_authority': False, 'input_dispatched': False,
                'target_generation': self.receipt['target_generation'],
                'target_generation_consistency': 'matched',
                'observation': {
                    'capture_started_ns': capture_start,
                    'capture_ended_ns': capture_end,
                    'artifact': {'mime_type': 'image/png',
                                 'bytes': len(png), 'sha256': image_digest},
                },
            }
            event = next(event for event in self.events
                         if event.get('call_id') == call_id)
            event['method'] = 'interface_observe'
            event['result'] = {
                'status': 'returned', 'tool': 'interface_observe',
                'result': {'content': [
                    {'type': 'text', 'text': json.dumps(
                        body, sort_keys=True, separators=(',', ':'))},
                    {'type': 'image', 'mimeType': 'image/png',
                     'data': base64.b64encode(png).decode('ascii')},
                ]},
            }
            captures.append(row)
        self.measurement['local_observations'] = captures
        self.receipt['before_observation'] = captures[0]
        self.receipt['after_observation'] = captures[1]
        self.write_receipt()

    def test_public_win32_capture_pair_joins_action_score_and_owner_horizon(self):
        self._install_public_capture_pair()
        adapted = self.adapt()
        self.assertTrue(adapted['factual_task_success'])
        self.assertTrue(adapted['eligible_task_success'])
        self.assertEqual(adapted['timing_status'], 'within_authority')
        self.assertTrue(adapted['authority_binding']['release_confirmed'])
        self.assertTrue(adapted['authority_binding']['horizon_verified'])

    def test_public_action_id_is_resolved_separately_from_recorder_call_id(self):
        self._install_public_capture_pair()
        dispatch_event = next(event for event in self.events
                              if event.get('method') == 'interface_dispatch')
        public_body = json.loads(
            dispatch_event['result']['result']['content'][0]['text'])
        dispatch_event['call_id'] = 'd' * 32
        self.assertEqual(public_body['call_id'], self.receipt['action_call_id'])
        self.assertNotEqual(dispatch_event['call_id'], public_body['call_id'])
        adapted = self.adapt()
        self.assertEqual(adapted['authority_binding']['action_call_id'],
                         public_body['call_id'])
        self.assertTrue(adapted['eligible_task_success'])

    def test_public_win32_capture_pair_rejects_changed_action_generation(self):
        self._install_public_capture_pair()
        self.receipt['after_observation']['target_generation'] = 'd' * 64
        event = next(event for event in self.events
                     if event.get('call_id') == 'observe-after')
        report = json.loads(event['result']['result']['content'][0]['text'])
        report['target_generation'] = 'd' * 64
        event['result']['result']['content'][0]['text'] = json.dumps(
            report, sort_keys=True, separators=(',', ':'))
        self.write_receipt()
        with self.assertRaisesRegex(
                LedgerValidationError,
                'public capture must bind the exact observation and action generation'):
            self.adapt()

    def test_public_win32_effect_interval_must_fit_between_capture_windows(self):
        self._install_public_capture_pair()
        self.receipt['effect_interval_ns'] = {'lower_ns': 171, 'upper_ns': 173}
        self.write_receipt()
        with self.assertRaisesRegex(
                LedgerValidationError,
                'effect interval must be ordered inside its capture bracket'):
            self.adapt()

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

    def _install_completed_public_action(self, *, expiry_ns=155):
        def replace_public_body(call_id, body):
            event = next(event for event in self.events
                         if event.get('call_id') == call_id)
            event['result']['result']['content'][0]['text'] = json.dumps(
                body, sort_keys=True, separators=(',', ':'))

        owner_event = next(event for event in self.events
                           if event.get('call_id') == 'lookup-results-1')
        owner = json.loads(owner_event['result']['result']['content'][0]['text'])
        action_id = self.receipt['action_call_id']
        operation_id = self.receipt['action_operation_id']
        generation = self.receipt['target_generation']
        owner['cancellation'] = None
        owner['action'] = {
            'operation_id': operation_id,
            'target_generation': generation,
            'status': 'completed',
            'release_confirmed': True,
            'completion_custody': {
                'operation_id': operation_id,
                'target_generation': generation,
                'phase': 'completed',
                'status': 'completed',
                'deadline_ns': expiry_ns,
                'release_confirmed': True,
                'completion_release_receipt': {
                    'verified': True, 'monotonic_ns': 160,
                    'keys_down': [], 'buttons_down': [],
                    'keys_unknown': [], 'buttons_unknown': [],
                    'release_errors': [],
                },
                'completion_readback_outcome': 'verified',
                'completion_readback': {
                    'operation_id': operation_id,
                    'target_generation': generation,
                    'neutral': True,
                    'late_input_horizon_ns': 5,
                    'late_input_horizon_verified': True,
                    'late_input_observation_start_monotonic_ns': 160,
                    'late_input_observation_end_monotonic_ns': 165,
                    'late_input_observation_count': 2,
                    'late_input_max_observed_gap_ns': 5,
                    'late_input_max_sample_gap_ns': 5,
                },
            },
        }
        replace_public_body('lookup-results-1', owner)

        dispatch_event = next(event for event in self.events
                              if event.get('call_id') == action_id)
        dispatch = json.loads(
            dispatch_event['result']['result']['content'][0]['text'])
        dispatch['standard_program'] = {
            'authority': {'expires_at_ns': expiry_ns},
        }
        dispatch_event['result']['result']['content'][0]['text'] = json.dumps(
            dispatch, sort_keys=True, separators=(',', ':'))

        self.receipt['effect_interval_ns'] = {'lower_ns': 170, 'upper_ns': 172}
        self.write_receipt()

    def test_completed_public_action_handoff_uses_verified_completion_custody(self):
        self._install_completed_public_action()
        adapted = adapt_measured_run(
            self.measured, receipt_root=self.receipt_root,
            receipt_path='score.json')
        self.assertEqual(adapted['timing_status'], 'after_release_horizon')
        self.assertTrue(adapted['factual_task_success'])
        self.assertFalse(adapted['eligible_task_success'])
        self.assertEqual(adapted['authority_binding']['action_call_id'],
                         self.receipt['action_call_id'])

    def test_completed_public_action_release_before_expiry_keeps_effect_eligible(self):
        self._install_completed_public_action(expiry_ns=180)
        adapted = adapt_measured_run(
            self.measured, receipt_root=self.receipt_root,
            receipt_path='score.json')
        self.assertEqual(adapted['timing_status'], 'within_authority')
        self.assertTrue(adapted['factual_task_success'])
        self.assertTrue(adapted['eligible_task_success'])

    def test_completed_public_action_rejects_unverified_neutral_horizon(self):
        self._install_completed_public_action()
        owner_event = next(event for event in self.events
                           if event.get('call_id') == 'lookup-results-1')
        owner = json.loads(owner_event['result']['result']['content'][0]['text'])
        owner['action']['completion_custody']['completion_readback'][
            'late_input_horizon_verified'] = False
        owner_event['result']['result']['content'][0]['text'] = json.dumps(
            owner, sort_keys=True, separators=(',', ':'))
        with self.assertRaisesRegex(LedgerValidationError,
                                    'generation-bound neutral horizon'):
            adapt_measured_run(
                self.measured, receipt_root=self.receipt_root,
                receipt_path='score.json')

    def test_recorded_caller_actual_relay_records_capture_pair_and_adapts_effect(self):
        root = self.root / 'caller-composition'
        ticks = iter(range(100, 300, 5))
        recorder_root = root / 'recorder'
        recorder = ProviderAttemptRecorder(recorder_root, clock_ns=lambda: next(ticks))
        call_id, operation_id, generation = 'a' * 32, 'b' * 32, 'c' * 64
        owner_result = {
            'operation_id': operation_id, 'target_generation': generation,
            'phase': 'recovered', 'status': 'recovered', 'deadline_ns': 130,
            'release_confirmed': True, 'late_input_horizon_verified': True,
            'late_input_release_received_ns': 135, 'late_input_horizon_ns': 25,
            'late_input_observation_start_ns': 135,
            'late_input_observation_end_ns': 160,
            'late_input_observation_count': 2,
            'late_input_max_observed_gap_ns': 25,
            'late_input_max_sample_gap_ns': 25,
        }
        owner_public = {
            'call_id': call_id,
            'action': {'operation_id': operation_id,
                       'target_generation': generation, 'status': 'unknown'},
            'cancellation': {
                'operation_id': 'd' * 32, 'action_operation_id': operation_id,
                'target_generation': generation, 'status': 'recovered',
                'release_confirmed': True, 'result': owner_result,
            },
        }

        class FakeMCPResult:
            def __init__(self, body):
                self.body = body

            def model_dump(self, *, mode):
                if mode != 'json':
                    raise AssertionError(f'unexpected MCP serialization mode: {mode}')
                return {'content': [{'type': 'text',
                                     'text': json.dumps(self.body)}]}

        class FakeMCPClient:
            async def call_tool(self, method, arguments):
                if method == 'interface_guarded_observe':
                    sequence = 1 if arguments['capture'] == 'before' else 2
                    body = {'source': {'sequence': sequence}}
                elif method == 'interface_dispatch':
                    body = {'call_id': call_id, 'operation_id': operation_id,
                            'target_generation': generation, 'status': 'unknown',
                            'task_success': None, 'replay_allowed': False}
                elif method == 'interface_results':
                    body = owner_public
                else:
                    raise AssertionError(f'unexpected public method: {method}')
                return FakeMCPResult(body)

        usage = {'status': 'reported', 'input_tokens': 10, 'output_tokens': 2}
        recorder.invoke('attempt-1', b'{"prompt":"fixture"}',
                        lambda: {'status': 'completed', 'usage': usage,
                                 'response_bytes': b'{"plan":"dispatch"}'})
        caller = RecordedPublicMcpCaller(
            Relay(FakeMCPClient()), recorder,
            allowed_methods={'interface_guarded_observe', 'interface_dispatch',
                             'interface_results'})

        async def execute_calls():
            dispatch_recorder_id = 'f' * 32
            before = await caller.call_tool(
                'attempt-1', 'capture-before', 'interface_guarded_observe',
                {'capture': 'before'})
            dispatch = await caller.call_tool(
                'attempt-1', dispatch_recorder_id, 'interface_dispatch',
                {'operation_id': operation_id})
            lookup = await caller.call_tool(
                'attempt-1', 'lookup-results-1', 'interface_results',
                {'call_id': call_id})
            after = await caller.call_tool(
                'attempt-1', 'capture-after', 'interface_guarded_observe',
                {'capture': 'after'})
            return before, dispatch, lookup, after

        before_response, dispatch_response, lookup_response, after_response = (
            asyncio.run(execute_calls()))
        self.assertEqual(
            [(row['id'], row['next_id']) for row in (
                before_response, dispatch_response, lookup_response,
                after_response)],
            [(1, 2), (2, 3), (3, 4), (4, 5)])
        self.assertTrue(all(type(row['sdk_entry_ns']) is int and
                            type(row['sdk_return_ns']) is int
                            for row in (before_response, dispatch_response,
                                        lookup_response, after_response)))
        self.assertEqual(dispatch_response['status'], 'returned')
        self.assertEqual(lookup_response['status'], 'returned')
        state_before = b'fixture-state-before'
        state_after = b'fixture-state-after'
        image_bytes = b'fixture-observation-image'
        image_digest = hashlib.sha256(image_bytes).hexdigest()
        image_path = recorder_root / 'raw' / 'model-image.bin'
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(image_bytes)
        receipt = recorder.reconcile()
        dispatch_event = next(event for event in receipt['events']
                              if event.get('method') == 'interface_dispatch')
        dispatch_body = json.loads(
            dispatch_event['result']['result']['content'][0]['text'])
        self.assertNotEqual(dispatch_event['call_id'], dispatch_body['call_id'])
        image_ref = {'path': 'raw/model-image.bin', 'sha256': image_digest}
        receipt['raw_refs'].append(image_ref)
        metadata = {
            'schema': 'agent-interface/standard-mcp-task-ledger-v1',
            'run_id': 'caller-effect-r01',
            'comparison': {'arm': 'C', 'block': 1, 'order': 3,
                           'task_seed': 'caller-effect-seed'},
            'task': {'task_id': 'caller-effect-task', 'fixture_sha256': 'a' * 64,
                     'scorer_sha256': 'e' * 64},
            'source': {'commit': 'f' * 40, 'route_sha256': '9' * 64},
            'environment_sha256': '8' * 64,
            'model': {'id': 'fixture-model', 'effort': 'low',
                      'request_config_sha256': '7' * 64},
        }
        observations = [
            {'tool_call_id': 'capture-before', 'source_sequence': 1,
             'captured_ns': 112, 'image_sha256': image_digest},
            {'tool_call_id': 'capture-after', 'source_sequence': 2,
             'captured_ns': 142, 'image_sha256': image_digest},
        ]
        measurement = {
            'started_ns': 90, 'ended_ns': 250, 'elapsed_ns': 160,
            'phases': [{'name': 'other', 'started_ns': 90, 'ended_ns': 250,
                        'reason': 'bounded synthetic caller composition'}],
            'model_delivered_images': [{'attempt_id': 'attempt-1',
                                        'sha256': image_digest}],
            'local_observations': observations,
            'native_owner_evidence': {
                'lookup_tool_call_id': 'lookup-results-1',
                'action_call_id': call_id, 'effect_observed_ns': None,
            },
        }
        recorder.record_task_score('fixture-independent-oracle-v1', True, state_after)
        receipt = recorder.reconcile()
        receipt['raw_refs'].append(image_ref)
        self.assertTrue(receipt['complete'])
        self.assertEqual(
            [event.get('method') for event in receipt['events']
             if event['kind'] == 'tool_call'],
            ['interface_guarded_observe', 'interface_dispatch',
             'interface_results', 'interface_guarded_observe'])
        measured = build_measured_run(
            receipt, recorder_root=recorder_root,
            ledger_metadata=metadata, measurement=measurement)
        task_score = next(event for event in measured['task_ledger']['events']
                          if event['kind'] == 'task_score')
        receipt_score = {
            'schema': 'agent-interface/task-effect-score-receipt-v1',
            'task_id': metadata['task']['task_id'],
            'lookup_tool_call_id': 'lookup-results-1',
            'action_call_id': call_id, 'action_operation_id': operation_id,
            'target_generation': generation,
            'scorer_id': task_score['scorer_id'],
            'scorer_sha256': metadata['task']['scorer_sha256'],
            'task_success': task_score['task_success'],
            'state_sha256': task_score['state_sha256'],
            'before_task_success': False,
            'before_state_sha256': hashlib.sha256(state_before).hexdigest(),
            'before_observation': observations[0],
            'after_observation': observations[1],
            'effect_interval_ns': {'lower_ns': 122, 'upper_ns': 123},
        }
        effect_path = recorder_root / 'score.json'
        effect_path.write_text(json.dumps(receipt_score, sort_keys=True,
                                          separators=(',', ':')), encoding='utf-8')
        adapted = adapt_measured_run(
            measured, receipt_root=recorder_root, receipt_path='score.json')
        self.assertEqual(adapted['timing_status'], 'within_authority')
        self.assertTrue(adapted['factual_task_success'])
        self.assertTrue(adapted['eligible_task_success'])
        self.assertEqual(adapted['authority_binding']['action_call_id'], call_id)

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
