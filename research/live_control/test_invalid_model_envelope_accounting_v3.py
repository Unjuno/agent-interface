import unittest
from research.live_control.adaptive_acquisition_caller_v3 import run


class InvalidModelEnvelopeAccounting(unittest.TestCase):
    def execute_case(self, invalid_field, invalid_value):
        calls = {'model': 0, 'execute': 0}
        def model(_):
            calls['model'] += 1
            result = {'call_id': 'reported-call', 'thread_id': 'reported-thread',
                      'output': {'status': 'candidate'}, 'usage': {'input_tokens': 7},
                      'requested_model': 'inert-model', 'requested_effort': 'low',
                      'cost': 0.25, 'visible_images_submitted': 1, 'wait_ns': 20}
            result[invalid_field] = invalid_value
            return result
        def execute(_):
            calls['execute'] += 1
            return {'status': 'completed'}
        spec = {'target': 'inert', 'route': 'cold', 'coarse_origin': 'model_produced',
                'provided_coarse': None, 'cached_target': None, 'repair_on': [],
                'local_repair_on': [], 'session_id': 'inert'}
        result = run(spec, {'observe_source': lambda _: {}, 'coarse_model': model,
                            'execute': execute}, clock=lambda: 10, id_factory=lambda: 'attempt')
        self.assertEqual(calls, {'model': 1, 'execute': 0})
        self.assertEqual(result['outcome'], 'CALLER_FAILED')
        self.assertEqual(result['accounting']['attempted_calls'], 1)
        self.assertEqual(result['accounting']['completed_calls'], 0)
        self.assertIsNone(result['accounting']['cost'])
        return result

    def test_bad_usage_does_not_erase_valid_reported_identifiers(self):
        result = self.execute_case('usage', {'input_tokens': -1})
        attempt = result['attempt_ledger'][0]
        self.assertEqual(attempt['call_id'], 'reported-call')
        self.assertEqual(attempt['thread_id'], 'reported-thread')
        self.assertEqual(attempt['requested_model'], 'inert-model')
        self.assertEqual(attempt['wait_ns'], 20)
        self.assertIsNone(attempt['usage'])
        self.assertIsNone(result['accounting']['usage_totals']['input_tokens'])

    def test_bad_identifier_is_not_replaced_or_invented(self):
        result = self.execute_case('call_id', '')
        attempt = result['attempt_ledger'][0]
        self.assertEqual(attempt['status'], 'failed')
        self.assertIsNone(attempt['call_id'])
        self.assertEqual(attempt['thread_id'], 'reported-thread')
        self.assertEqual(attempt['usage'], {'input_tokens': 7})

    def test_bad_image_count_preserves_independently_valid_usage(self):
        result = self.execute_case('visible_images_submitted', True)
        attempt = result['attempt_ledger'][0]
        self.assertEqual(attempt['call_id'], 'reported-call')
        self.assertEqual(attempt['usage'], {'input_tokens': 7})
        self.assertIsNone(attempt['visible_images_submitted'])
        self.assertEqual(result['accounting']['usage_totals']['input_tokens'], 7)


if __name__ == '__main__':
    unittest.main()
