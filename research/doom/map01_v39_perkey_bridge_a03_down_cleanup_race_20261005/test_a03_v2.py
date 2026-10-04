from __future__ import annotations
import copy,hashlib,json,unittest
from pathlib import Path
import audit_a03_v2 as audit
HERE=Path(__file__).resolve().parent
class ExactRaceAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.freeze,cls.raw,cls.result,cls.scenario,*_=audit.load()
 def test_retained_probe_passes_corrected_raw_scenario_binding(self):
  v=audit.audit(self.raw,self.result,self.freeze,self.scenario)
  self.assertEqual(v["disposition"],"PASS_DOWN_CLEANUP_RACE_REPAIRED")
 def test_bool_integer_alias_in_projected_bracket_is_rejected(self):
  raw=copy.deepcopy(self.raw);up=next(x for x in raw["successor"]["events"] if x.get("event")=="input_release_measurement")
  up["physical_key_measurement"]["bracket"]["grants_input_authority"]=0
  with self.assertRaisesRegex(audit.AuditFailure,"differs by value or type"):
   audit.audit(raw,self.result,self.freeze,self.scenario)
 def test_embedded_scenario_type_alias_is_rejected(self):
  raw=copy.deepcopy(self.raw);raw["scenario"]["step"]=True
  with self.assertRaisesRegex(audit.AuditFailure,"embedded scenario differs"):
   audit.audit(raw,self.result,self.freeze,self.scenario)
if __name__=="__main__":unittest.main(verbosity=2)
