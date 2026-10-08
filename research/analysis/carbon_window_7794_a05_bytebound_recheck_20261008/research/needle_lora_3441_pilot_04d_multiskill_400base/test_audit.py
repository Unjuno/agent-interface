"""Construction-only corruption tests for independent row auditor."""
import base64,hashlib,io,json,pathlib,subprocess,sys,tempfile,torch
ROOT=pathlib.Path(__file__).resolve().parent
def data(n,seed,flip0=False,flip1=False):
 g=torch.Generator(device="cpu").manual_seed(seed);x=torch.randn((n,8),generator=g,dtype=torch.float32)
 b0=(x[:,0]>0).long();b1=(x[:,1]>0).long()
 if flip0:b0=1-b0
 if flip1:b1=1-b1
 y=b0*2+b1;return y.tolist(),torch.sha256(torch.tensor([],dtype=torch.uint8)) if False else __import__("hashlib").sha256(x.numpy().tobytes()+y.numpy().tobytes()).hexdigest()
def fixture():
 seeds={"A":(3918,False,False),"B":(3919,True,False),"C":(3920,False,True)}
 rows={};hashes={}
 for arm in ("routed","shared"):
  rows[arm]={}
  for skill,(ds,f0,f1) in seeds.items():
   y,h=data(4096,ds,f0,f1);rows[arm][skill]={"expected":y,"predicted":y.copy(),"n":4096,"correct":4096,"accuracy":1.0};hashes[skill+"_eval"]=h
 snapshots={}
 for name in ("global","B","C"):
  initial={"core.weight":torch.zeros((2,2)),"a":torch.zeros((2,2))}
  learned={"core.weight":torch.zeros((2,2)),"a":torch.ones((2,2))}
  def packed(state):
   b=io.BytesIO();torch.save(state,b);return b.getvalue()
  ib,lb=packed(initial),packed(learned)
  snapshots[name]={"initial_state_b64":base64.b64encode(ib).decode(),"state_b64":base64.b64encode(lb).decode(),"initial_sha256":hashlib.sha256(ib).hexdigest(),"sha256":hashlib.sha256(lb).hexdigest()}
 return {"allocation":"needle-lora-3441-pilot-04d-multiskill-400base","parameters":{"seed":3914,"base_updates":400},"data_sha256":hashes,"measurements":{"row_evidence":rows,"snapshots":snapshots,"routed_accuracy":{"A":1.0,"B":1.0,"C":1.0},"shared_sequential_accuracy":{"A":1.0,"B":1.0,"C":1.0},"adapter_setup_ms":1.0,"update_ms":{"global_B":1.0,"global_C":1.0,"adapter_B":1.0,"adapter_C":1.0}},"checks":{"invalid_routes":{"x":"YIELD"},"base_immutable":True,"all_snapshot_roundtrip_exact":True,"all_rollbacks_exact":True}}
def run(obj):
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".json",delete=False) as f:path=f.name;json.dump(obj,f)
 try:
  p=subprocess.run([sys.executable,"-B",str(ROOT/"audit.py"),path],capture_output=True,text=True,check=True)
  return json.loads(p.stdout)
 finally:pathlib.Path(path).unlink(missing_ok=True)
if __name__=="__main__":
 import unittest
 class AuditorTests(unittest.TestCase):
  def test_valid_rows_recompute(self):
   r=run(fixture());self.assertEqual(r["disposition"],"PASS_MULTI_SKILL_ROUTING_SCOPED");self.assertEqual(r["rows_recomputed"],6*4096)
  def test_corrupt_prediction_is_rejected(self):
   x=fixture();x["measurements"]["row_evidence"]["routed"]["B"]["predicted"][0]=(x["measurements"]["row_evidence"]["routed"]["B"]["predicted"][0]+1)%4
   r=run(x);self.assertFalse(r["integrity"]);self.assertIn("B:routed:metric",r["errors"])
  def test_corrupt_expected_label_is_rejected(self):
   x=fixture();x["measurements"]["row_evidence"]["shared"]["C"]["expected"][0]=(x["measurements"]["row_evidence"]["shared"]["C"]["expected"][0]+1)%4
   r=run(x);self.assertFalse(r["integrity"]);self.assertIn("C:shared:expected_rows",r["errors"])
  def test_corrupt_full_state_digest_is_rejected(self):
   x=fixture();x["measurements"]["snapshots"]["B"]["sha256"]="0"*64
   r=run(x);self.assertFalse(r["integrity"]);self.assertIn("B:learned_sha",r["errors"])
 unittest.main(verbosity=2)
