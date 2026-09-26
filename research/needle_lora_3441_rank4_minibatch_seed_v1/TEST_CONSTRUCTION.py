"""Construction-only checks; does not train or execute a formal allocation."""
import ast,hashlib,json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE/"SOURCE_3807_RUNNER.py"; BASELINE=HERE/"SOURCE_3807_BASELINE.py"; FREEZE=HERE/"FREEZE.json"
class Construction(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.text=SOURCE.read_text(encoding="utf-8");cls.tree=ast.parse(cls.text)
  cls.base=BASELINE.read_text(encoding="utf-8");cls.freeze=json.loads(FREEZE.read_text(encoding="utf-8"))
 def test_issue_and_main_base(self):
  self.assertEqual(self.freeze["issue"],3851)
  self.assertEqual(self.freeze["main_base_commit"],"e56f0e705ce7d5d48ef945e0b71b2ee21328db83")
 def test_exact_3807_cuda_baseline_pinned(self):
  self.assertEqual(self.freeze["predecessors"]["runner_git_blob"],"18b6be0a175df957d838e188de4c7ca826b26af8")
  self.assertIn('rng=torch.Generator(device="cpu").manual_seed(seed+31+rank)',self.base)
  self.assertIn('torch.manual_seed(seed+20+rank)',self.base)
 def test_experiment_source_hashes_match_freeze(self):
  for name,expected in self.freeze["source_sha256"].items():
   self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),expected,name)
 def test_five_seeds_and_two_rng_streams(self):
  self.assertIn("SEEDS=(3451,3452,3453,3454,3455)",self.text)
  self.assertIn('("rank4_legacy_seed35",35)',self.text)
  self.assertIn('("rank4_shared_seed31",31)',self.text)
  self.assertIn("manual_seed(seed+offset)",self.text)
 def test_same_rank4_initial_and_support_order(self):
  self.assertIn("initial=clone_state(template)",self.text)
  self.assertIn("model.load_state_dict(initial)",self.text)
  self.assertIn("manual_seed(seed+30)",self.text)
  self.assertIn("initial_adapter_sha256",self.text)
  self.assertIn("initial_state_exact",self.text)
 def test_no_external_io_or_persistent_checkpoint(self):
  forbidden=("requests.","urllib.","http://","https://","open(","subprocess.")
  self.assertFalse([x for x in forbidden if x in self.text])
  self.assertIn("torch.save(learned,buf)",self.text)
  self.assertIn("io.BytesIO()",self.text)
 def test_cuda_determinism_preflight(self):
  for token in ("torch.cuda.is_available()","CUBLAS_WORKSPACE_CONFIG","torch.__version__","torch.use_deterministic_algorithms(True)","allow_tf32=False","manual_seed_all(seed+24)"):
   self.assertIn(token,self.text)
 def test_balanced_order_and_full_curves(self):
  self.assertIn("if index%2:arm_specs.reverse()",self.text)
  self.assertIn("for count,row in enumerate(order,start=1)",self.text)
  self.assertIn('"curve":curves',self.text)
  self.assertIn('"predicted_b64"',self.text)
 def test_routes_snapshot_and_one_entrypoint(self):
  self.assertIn('"invalid_routes":invalid',self.text)
  self.assertIn("roundtrip_exact",self.text);self.assertIn("rollback_exact",self.text)
  self.assertIn('route_version=0 if role=="A" else VERSION',self.text)
  self.assertEqual(self.text.count('if __name__=="__main__":main()'),1)
  self.assertEqual(self.freeze["D"]["invocationLimit"],1)
if __name__=="__main__":unittest.main(verbosity=2)

