"""Saved first-STOP receipts only; never dispatches input or formal auditor."""
import hashlib
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).parent
class SavedStopTests(unittest.TestCase):
    def test_frozen_method_and_terminal_single_candidate(self):
        freeze=json.loads((ROOT/"FREEZE.json").read_text())
        for name,digest in freeze["sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        receipt=json.loads((ROOT/"runs/candidate/receipt.json").read_text())
        self.assertEqual(receipt["scientific_candidate_invocations"],1)
        self.assertEqual(receipt["run"]["returncode"],1)
        self.assertFalse(receipt["terminal"]["Running"])
        self.assertEqual(receipt["terminal"]["ExitCode"],1)
        self.assertFalse(receipt["terminal"]["OOMKilled"])
        self.assertFalse((ROOT/"runs/auditor").exists())
    def test_saved_method_failure_not_crash_science(self):
        rows=[json.loads(s)for s in (ROOT/"runs/candidate/evidence/raw.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows),1)
        row=rows[0];self.assertEqual(row["id"],"r1-empty_scope-healthy")
        self.assertIn("STOP_SUPERVISOR_RESULT",row["error"])
        self.assertIsNone(row["times"]["kill_sent"])
        path=ROOT/"runs/candidate/evidence/cases"/row["id"]
        owner=[json.loads(s)for s in (path/"owner/stdout.jsonl").read_text().splitlines()]
        helper=[json.loads(s)for s in (path/"supervisor/stdout.jsonl").read_text().splitlines()]
        completed=[p for p in owner if p["event"]=="completed"]
        self.assertEqual(len(completed),1)
        self.assertEqual(completed[0]["result"]["execution"]["completed_ops"],[0,1,2,3])
        self.assertEqual([(p["call"]["kind"],p["call"]["code"])for p in owner if p["event"]=="native"],[("press",74),("release",74)])
        self.assertTrue(completed[0]["result"]["execution"]["releases"][0]["verified"])
        self.assertEqual([p["event"]for p in helper],["registered","error"])
        self.assertIn("STOP_EOF_NOT_ORIGINAL_OWNER_DEATH",helper[-1]["traceback"])
        self.assertEqual(row["final_emergency"]["emissions"],0)
        self.assertTrue(row["final_emergency"]["receipt"]["verified"])
        self.assertEqual(row["xvfb_exit"],0)
if __name__=="__main__":unittest.main()
