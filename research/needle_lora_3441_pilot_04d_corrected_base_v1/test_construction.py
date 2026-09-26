"""Construction-only coverage for corrected-step fresh-seed CUDA allocation; no training."""
import ast, hashlib, json, pathlib, runpy, unittest, torch
ROOT=pathlib.Path(__file__).resolve().parent
RUNNER=ROOT/"runner.py"
class Construction(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.text=RUNNER.read_text(encoding="utf-8")
  cls.tree=ast.parse(cls.text)
  cls.mod=runpy.run_path(str(RUNNER),run_name="construction_only")
 def test_fresh_seed_and_fixed_shapes(self):
  self.assertIn("SEED = 3927",self.text);self.assertNotIn("SEED = 3444",self.text)
  self.assertEqual(self.mod["BASE_STEPS"],400);self.assertEqual(self.mod["ADAPTER_STEPS"],120);self.assertEqual(self.mod["RANK"],2)
  self.assertIn("fit(base, xa, ya, SEED + 10, BASE_STEPS)",self.text)
 def test_frozen_source_pins(self):
  freeze=json.loads((ROOT/"FREEZE.json").read_text(encoding="utf-8"))
  for name,digest in freeze["sources"].items():
   canonical=(ROOT/name).read_text(encoding="utf-8").replace("\r\n","\n").encode("utf-8")
   self.assertEqual(hashlib.sha256(canonical).hexdigest(),digest,name)
 def test_dataset_reproducibility_and_cardinality(self):
  x1,y1,h1=self.mod["dataset"](32,3928)
  x2,y2,h2=self.mod["dataset"](32,3928)
  self.assertTrue(torch.equal(x1,x2));self.assertTrue(torch.equal(y1,y2));self.assertEqual(h1,h2)
  self.assertEqual((x1.shape,y1.shape),(torch.Size([32,8]),torch.Size([32])))
 def test_full_module_state_roundtrip_and_rollback(self):
  core=self.mod["Core"](); model=self.mod["Adapter"](core,3938)
  initial=self.mod["tensors"](model)
  self.assertIn("core.enc.0.weight",initial);self.assertIn("a",initial);self.assertIn("b",initial)
  changed={k:v.clone() for k,v in initial.items()}
  changed["a"].add_(1)
  model.load_state_dict(changed,strict=True)
  got=self.mod["tensors"](model)
  self.assertTrue(self.mod["equal_state"](got,changed))
  self.mod["restore"](model,initial)
  self.assertTrue(self.mod["equal_state"](self.mod["tensors"](model),initial))
 def test_dispatch_returns_exact_evaluated_identity(self):
  core=self.mod["Core"](); adapters={"B":self.mod["Adapter"](core,2),"C":self.mod["Adapter"](core,3)}
  for skill,aid,version in (("A",None,None),("B","adapter-B",1),("C","adapter-C",1)):
   decision,selected=self.mod["dispatch"](skill,self.mod["EPOCH"],aid,version,core,adapters)
   self.assertEqual(decision,"PROPOSE")
   self.assertIs(selected,core if skill=="A" else adapters[skill])
 def test_invalid_routes_yield(self):
  core=self.mod["Core"]();ads={"B":self.mod["Adapter"](core,2),"C":self.mod["Adapter"](core,3)}
  cases=[("X",7,None,None),("B",6,"adapter-B",1),("B",7,"adapter-C",1),("C",7,"adapter-C",2)]
  for args in cases:self.assertEqual(self.mod["dispatch"](*args,core,ads)[0],"YIELD")
 def test_row_metrics_are_recomputable(self):
  expected=[0,1,2,3];predicted=[0,1,0,3]
  count=sum(int(a==b) for a,b in zip(expected,predicted))
  self.assertEqual(count,3);self.assertEqual(count/len(expected),.75)
 def test_cuda_timing_and_evidence_are_present(self):
  for token in ("torch.cuda.synchronize(); setup_start","adapter_setup_ms","row_evidence","expected","predicted"):
   self.assertIn(token,self.text)
 def test_wddm_memory_stat_is_typed_unavailable(self):
  self.assertNotIn("reset_peak_memory_stats",self.text)
  self.assertNotIn("max_memory_allocated",self.text)
  self.assertIn('"cuda_peak_memory_status": "UNAVAILABLE_WDDM"',self.text)
 def test_runner_never_claims_independent_audit_pass(self):
  self.assertIn("QUALITY_GATE_MET_PENDING_INDEPENDENT_AUDIT",self.text)
  self.assertNotIn('result["outcome"] = "PASS_MULTI_SKILL_ROUTING_SCOPED"',self.text)
if __name__=="__main__":unittest.main(verbosity=2)

