import hashlib,json,pathlib,unittest
ROOT=pathlib.Path(__file__).parent
class EvidenceTests(unittest.TestCase):
    def test_retained_raw_matches_receipt_and_audit_gate(self):
        raw=ROOT/"formal_01/RAW.json"; receipt=json.loads((ROOT/"formal_01/CANDIDATE_RECEIPT.json").read_text())
        audit=json.loads((ROOT/"formal_01/AUDIT.json").read_text())
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),receipt["raw_sha256"])
        self.assertEqual(audit["status"],"PASS_METHOD_SCOPED")
        self.assertEqual(audit["errors"],[])
        self.assertEqual(audit["cases"],8)
        self.assertEqual(len(audit["mutations_rejected"]),4)
if __name__=="__main__":unittest.main()
