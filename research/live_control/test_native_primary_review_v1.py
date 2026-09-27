import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from native_primary_review_v1 import review_task, validate_review


class PrimaryReviewTests(unittest.TestCase):
    def test_exact_task_source_and_explicit_interpretation(self):
        valid = dict(task_id='task-1', source_sequence=7, outcome='complete', reason='Saved receipt and image agree')
        self.assertEqual(validate_review(valid, 'task-1', 7), valid)
        for change in ({'task_id':'task-2'}, {'source_sequence':8}, {'source_sequence':True},
                       {'outcome':True}, {'reason':''}, {'reason':'x'*2001}, {'extra':1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_review(dict(valid, **change), 'task-1', 7)

    def test_reviewed_complete_returns_but_uncertain_failed_and_malformed_stop(self):
        for outcome in ('complete', 'uncertain', 'failed', 'invalid'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                source = {'sequence':7, 'native':{'artifact':{'path':'retained.png'}}}
                now = time.monotonic_ns()
                row = {'feedback':{'status':'matched'}, 'action_started_ns':now, 'feedback_received_ns':now}
                decision = dict(task_id='task-1', source_sequence=7, outcome=outcome, reason='primary interpretation')
                def respond(_):
                    (out/'task-1-primary-review.json').write_text(json.dumps(decision))
                with patch('native_primary_review_v1.time.sleep', side_effect=respond), contextlib.redirect_stdout(io.StringIO()):
                    if outcome == 'complete':
                        result = review_task(out, 'task-1', source, row)
                        self.assertGreaterEqual(result['action_to_review_ms'], 0)
                    else:
                        with self.assertRaises((RuntimeError, ValueError)):
                            review_task(out, 'task-1', source, row)
                result = json.loads((out/'task-1-primary-review-result.json').read_text())
                self.assertEqual('error' in result, outcome != 'complete')

    def test_timeout_retains_unavailable_result_without_decision(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out = Path(tmp)
            source = {'sequence':1, 'native':{'artifact':{'path':'retained.png'}}}
            with self.assertRaises(TimeoutError):
                review_task(out, 'task-1', source, {'feedback':{}}, timeout=0)
            result = json.loads((out/'task-1-primary-review-result.json').read_text())
            self.assertEqual(result['status'], 'unavailable')
            self.assertNotIn('action_to_review_ms', result)


if __name__ == '__main__':
    unittest.main()
