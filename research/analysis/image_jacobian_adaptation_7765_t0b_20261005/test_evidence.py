import hashlib,json,pathlib,unittest
ROOT=pathlib.Path(__file__).parent

class EvidenceTests(unittest.TestCase):
    def test_raw_audit_and_failure_gate_are_consistent(self):
        raw=ROOT/"formal_01/RAW.jsonl"; a=json.loads((ROOT/"formal_01/AUDIT.json").read_text())
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),a["raw_sha256"])
        self.assertEqual(a["status"],"FAIL_NO_GAIN")
        self.assertEqual(a["errors"],[])
        self.assertEqual(a["adaptation_subset_fixed"],185)
        self.assertEqual(a["adaptation_subset_online"],191)
        self.assertEqual(a["safety_violations"],0)
        self.assertTrue(a["all_goals_reached"])

if __name__=="__main__": unittest.main()
