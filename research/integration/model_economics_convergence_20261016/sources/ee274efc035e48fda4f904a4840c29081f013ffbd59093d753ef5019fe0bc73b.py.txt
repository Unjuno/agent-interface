"""Real grounding/planner/caller composition; only the RPC client is inert."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import adaptive_acquisition_caller_v3 as caller
from research.live_control.integrated_efficiency_app_server_model_v1 import PersistentGroundingModel
from research.live_control.test_integrated_efficiency_app_server_model_v1 import FakeClient, raw, usage

ROWS = []


class Client(FakeClient):
    def __init__(self, status, reported_usage, malformed=False):
        super().__init__([raw(100, 500)], [reported_usage])
        self.status, self.malformed = status, malformed
        self.close_calls = 0

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        if self.status == 'timeout':
            raise TimeoutError('owned inert timeout')
        value = super().wait_turn_completed(thread_id, turn_id, timeout)
        value['turn']['status'] = self.status
        if self.malformed:
            value['turn']['items'][0]['text'] = '{}'
        return value

    def start_turn(self, *args, **kwargs):
        if self.status == 'start_failure':
            raise OSError('owned inert failure before returned turn handle')
        return super().start_turn(*args, **kwargs)

    def close(self):
        self.close_calls += 1


def cell(status='failed', reported_usage=None, publication=None, malformed=False):
    client = Client(status, reported_usage, malformed)
    counts = {'execute': 0, 'verify': 0}
    errors, events, completed = [], [], []
    with tempfile.TemporaryDirectory(prefix='grounding-accounting-') as directory:
        root = Path(directory)
        workspace = root/'workspace'; workspace.mkdir()
        image = root/'image.inert'; image.write_bytes(b'inert; not a captured display')
        model = PersistentGroundingModel(root/'session', workspace, node='unused',
            cli='unused', client=client, path_converter=str, model='inert', effort='low')

        def anchor(_):
            try:
                value = model.call(root/'call', 'inert request', image, 'compiled', workspace)
            except Exception as error:
                errors.append({'type': type(error).__name__,
                    'message': str(error), 'cause': type(error.__cause__).__name__ if error.__cause__ else None,
                    **{k: copy.deepcopy(getattr(error, k, None)) for k in
                       ('call_id', 'usage', 'visible_images_submitted', 'wait_ns')}})
                raise
            completed.append(value)
            return {'call_id': value['call_id'], 'output': {'status': 'target_reference',
                    'target': value['grounding']}, 'usage': value['usage'],
                    'requested_model': value['requested_model'], 'requested_effort': value['requested_effort'],
                    'cost': value['cost'], 'visible_images_submitted': 1, 'wait_ns': value['runner_ns']}

        def execute(_):
            counts['execute'] += 1
            return {'status': 'completed'}

        def verify(_):
            counts['verify'] += 1
            return {'status': 'unavailable'}

        original_write = Path.write_text
        def write(path, *args, **kwargs):
            if path.name == publication:
                raise PermissionError('owned inert publication refusal')
            return original_write(path, *args, **kwargs)

        with patch.object(Path, 'write_text', write):
            result = caller.run({'target': 'inert form', 'route': 'cold',
                'coarse_origin': 'caller_provided', 'provided_coarse': {'status': 'candidate'},
                'cached_target': None, 'local_repair_on': [], 'repair_on': [], 'session_id': 'inert'},
                {'observe_source': lambda _: {}, 'acquire_anchor': lambda _: {},
                 'anchor_model': anchor, 'final_revalidate': lambda _: {'status': 'revalidated'},
                 'execute': execute, 'verify_effect': verify, 'journal': events.append})
        model.close()
        files = {p.name: p.read_text() for p in (root/'call').iterdir() if p.is_file()}
        row = {'status': status, 'reported_usage': reported_usage, 'publication': publication,
            'malformed': malformed, 'result': result, 'errors': errors, 'events': events,
            'completed': completed, 'files': files, 'counts': counts,
            'client_turns': client.turn, 'thread_starts': client.thread_starts,
            'model_calls': model.calls, 'borrowed_close_calls': client.close_calls}
        ROWS.append(copy.deepcopy(row))
        return row


class GroundingFailureAccounting(unittest.TestCase):
    def assert_failed(self, row, known=True):
        r = row['result']; attempt, = r['attempt_ledger']
        self.assertEqual(row['counts'], {'execute': 0, 'verify': 0})
        self.assertEqual((row['client_turns'], row['thread_starts'], row['borrowed_close_calls']), (1, 1, 0))
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertIsNone(r['delivery']); self.assertIsNone(r['task_effect'])
        self.assertEqual(r['input_authority'], 'none')
        self.assertEqual(r['accounting']['attempted_calls'], 1)
        self.assertEqual(r['accounting']['completed_calls'], 0)
        self.assertEqual(attempt['status'], 'failed')
        self.assertEqual(attempt['call_id'], 'turn-1')
        self.assertEqual(attempt['visible_images_submitted'], 1)
        self.assertIs(type(attempt['wait_ns']), int)
        self.assertGreaterEqual(attempt['wait_ns'], 0)
        self.assertEqual(attempt['usage'], {'input_tokens': 100, 'cached_input_tokens': 20,
            'cache_write_input_tokens': 0, 'output_tokens': 20, 'reasoning_output_tokens': 5} if known else None)
        self.assertEqual(r['accounting']['usage_totals']['input_tokens'], 100 if known else None)
        self.assertEqual(r['accounting']['usage_coverage']['input_tokens'], int(known))
        self.assertIsNone(r['accounting']['cost'])
        self.assertEqual(r['stages']['anchor_model']['status'], 'failed')
        self.assertIsNotNone(attempt['completed_ns'])
        json.dumps(r, allow_nan=False)

    def test_failed_and_interrupted_turn_keep_known_accounting(self):
        for status in ('failed', 'interrupted'):
            with self.subTest(status=status):
                self.assert_failed(cell(status, usage(100, 20)))

    def test_unknown_usage_stays_unknown_with_known_turn(self):
        self.assert_failed(cell('failed'), known=False)

    def test_failure_publication_refusal_keeps_known_accounting_and_cause(self):
        row = cell('failed', usage(100, 20), 'failure.json')
        self.assert_failed(row)
        self.assertEqual(row['errors'][0]['cause'], 'PermissionError')
        self.assertNotIn('failure.json', row['files'])

    def test_completed_result_publication_refusal_is_not_unbilled_or_successful(self):
        self.assert_failed(cell('completed', usage(100, 20), 'result.json'))

    def test_invalid_completed_answer_keeps_known_usage_without_execution(self):
        self.assert_failed(cell('completed', usage(100, 20), malformed=True))

    def test_await_timeout_keeps_known_turn_but_not_invented_usage(self):
        self.assert_failed(cell('timeout'), known=False)

    def test_invalid_usage_keeps_other_known_metadata(self):
        self.assert_failed(cell('failed', usage(-1, 0)), known=False)

    def test_start_failure_does_not_invent_turn_or_image_admission(self):
        row = cell('start_failure')
        r = row['result']; attempt, = r['attempt_ledger']
        self.assertEqual(row['client_turns'], 0)
        self.assertEqual(row['counts'], {'execute': 0, 'verify': 0})
        self.assertEqual(r['outcome'], 'CALLER_FAILED')
        self.assertIsNone(attempt['call_id'])
        self.assertIsNone(attempt['visible_images_submitted'])
        self.assertIsNone(attempt['usage'])
        self.assertEqual(r['accounting']['attempted_calls'], 1)
        self.assertEqual(r['accounting']['completed_calls'], 0)
        self.assertEqual(row['borrowed_close_calls'], 0)

    def test_successful_model_then_unknown_effect_does_not_claim_task_success(self):
        row = cell('completed', usage(100, 20))
        r = row['result']
        self.assertEqual(r['outcome'], 'TASK_NOT_VERIFIED')
        self.assertEqual(r['task_effect'], 'unavailable')
        self.assertEqual(r['execution_progress'], {'status': 'completed'})
        self.assertEqual(r['accounting']['usage_totals']['input_tokens'], 100)
        self.assertEqual(r['accounting']['completed_calls'], 1)
        self.assertEqual(row['counts'], {'execute': 1, 'verify': 1})
        self.assertEqual(row['client_turns'], 1)
        self.assertEqual(row['borrowed_close_calls'], 0)


if __name__ == '__main__':
    unittest.main()
