"""Read-only saved evidence replay; no runtime dispatch or formal stage."""
import hashlib,json,unittest
from pathlib import Path
from auditor import audit
ROOT=Path(__file__).parent
class SavedReplayTests(unittest.TestCase):
    def test_final_freeze_and_stage_terminals(self):
        final=json.loads((ROOT/"FREEZE_FINAL.json").read_text())
        for f,h in final["sha256"].items():self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),h,f)
        for stage in("candidate","auditor"):
            r=json.loads((ROOT/"runs"/stage/"receipt.json").read_text())
            self.assertEqual(r["run"]["returncode"],0);self.assertFalse(r["terminal"]["Running"])
            self.assertEqual(r["terminal"]["ExitCode"],0);self.assertFalse(r["terminal"]["OOMKilled"])
        self.assertEqual(json.loads((ROOT/"setup/preflight.json").read_text())["returncode"],0)
        self.assertFalse(final["sha256"]["setup/preflight.json"]==json.loads((ROOT/"FREEZE.json").read_text())["sha256"]["setup/preflight.json"])
    def test_actual_contrast_and_whole_terminal(self):
        raw=(ROOT/"runs/candidate/evidence/raw.jsonl").read_bytes()
        rows=[json.loads(s)for s in raw.splitlines()]
        result=audit(rows,json.loads((ROOT/"PLAN.json").read_text()))
        saved=json.loads((ROOT/"runs/auditor/AUDIT.json").read_text())
        self.assertEqual(result["status"],"FAIL_EMPTY_SCOPE_AS_OWNER_RELEASE_EVIDENCE")
        self.assertEqual(result["baseline_crash_still_down"],6)
        self.assertEqual(result["reference"],"SUPPORTED_PREARMED_OWNER_SCOPE_TRANSFER_SCOPED")
        self.assertEqual(saved["raw_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(saved["actor_stream_sha256"]),36)
        for name,h in saved["actor_stream_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/"runs/candidate/evidence"/name).read_bytes()).hexdigest(),h)
        for row in rows:
            self.assertEqual(row["final_emergency"]["emissions"],0)
            self.assertTrue(row["final_emergency"]["receipt"]["verified"])
if __name__=="__main__":unittest.main()
