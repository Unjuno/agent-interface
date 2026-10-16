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
    def test_one_invalid_failure_field_preserves_other_available_fields(self):
        for invalid in ['usage','wait_ns','visible_images_submitted']:
            with self.subTest(invalid=invalid):
                def model(_):
                    error=coverage.ModelFailure('mixed metadata',call_id='mixed-call',usage={'input_tokens':10},wait_ns=23,visible_images_submitted=1)
                    setattr(error,invalid,{'input_tokens':10,'cached_input_tokens':11} if invalid=='usage' else -1)
                    raise error
                r=coverage.CostCoverage().route('mixed-error-usage',coarse='model',coarse_fn=model)
                ROWS.append({'case':'mixed_failure_metadata','invalid_field':invalid,'result':r})
                a=r['attempt_ledger'][0]
                self.assertEqual(a['status'],'failed')
                self.assertEqual(a['usage'],None if invalid=='usage' else {'input_tokens':10})
                self.assertEqual(a['wait_ns'],None if invalid=='wait_ns' else 23)
                self.assertEqual(a['visible_images_submitted'],None if invalid=='visible_images_submitted' else 1)
                self.assertEqual(r['outcome'],'CALLER_FAILED')
                self.assertIsNone(r['accounting']['cost'])

    def test_nonstring_failure_usage_keys_preserve_siblings_and_close_stage(self):
        for usage in [{1:0},{1:0,'unknown':0},{None:0},{False:0},{(1,):0},{'unknown':0}]:
            with self.subTest(usage=repr(usage)):
                def model(_):
                    raise coverage.ModelFailure('invalid keys',call_id='known-call',usage=usage,wait_ns=23,visible_images_submitted=1)
                r=coverage.CostCoverage().route('usage-keys',coarse='model',coarse_fn=model)
                ROWS.append({'case':'invalid_usage_keys','input_repr':repr(usage),'result':r})
                a=r['attempt_ledger'][0]
                self.assertEqual(a['status'],'failed')
                self.assertEqual(a['call_id'],'known-call')
                self.assertIsNotNone(a['completed_ns'])
                self.assertIsNone(a['usage'])
                self.assertEqual(a['wait_ns'],23)
                self.assertEqual(a['visible_images_submitted'],1)
                self.assertEqual(r['outcome'],'CALLER_FAILED')
                self.assertIsNone(r['accounting']['cost'])
                self.assertIsNone(r['task_effect'])
                self.assertEqual(r['stages']['coarse_model']['status'],'failed')
                json.dumps(r,allow_nan=False)
