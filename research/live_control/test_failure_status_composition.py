import unittest,json
import test_adaptive_acquisition_cost_coverage as c
class StatusBoundary(unittest.TestCase):
    def test_corrupted_and_valid_status(self):
        for status in [None,7,[],{},"", "UNKNOWN", "DEFERRED_UPSTREAM", "FAILED_UPSTREAM", "FAILED_OUTPUT", "DELETE"]:
            with self.subTest(status=repr(status)):
                def model(_):
                    e=c.ModelFailure("primary",call_id="known",usage={"input_tokens":4},wait_ns=23,visible_images_submitted=1)
                    if status=="DELETE":del e.typed_status
                    else:e.typed_status=status
                    raise e
                r=c.CostCoverage().route("status",coarse="model",coarse_fn=model)
                valid=type(status) is str and status in {"DEFERRED_UPSTREAM","FAILED_UPSTREAM","FAILED_OUTPUT"}
                self.assertEqual(r["outcome"],"TASK_DEFERRED" if status=="DEFERRED_UPSTREAM" else "CALLER_FAILED")
                self.assertEqual(r["reason"],status.lower() if valid else "invalid_model_failure_status")
                a=r["attempt_ledger"][0]
                self.assertEqual(a["status"],"failed");self.assertIsNotNone(a["completed_ns"])
                self.assertEqual(a["call_id"],"known");self.assertEqual(a["usage"],{"input_tokens":4})
                self.assertEqual(a["wait_ns"],23);self.assertEqual(a["visible_images_submitted"],1)
                self.assertEqual(r["input_authority"],"none");self.assertIsNone(r["task_effect"])
                json.dumps(r,allow_nan=False)
