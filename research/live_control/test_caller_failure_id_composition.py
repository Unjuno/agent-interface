import unittest,json,os,atexit
from pathlib import Path
import test_adaptive_acquisition_cost_coverage as coverage
ROWS=[]
atexit.register(lambda:Path(os.environ['ID_ROWS']).write_text(json.dumps(ROWS,indent=2,allow_nan=False)) if os.environ.get('ID_ROWS') else None)
class FailureIdComposition(unittest.TestCase):
    def test_bad_ids_preserve_sibling_accounting_and_strict_json(self):
        for value in [None,'known','',7,[],{},float('nan')]:
            with self.subTest(value=repr(value)):
                def model(_):raise coverage.ModelFailure('primary',call_id=value,usage={'input_tokens':4},wait_ns=23,visible_images_submitted=1)
                r=coverage.CostCoverage().route('failure-id',coarse='model',coarse_fn=model)
                a=r['attempt_ledger'][0]
                self.assertEqual(a['call_id'],'known' if value=='known' else None)
                self.assertEqual(a['usage'],{'input_tokens':4});self.assertEqual(a['wait_ns'],23);self.assertEqual(a['visible_images_submitted'],1)
                self.assertEqual(a['status'],'failed');self.assertIsNotNone(a['completed_ns']);self.assertEqual(a['error'],"ModelFailure('primary')")
                self.assertEqual(r['stages']['coarse_model']['status'],'failed');self.assertEqual(r['outcome'],'CALLER_FAILED')
                self.assertEqual(r['accounting']['attempted_calls'],1);self.assertEqual(r['accounting']['completed_calls'],0)
                self.assertIsNone(r['task_effect']);self.assertIsNone(r['accounting']['cost']);self.assertEqual(r['input_authority'],'none')
                json.dumps(r,allow_nan=False);ROWS.append({'input_repr':repr(value),'result':r})
