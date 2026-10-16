from __future__ import annotations
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
import audit_a04
HERE=Path(__file__).resolve().parent
SRC=HERE/"SOURCE"
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
class OwnerSourceAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.freeze,cls.raw,cls.result=audit_a04.load_frozen();cls.oracle=staticmethod(audit_a04.load_oracle())
  cls.legacy=load(SRC/"BRIDGE/audit.py","legacy_bridge_audit")
  cls.legacy.HERE=HERE.parents[0]/"map01_v39_perkey_bridge_a02_cleanup_forwarding_20261005"
 def assert_legacy_passes_but_successor_rejects(self,mutate):
  raw=copy.deepcopy(self.raw); result=copy.deepcopy(self.result)
  up=next(e for e in raw["events"] if e.get("event")=="input_release_measurement")
  mutate(raw,up)
  raw_bytes=(json.dumps(raw,sort_keys=True,indent=2)+"\n").encode();result["raw_sha256"]=hashlib.sha256(raw_bytes).hexdigest()
  with tempfile.TemporaryDirectory(prefix="v39-a04-source-audit-") as td:
   out=Path(td);(out/"RAW.json").write_bytes(raw_bytes);(out/"RESULT.json").write_text(json.dumps(result))
   old_out=self.legacy.OUT;self.legacy.OUT=out
   try:
    self.legacy.main();legacy_result=json.loads((out/"AUDIT.json").read_text())
   finally:self.legacy.OUT=old_out
  self.assertEqual(legacy_result["status"],"PASS")
  with self.assertRaises(audit_a04.AuditFailure):
   audit_a04.strict_source_audit(raw,result,self.freeze,self.oracle)
 def test_original_raw_binds_projected_cleanup_to_owner_stream(self):
  v=audit_a04.strict_source_audit(self.raw,self.result,self.freeze,self.oracle)
  self.assertEqual(v["status"],"PASS_OWNER_SOURCE_BOUND_CLEANUP_AUDIT")
  self.assertEqual(v["matching_per_key_release_rows"],1)
 def test_legacy_passes_when_owner_source_row_is_removed(self):
  def mutate(raw,up):
   raw["owner_records"][0]["per_key_release_measurements"]=[]
   up["owner_cleanup_record"]["per_key_release_measurements"]=[]
  self.assert_legacy_passes_but_successor_rejects(mutate)
 def test_legacy_passes_when_source_up_sample_is_invalidated(self):
  def mutate(raw,up):
   for owner in (raw["owner_records"][0],up["owner_cleanup_record"]):
    row=owner["per_key_release_measurements"][0]
    row["classification"]="FAILED";row["bracket"]["status"]="UNAVAILABLE"
    row["pre_sample"]["available"]=False;row["pre_sample"]["error"]="injected"
    row["post_sample"]["down"]=True
  self.assert_legacy_passes_but_successor_rejects(mutate)
 def test_projected_cleanup_must_equal_owner_record_stream(self):
  raw=copy.deepcopy(self.raw);result=copy.deepcopy(self.result)
  raw["owner_records"][0]["verified"]=False
  with self.assertRaises(audit_a04.AuditFailure):
   audit_a04.strict_source_audit(raw,result,self.freeze,self.oracle)
if __name__=="__main__":unittest.main(verbosity=2)
