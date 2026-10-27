import unittest
from research.live_control.adaptive_acquisition_caller_v3 import run


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


if __name__ == '__main__': unittest.main()
