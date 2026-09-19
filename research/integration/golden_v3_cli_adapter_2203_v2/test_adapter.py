import unittest
from adapter import adapt_dispatch,oracle

class AdapterTests(unittest.TestCase):
    def check(self,x):
        self.assertTrue(oracle(x),x)
    def test_success_distinct(self):
        x=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True,"partial_effects":[]}},usage={"input":2},lifecycle=["dispatch","effect","release","cleanup"])
        self.check(x); self.assertEqual(x["status"],"success"); self.assertEqual(x["usage"],{"input":2})
    def test_partial_effects(self):
        x=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":False,"partial_effects":["A1"]}},lifecycle=["dispatch","effect"])
        self.check(x); self.assertEqual(x["status"],"partial"); self.assertEqual(x["partial_effects"],["A1"])
    def test_known_refusal_diagnostic(self):
        x=adapt_dispatch({"status":"backend_unavailable","error":"NO_BACKEND"},lifecycle=["doctor","refusal"])
        self.check(x); self.assertEqual(x["diagnostic"],"NO_BACKEND")
    def test_cleanup_cannot_succeed(self):
        x=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True},"cleanup_error":"close"},lifecycle=["dispatch","effect","release","cleanup"])
        self.check(x); self.assertEqual(x["status"],"cleanup_failed"); self.assertFalse(x["task_success"])
    def test_unknown_status_rejects(self):
        x=adapt_dispatch({"status":"mystery","error":"M"},lifecycle=["dispatch"])
        self.check(x); self.assertEqual(x["adapter_error"],"UNKNOWN_STATUS"); self.assertEqual(x["lifecycle"],[])
    def test_missing_status_rejects(self):
        x=adapt_dispatch({},lifecycle=["dispatch"])
        self.check(x); self.assertEqual(x["adapter_error"],"UNKNOWN_STATUS")
    def test_unknown_lifecycle_rejects(self):
        x=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True}},lifecycle=["dispatch","bogus"])
        self.check(x); self.assertEqual(x["adapter_error"],"UNKNOWN_LIFECYCLE"); self.assertEqual(x["lifecycle"],[])
    def test_authority_true_never_passes(self):
        x=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True}},lifecycle=["dispatch"])
        x["authority_granted"]=True
        self.assertFalse(oracle(x))

if __name__=="__main__": unittest.main()
