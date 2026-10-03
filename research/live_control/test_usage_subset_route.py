import copy,json,unittest
import test_adaptive_acquisition_cost_coverage as coverage
ROWS=[]
class UsageSubsetRoute(unittest.TestCase):
    def route(self,usage):
        def model(_):
            r=coverage.result({'status':'candidate'},5,'coarse');r['usage']=copy.deepcopy(usage);return r
        r=coverage.CostCoverage().route('usage-subset',coarse='model',coarse_fn=model)
        ROWS.append({'usage':usage,'result':r});return r
    def test_impossible_subsets_preserve_attempt_without_success(self):
        for usage in [{'input_tokens':10,'cached_input_tokens':11}, {'output_tokens':4,'reasoning_output_tokens':5}]:
            with self.subTest(usage=usage):
                r=self.route(usage)
                self.assertEqual(r['outcome'],'CALLER_FAILED')
                self.assertEqual(r['accounting']['attempted_calls'],1)
                self.assertEqual(r['accounting']['completed_calls'],0)
                self.assertIsNone(r['accounting']['cost'])
                self.assertEqual(len(r['attempt_ledger']),1)
                self.assertEqual(r['attempt_ledger'][0]['status'],'failed')
                self.assertIsNone(r['task_effect'])
    def test_partial_and_missing_usage_do_not_invent_totals(self):
        for usage in [None,{}, {'cached_input_tokens':5}, {'reasoning_output_tokens':2}, {'input_tokens':10,'cached_input_tokens':10,'output_tokens':4,'reasoning_output_tokens':4}]:
            with self.subTest(usage=usage):
                r=self.route(usage)
                self.assertEqual(r['outcome'],'TASK_SUCCEEDED')
                self.assertEqual(r['accounting']['attempted_calls'],2)
                self.assertEqual(r['attempt_ledger'][0]['usage'],usage)
                if usage is None or 'input_tokens' not in usage:self.assertIsNone(r['accounting']['usage_totals']['input_tokens'])
                json.dumps(r,allow_nan=False)
    def test_invalid_exception_usage_still_finishes_failed_attempt(self):
        def model(_):
            error=coverage.ModelFailure('inert provider failure',call_id='failed-usage',usage=None)
            error.usage={'input_tokens':10,'cached_input_tokens':11}
            raise error
        r=coverage.CostCoverage().route('invalid-error-usage',coarse='model',coarse_fn=model)
        ROWS.append({'case':'invalid_exception_usage','result':r})
        self.assertEqual(r['outcome'],'CALLER_FAILED')
        self.assertEqual(r['attempt_ledger'][0]['status'],'failed')
        self.assertIsNotNone(r['attempt_ledger'][0]['completed_ns'])
        self.assertIsNone(r['attempt_ledger'][0]['usage'])
        self.assertEqual(r['attempt_ledger'][0]['call_id'],'failed-usage')
        self.assertEqual(r['accounting']['attempted_calls'],1)
        self.assertEqual(r['accounting']['completed_calls'],0)
        self.assertIsNone(r['accounting']['cost'])
