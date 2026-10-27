import unittest
from research.live_control.adaptive_acquisition_caller_v3 import ModelFailure, run


class ModelCompletionClockFailure(unittest.TestCase):
    def test_model_result_survives_timing_failure_before_journaling(self):
        ticks = 0
        calls = {'model': 0, 'execute': 0}
        def clock():
            nonlocal ticks
            ticks += 1
            if ticks == 4:
                raise RuntimeError('completion clock unavailable')
            return ticks * 10
        def model(_):
            calls['model'] += 1
            return {'call_id': 'call-1', 'thread_id': 'thread-1',
                'output': {'status': 'candidate'}, 'usage': {'input_tokens': 7},
                'requested_model': 'inert-model', 'requested_effort': 'low',
                'cost': 0.25, 'visible_images_submitted': 1, 'wait_ns': 20}
        def execute(_):
            calls['execute'] += 1
            return {'status': 'completed'}
        spec = {'target': 'inert', 'route': 'cold', 'coarse_origin': 'model_produced',
                'provided_coarse': None, 'cached_target': None, 'repair_on': [],
                'local_repair_on': [], 'session_id': 'inert'}
        result = run(spec, {'observe_source': lambda _: {}, 'coarse_model': model,
                            'execute': execute}, clock=clock, id_factory=lambda: 'attempt-1')
        self.assertEqual(calls, {'model': 1, 'execute': 0})
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        self.assertEqual(result['attempt_ledger'][0]['call_id'], 'call-1')
        self.assertEqual(result['attempt_ledger'][0]['status'], 'completed')
        self.assertIsNone(result['attempt_ledger'][0]['completed_ns'])
        self.assertEqual(result['accounting']['attempted_calls'], 1)
        self.assertEqual(result['accounting']['completed_calls'], 1)
        self.assertEqual(result['accounting']['usage_totals']['input_tokens'], 7)
        self.assertEqual(result['accounting']['cost'], 0.25)
        self.assertEqual(result['model_call_ledger'][0]['call_id'], 'call-1')
        self.assertIsNone(result['delivery'])


class ModelFailureClockFailure(unittest.TestCase):
    def test_failed_model_metadata_survives_completion_clock_failure(self):
        ticks = 0
        events = []
        def clock():
            nonlocal ticks
            ticks += 1
            if ticks == 4: raise RuntimeError('completion clock unavailable')
            return ticks * 10
        def model(_):
            raise ModelFailure('provider failed', call_id='call-failed',
                thread_id='thread-failed', requested_model='inert-model',
                requested_effort='low', usage={'input_tokens': 7},
                visible_images_submitted=1, wait_ns=20)
        spec = {'target': 'inert', 'route': 'cold', 'coarse_origin': 'model_produced',
                'provided_coarse': None, 'cached_target': None, 'repair_on': [],
                'local_repair_on': [], 'session_id': 'inert'}
        result = run(spec, {'observe_source': lambda _: {}, 'coarse_model': model,
                            'journal': events.append}, clock=clock, id_factory=lambda: 'attempt-1')
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        attempt = result['attempt_ledger'][0]
        self.assertEqual(attempt['status'], 'failed')
        self.assertIsNone(attempt['completed_ns'])
        self.assertEqual(attempt['call_id'], 'call-failed')
        self.assertEqual(attempt['thread_id'], 'thread-failed')
        self.assertEqual(attempt['usage'], {'input_tokens': 7})
        self.assertEqual(attempt['wait_ns'], 20)
        self.assertIn('provider failed', attempt['error'])
        self.assertEqual(result['accounting']['attempted_calls'], 1)
        self.assertEqual(result['accounting']['completed_calls'], 0)
        self.assertEqual(result['accounting']['usage_totals']['input_tokens'], 7)
        self.assertIsNone(result['accounting']['cost'])
        self.assertEqual(result['stages']['coarse_model']['status'], 'failed')
        self.assertEqual(len([e for e in events if e['event'] == 'model_attempt_finished']), 1)
        self.assertEqual(result['input_authority'], 'none')

    def test_malformed_envelope_metadata_survives_clock_failure(self):
        ticks = 0
        def clock():
            nonlocal ticks
            ticks += 1
            if ticks == 4: raise RuntimeError('completion clock unavailable')
            return ticks * 10
        def model(_):
            return {'call_id': 'reported-call', 'thread_id': 'reported-thread',
                'output': {'status': 'candidate'}, 'usage': {'input_tokens': -1},
                'requested_model': 'inert-model', 'requested_effort': 'low',
                'cost': 0.25, 'visible_images_submitted': 1, 'wait_ns': 20}
        spec = {'target': 'inert', 'route': 'cold', 'coarse_origin': 'model_produced',
                'provided_coarse': None, 'cached_target': None, 'repair_on': [],
                'local_repair_on': [], 'session_id': 'inert'}
        result = run(spec, {'observe_source': lambda _: {}, 'coarse_model': model},
                     clock=clock, id_factory=lambda: 'attempt-1')
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        attempt = result['attempt_ledger'][0]
        self.assertEqual(attempt['status'], 'failed')
        self.assertIsNone(attempt['completed_ns'])
        self.assertEqual(attempt['call_id'], 'reported-call')
        self.assertIsNone(attempt['usage'])
        self.assertEqual(attempt['wait_ns'], 20)
        self.assertIsNone(result['accounting']['cost'])
        self.assertIsNone(result['accounting']['usage_totals']['input_tokens'])



if __name__ == '__main__': unittest.main()
