"""Independent-auditor corruption tests for Issue #4471; CPU only, no training."""
import base64, hashlib, io, json, pathlib, subprocess, sys, tempfile, unittest, torch
ROOT=pathlib.Path(__file__).resolve().parent
def fixture():
 n=4096
 rows={"routed":{},"shared":{}}
 data_hash={}
 for skill,ds,flip0,flip1 in (("A",3931,False,False),("B",3932,True,False),("C",3933,False,True)):
  g=torch.Generator(device="cpu").manual_seed(ds);x=torch.randn((n,8),generator=g,dtype=torch.float32)
  b0=(x[:,0]>0).long();b1=(x[:,1]>0).long()
  if flip0:b0=1-b0
  if flip1:b1=1-b1
  labels=(b0*2+b1).tolist()
  data_hash[skill+"_eval"]=hashlib.sha256(x.numpy().tobytes()+(b0*2+b1).numpy().tobytes()).hexdigest()
  for arm in rows:
   pred=labels.copy()
   if arm=="shared" and skill=="C": pred=[0]*n
   correct=sum(a==b for a,b in zip(labels,pred))
   rows[arm][skill]={"expected":labels.copy(),"predicted":pred,"n":n,"correct":correct,"accuracy":correct/n}
 routed={s:rows["routed"][s]["accuracy"] for s in ("A","B","C")}
 shared={s:rows["shared"][s]["accuracy"] for s in ("A","B","C")}
 snapshots={}
 for name in ("global","B","C"):
  initial={"core.weight":torch.zeros((2,2)),"a":torch.zeros((2,2))}
  learned={"core.weight":torch.zeros((2,2)),"a":torch.ones((2,2))}
  def pack(state):
   b=io.BytesIO();torch.save(state,b);return b.getvalue()
  ib,lb=pack(initial),pack(learned)
  snapshots[name]={"initial_state_b64":base64.b64encode(ib).decode(),"state_b64":base64.b64encode(lb).decode(),
   "initial_sha256":hashlib.sha256(ib).hexdigest(),"sha256":hashlib.sha256(lb).hexdigest()}
 return {"allocation":"needle-lora-3441-pilot-04d-corrected-base-20260926-01","parameters":{"seed":3927,"base_pretrain_steps":400,"adapter_steps":120},
  "data_sha256":data_hash,"checks":{"invalid_routes":{"unknown":"YIELD","stale":"YIELD"},"base_immutable":True,"all_snapshot_roundtrip_exact":True,"all_rollbacks_exact":True},
  "measurements":{"row_evidence":rows,"routed_accuracy":routed,"shared_sequential_accuracy":shared,
   "adapter_setup_ms":1.0,"update_ms":{"global_B":1.,"global_C":1.,"adapter_B":1.,"adapter_C":1.},"snapshots":snapshots}}}
def run(obj):
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".json",delete=False) as f:
  path=f.name;json.dump(obj,f)
 try:
  p=subprocess.run([sys.executable,"-B",str(ROOT/"audit.py"),path],capture_output=True,text=True,check=True)
  return json.loads(p.stdout)
 finally:pathlib.Path(path).unlink(missing_ok=True)
class AuditorTests(unittest.TestCase):
 def test_valid_with_routing_advantage_passes(self):
  r=run(fixture());self.assertEqual(r["disposition"],"PASS_MULTI_SKILL_ROUTING_SCOPED");self.assertTrue(r["routing_advantage_gate"])
 def test_missing_routing_advantage_holds(self):
  x=fixture(); rows=x["measurements"]["row_evidence"]["shared"]["C"];rows["predicted"]=rows["expected"].copy();rows["correct"]=len(rows["expected"]);rows["accuracy"]=1.
  x["measurements"]["shared_sequential_accuracy"]["C"]=1.
  r=run(x);self.assertEqual(r["disposition"],"HOLD_NO_ROUTING_ADVANTAGE")
 def test_corrupt_metric_is_rejected(self):
  x=fixture();x["measurements"]["row_evidence"]["routed"]["B"]["predicted"][0]=3
  r=run(x);self.assertFalse(r["integrity"]);self.assertIn("B:routed:metric",r["errors"])
 def test_corrupt_state_hash_is_rejected(self):
  x=fixture();x["measurements"]["snapshots"]["B"]["sha256"]="0"*64
  r=run(x);self.assertFalse(r["integrity"]);self.assertIn("B:learned_sha",r["errors"])
 def test_accuracy_miss_fails(self):
  x=fixture();x["measurements"]["row_evidence"]["routed"]["B"]["predicted"]=[0]*32
  row=x["measurements"]["row_evidence"]["routed"]["B"];row["correct"]=sum(a==b for a,b in zip(row["expected"],row["predicted"]));row["accuracy"]=row["correct"]/len(row["expected"])
  x["measurements"]["routed_accuracy"]["B"]=row["accuracy"]
  r=run(x);self.assertEqual(r["disposition"],"FAIL_MULTI_SKILL_INTERFERENCE")
if __name__=="__main__":unittest.main(verbosity=2)
