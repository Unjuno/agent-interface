import unittest,json
import test_adaptive_acquisition_cost_coverage as coverage
class BrokenDiagnostic(coverage.ModelFailure):
    def __repr__(self):raise RuntimeError('inert repr failure')
class DiagnosticComposition(unittest.TestCase):
    def test_broken_repr_does_not_prevent_failure_finalization(self):
        for invalid in [False,True]:
            def model(_):
                raise BrokenDiagnostic('primary',call_id='known',usage={'input_tokens':-1 if invalid else 10},wait_ns=23,visible_images_submitted=1)
            r=coverage.CostCoverage().route('broken-repr',coarse='model',coarse_fn=model)
            a=r['attempt_ledger'][0]
            self.assertEqual(a['status'],'failed');self.assertIsNotNone(a['completed_ns'])
            self.assertEqual(a['error'],'<exception repr unavailable>')
            self.assertEqual(a['call_id'],'known');self.assertEqual(a['wait_ns'],23);self.assertEqual(a['visible_images_submitted'],1)
            self.assertEqual(a['usage'],None if invalid else {'input_tokens':10})
            self.assertEqual(r['stages']['coarse_model']['status'],'failed');self.assertEqual(r['outcome'],'CALLER_FAILED')
            self.assertIsNone(r['task_effect']);self.assertIsNone(r['accounting']['cost']);json.dumps(r,allow_nan=False)
    def test_invalid_metadata_keeps_primary_diagnostic(self):
        def model(_):raise coverage.ModelFailure('primary',call_id='known',usage={'input_tokens':-1},wait_ns=23,visible_images_submitted=1)
        r=coverage.CostCoverage().route('primary-diagnostic',coarse='model',coarse_fn=model)
        self.assertEqual(r['attempt_ledger'][0]['error'],"ModelFailure('primary')")
        self.assertIn('invalid model failure accounting',r['reason'])
        self.assertEqual(r['attempt_ledger'][0]['wait_ns'],23)
