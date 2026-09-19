import unittest
from adapter import adapt_dispatch

class AdapterTests(unittest.TestCase):
    def test_success(self):
        r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True,"partial_effects":[]}})
        self.assertEqual(r["status"],"success"); self.assertTrue(r["task_success"]); self.assertFalse(r["authority_granted"])
    def test_partial(self):
        r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":False,"partial_effects":["A1"]}})
        self.assertEqual(r["status"],"partial"); self.assertFalse(r["task_success"])
    def test_refusal(self):
        r=adapt_dispatch({"status":"backend_unavailable","error":"x"})
        self.assertEqual(r["status"],"refused"); self.assertFalse(r["program_completed"])
    def test_cleanup_failure(self):
        r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True},"cleanup_error":"close"})
        self.assertEqual(r["status"],"cleanup_failed"); self.assertFalse(r["task_success"])

if __name__=="__main__":
    unittest.main()
