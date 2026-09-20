"""Preallocation checks, including the exact index contract; no optimizer steps."""
import ast,hashlib,json,pathlib,runpy,unittest,torch
HERE=pathlib.Path(__file__).resolve().parent
RUNNER=HERE/"SOURCE_RUNNER.py"; BASELINE=HERE/"SOURCE_3807_BASELINE.py"; FREEZE=HERE/"FREEZE.json"
class Construction(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.text=RUNNER.read_text(encoding="utf-8");cls.tree=ast.parse(cls.text)
  cls.baseline=BASELINE.read_text(encoding="utf-8");cls.freeze=json.loads(FREEZE.read_text(encoding="utf-8"))
 def test_issue_main_and_predecessor(self):
  self.assertEqual(self.freeze["issue"],3887)
  self.assertEqual(self.freeze["main_base_commit"],"5bf75b7eaaee19a4f44b751b81d483a18864ec18")
  self.assertEqual(self.freeze["predecessor"]["issue"],3851)
  self.assertIn("source_runner_git_blob",self.freeze["predecessor"])
 def test_official_3807_runner_blob_and_rng(self):
  self.assertEqual(self.freeze["reference_3807_runner_git_blob"],"18b6be0a175df957d838e188de4c7ca826b26af8")
  self.assertIn("manual_seed(seed+31+rank)",self.baseline)
  self.assertIn("manual_seed(seed+30)",self.baseline)
 def test_only_sampler_offsets_differ(self):
  self.assertIn('("rank4_legacy_seed35",35)',self.text)
  self.assertIn('("rank4_shared_seed31",31)',self.text)
  self.assertIn("manual_seed(seed+offset)",self.text)
  self.assertEqual(self.text.count("def one_seed("),1)
 def test_direct_global_id_mapping(self):
  self.assertIn("x[bix]",self.text);self.assertIn("y[bix]",self.text)
  self.assertIn("set(batch_rows).issubset(set(seen_rows))",self.text)
  self.assertNotIn("ids[bix]",self.text)
 def test_first_feedback_row4_maps_without_training(self):
  m=runpy.run_path(str(RUNNER),run_name="construction_only")
  order=torch.randperm(16,generator=torch.Generator(device="cpu").manual_seed(3451+30)).tolist()
  self.assertEqual(order[0],4)
  schedule,_=m["stream_schedule"](order,3451,35)
  self.assertEqual(schedule[0],[4]*32)
  support=torch.arange(16)
  self.assertEqual(support[torch.tensor(schedule[0])].tolist(),[4]*32)
 def test_balanced_order_and_full_curves(self):
  self.assertIn("if index%2:arm_specs.reverse()",self.text)
  self.assertIn("for count,row in enumerate(order,start=1)",self.text)
  self.assertIn('"curve":curves',self.text);self.assertIn('"predicted_b64"',self.text)
 def test_identical_full_rank4_initialization(self):
  self.assertIn("initial=clone_state(template)",self.text)
  self.assertIn("model.load_state_dict(initial)",self.text)
  self.assertIn("initial_state_exact",self.text)
 def test_fail_closed_cuda_gates(self):
  for x in ("CUBLAS_WORKSPACE_CONFIG","torch.__version__","NVIDIA GeForce RTX 3080 Laptop GPU","STOP_GPU_MEMORY_LOW","torch.use_deterministic_algorithms(True)"):
   self.assertIn(x,self.text)
 def test_snapshot_routes_base_and_single_entrypoint(self):
  for x in ("roundtrip_exact","rollback_exact","invalid_routes","base_immutable"):
   self.assertIn(x,self.text)
  self.assertEqual(self.text.count('if __name__=="__main__":main()'),1)
  self.assertEqual(self.freeze["D"]["invocationLimit"],1)
 def test_no_network_or_persistent_checkpoint(self):
  for x in ("requests.","urllib.","subprocess.","http://","https://","open("):
   self.assertNotIn(x,self.text)
if __name__=="__main__":unittest.main(verbosity=2)


