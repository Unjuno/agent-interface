import importlib.util,unittest,torch
spec=importlib.util.spec_from_file_location("study","/work/needle_frontier_study.py");study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

class Construction(unittest.TestCase):
    def test_balanced_unique_support_and_seeded_eval(self):
        xa,ya,xb,yb,sx,sy=study.datasets(67117)
        self.assertEqual(xa.shape,(256,8));self.assertEqual(xb.shape,(256,8));self.assertEqual(sx.shape,(32,8,8))
        self.assertEqual(int(ya.sum()),128);self.assertEqual(int(yb.sum()),128)
        flat=sx.reshape(-1,8);self.assertEqual(len({tuple(x.tolist()) for x in flat}),256)
        self.assertTrue(all(int(batch[:,0].sum())==4 for batch in sx));self.assertTrue(torch.equal(sy,1-sx[:,:,0].long()))

    def test_zero_adapter_is_exact_base(self):
        torch.manual_seed(4);base=study.Net();model=study.Candidate(base,5);x=torch.rand(12,8)
        self.assertEqual(int(torch.count_nonzero(model.b)),0)
        self.assertTrue(torch.equal(base(x),model(x)))

    def test_scope_epoch_guard(self):
        model=study.Candidate(study.Net(),5);x=torch.rand(8)
        self.assertEqual(study.guard(model,x,"B",11)["decision"],"PROPOSE")
        for s,e in [("other",11),("B",10),(None,11)]: self.assertEqual(study.guard(model,x,s,e),{"decision":"YIELD","logits":None})

if __name__=="__main__": unittest.main(verbosity=2)

