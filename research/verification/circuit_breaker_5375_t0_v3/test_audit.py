"""Raw auditor mutation checks; all changes are deep-copy-only."""
import base64,contextlib,copy,io,json,os,unittest
from audit_t0 import audit
RAW=json.loads(base64.b64decode(os.environ["AGENT_INTERFACE_RAW_B64"]).decode("utf-8"))
def check(raw):
    out=io.StringIO()
    with contextlib.redirect_stdout(out): code=audit(raw)
    return code,json.loads(out.getvalue())
class AuditTests(unittest.TestCase):
    def test_frozen_raw_accepted(self): self.assertEqual(check(copy.deepcopy(RAW))[0],0)
    def test_reject_changed_state(self):
        x=copy.deepcopy(RAW); x["rows"][0]["predicted"]["state"]="OPEN"; self.assertNotEqual(check(x)[0],0)
    def test_reject_missing_row(self):
        x=copy.deepcopy(RAW); x["rows"].pop(); self.assertNotEqual(check(x)[0],0)
    def test_reject_source_mutation(self):
        x=copy.deepcopy(RAW); x["source_identity"]["corpus_git_blob_sha"]="0"*40; self.assertNotEqual(check(x)[0],0)
    def test_reject_authority(self):
        x=copy.deepcopy(RAW); x["side_effects"]["authority_grants"]=1; self.assertNotEqual(check(x)[0],0)
    def test_reject_disposition_relabel(self):
        x=copy.deepcopy(RAW); x["disposition"]="FAIL_CIRCUIT_BOUNDARY"; self.assertNotEqual(check(x)[0],0)
if __name__=="__main__": unittest.main()
