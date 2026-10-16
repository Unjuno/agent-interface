import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from native_primary_review_v1 import grounding_notice, receipt_summary, review_task, validate_review


class PrimaryReviewTests(unittest.TestCase):
    def test_repair_notice_carries_refusal_and_exact_source_without_changing_cold_notice(self):
        source = {'sequence':37, 'native':{'artifact':{'path':'repair.png'}}}
        row = {'entered':{'status':'refused', 'input_dispatched':False, 'error':'MISSING'},
               'refusal_emissions':0}
        notice = grounding_notice('repair', source, 'decision.json', prior_receipt=row, receipt_file='tasks.json')
        self.assertEqual(notice['source_sequence'], 37)
        self.assertEqual(notice['image'], 'repair.png')
        self.assertEqual(notice['receipt_file'], 'tasks.json')
        self.assertEqual(notice['receipt_summary']['refusal_emissions'], 0)
        self.assertFalse(notice['receipt_summary']['operations']['entered']['input_dispatched'])
        cold = grounding_notice('cold', source, 'decision.json')
        self.assertEqual(set(cold), {'needs_grounding','source_sequence','image','request_file'})
        with self.assertRaises(ValueError):
            grounding_notice('repair', source, 'decision.json', prior_receipt=row)

    def test_notice_preserves_partial_failure_and_release_evidence_without_success_inference(self):
        failed = {'status':'partial', 'error':'interrupted', 'recovery_required':True,
                  'execution':{'program_emissions':2, 'error':'release failed',
                               'releases':[{'verified':False, 'keys_down':['CTRL'], 'buttons_down':[]}],
                               'observations':[{'large':'capture'}]}, 'guard_checks':[{'large':'checks'}]}
        row = {'direct':{'status':'returned', 'result':failed},
               'feedback':{'status':'matched', 'observation':{'large':'image'}}, 'refusal_emissions':0}
        before = json.dumps(row)
        summary = receipt_summary(row)
        result = summary['operations']['direct']
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(result['recovery_required'])
        self.assertEqual(result['error'], 'interrupted')
        self.assertEqual(result['execution']['error'], 'release failed')
        self.assertEqual(result['execution']['releases'], failed['execution']['releases'])
        self.assertEqual(summary['refusal_emissions'], 0)
        self.assertIsNone(summary['task_success'])
        self.assertNotIn('observation', summary['feedback'])
        self.assertNotIn('guard_checks', result)
        self.assertEqual(json.dumps(row), before)

    def test_notice_keeps_refusal_before_repair_and_transport_errors(self):
        row = {'navigation':{'result':{'status':'error', 'error':'not admitted'}},
               'entered':{'status':'refused', 'input_dispatched':False, 'error':'MISSING'},
               'repaired_enter':{'status':'completed'}, 'saved':{'status':'completed'}}
        summary = receipt_summary(row)
        self.assertEqual(summary['operations']['navigation']['transport']['error'], 'not admitted')
        self.assertFalse(summary['operations']['entered']['input_dispatched'])
        self.assertEqual(summary['operations']['entered']['error'], 'MISSING')
        self.assertEqual(summary['operations']['repaired_enter']['status'], 'completed')
        self.assertIsNone(summary['task_success'])

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
