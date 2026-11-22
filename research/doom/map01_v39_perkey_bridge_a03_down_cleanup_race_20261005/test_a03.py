from __future__ import annotations
import json,unittest
from pathlib import Path
import probe_a03,audit_a03
HERE=Path(__file__).resolve().parent
class DownCleanupOrderingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.freeze=json.loads((HERE/"FREEZE.json").read_text());cls.scenario=json.loads((HERE/"scenario.json").read_text())
  cls.old=probe_a03.load_backend(HERE/"SOURCE/A02/bridge.py","test_bridge_a02")
  cls.new=probe_a03.load_backend(HERE/"bridge_a03.py","test_bridge_a03")
 def test_baseline_reproduces_unscoped_cleanup_and_duplicate_noop(self):
  raw=probe_a03.run_one(self.old,self.scenario);rows=raw["events"]
  self.assertEqual([r["event"] for r in rows],["input_cleanup_unscoped","input_admission","input_release_measurement"])
  self.assertEqual(rows[0]["measurement"]["actuation_id"],self.scenario["actuation_id"])
  self.assertEqual(rows[-1]["physical_key_measurement"]["classification"],"NOOP_ALREADY_UP")
 def test_successor_registers_context_before_drain_and_suppresses_noop(self):
  raw=probe_a03.run_one(self.new,self.scenario);rows=raw["events"]
  self.assertEqual([r["event"] for r in rows],["input_admission","input_release_measurement"])
  self.assertEqual((rows[0]["id"],rows[0]["step"]),(self.scenario["program_id"],self.scenario["step"]))
  self.assertEqual(rows[1]["physical_key_measurement"]["actuation_id"],self.scenario["actuation_id"])
  self.assertEqual(raw["held_keys"],[]);self.assertEqual(raw["physical_keys"],[])
 def test_independent_audit_requires_baseline_failure_and_successor_pass(self):
  import hashlib
  raw={"run_id":self.scenario["run_id"],"scenario":self.scenario,
       "baseline":probe_a03.run_one(self.old,self.scenario),"successor":probe_a03.run_one(self.new,self.scenario)}
  result={"run_id":self.scenario["run_id"],"status":"PENDING_INDEPENDENT_AUDIT",
    "baseline_invocations":1,"successor_invocations":1,"environment":{"in_memory_stub":True,"os_input":False,"gui":False,"game":False,"model_calls":0,
        "python_version":self.freeze["python_version"],"image_id":self.freeze["image_id"],"platform":self.freeze["platform"]}}
  result["raw_sha256"]=hashlib.sha256((json.dumps(raw,sort_keys=True,indent=2)+"\n").encode()).hexdigest()
  verdict=audit_a03.audit(raw,result,self.freeze)
  self.assertEqual(verdict["disposition"],"PASS_DOWN_CLEANUP_RACE_REPAIRED")
if __name__=="__main__":unittest.main(verbosity=2)
