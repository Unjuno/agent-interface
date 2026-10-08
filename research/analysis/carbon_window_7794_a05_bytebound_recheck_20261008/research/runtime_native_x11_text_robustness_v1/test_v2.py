import pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
class V2Static(unittest.TestCase):
    def test_plan_excludes_v1_pooling(self):
        s=(HERE/'PLAN_V2.md').read_text(); self.assertIn('V1 completed sessions are excluded',s)
    def test_batch_orders_fixed(self):
        s=(HERE/'run_batch_v2.py').read_text().replace(' ','')
        self.assertIn("BATCHES={1:[0.8,0.9,1.0,1.1],2:[1.1,1.0,0.9,0.8],3:[0.9,1.1,0.8,1.0],4:[1.0,0.8,1.1,0.9],5:[1.1,0.9,1.0,0.8]}",s)
    def test_semantic_failure_does_not_abort_batch(self):
        s=(HERE/'run_batch_v2.py').read_text(); self.assertIn("complete=all(r['report_exists'] and r['score_exists']",s)
    def test_aggregate_requires_all_batches_and_five_of_five(self):
        s=(HERE/'aggregate_v2.py').read_text(); self.assertIn("incomplete batch",s); self.assertIn("eligible_sessions']==5",s); self.assertIn("exact_sessions']==5",s)
if __name__=='__main__': unittest.main()
