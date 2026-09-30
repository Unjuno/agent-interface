"""Construction controls for the post-run audit-schema correction."""
import contextlib,io,unittest
import audit_t0_corrected as audit
def accepted_expected():
 raw=audit.expected_raw()
 raw["runtime"]={"python":"3.11.9","platform":"win32","container":False,"output_file_written":False}
 raw["disposition"]="PASS_CAUSAL_CUT_CONSTRUCTION_SCOPED"
 return raw
class CorrectionTests(unittest.TestCase):
 def errors(self,raw):
  with contextlib.redirect_stdout(io.StringIO()):
   try:audit.audit(raw)
   except SystemExit:pass
  # audit() returns an exit code, while emitted JSON reports detailed integrity.
  with contextlib.redirect_stdout(io.StringIO()) as output:audit.audit(raw)
  import json
  return json.loads(output.getvalue())["errors"]
 def test_complete_expected_schema_matches(self):self.assertEqual(self.errors(accepted_expected()),[])
 def test_missing_runtime_metadata_is_rejected(self):
  raw=accepted_expected();raw.pop("runtime")
  self.assertIn("raw_reconstruction_mismatch",self.errors(raw))
 def test_dropped_cut_row_is_rejected(self):
  raw=accepted_expected();raw["rows"].pop()
  self.assertIn("raw_reconstruction_mismatch",self.errors(raw))
 def test_nonzero_side_effect_is_rejected(self):
  raw=accepted_expected();raw["side_effects"]["actions_dispatched"]=1
  errs=self.errors(raw);self.assertIn("raw_reconstruction_mismatch",errs);self.assertIn("side_effects",errs)
 def test_wrong_candidate_blob_is_rejected(self):
  raw=accepted_expected();raw["source_identity"]["core_git_blob_sha"]="0"*40
  errs=self.errors(raw);self.assertIn("raw_reconstruction_mismatch",errs);self.assertIn("core_source_identity",errs)
if __name__=="__main__":unittest.main()
