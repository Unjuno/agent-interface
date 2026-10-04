import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).parent
class SavedTests(unittest.TestCase):
    def test_frozen_stages_and_first_byte_gate_fail(self):
        frozen=json.loads((ROOT/"FREEZE.json").read_text())
        for name,h in frozen["sha256"].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h,name)
        for name in("candidate","auditor"):
            r=json.loads((ROOT/"runs"/name/"receipt.json").read_text())
            self.assertEqual(r["run"]["returncode"],0);self.assertFalse(r["terminal"]["Running"]);self.assertFalse(r["terminal"]["OOMKilled"])
        a=json.loads((ROOT/"runs/auditor/AUDIT.json").read_text())
        self.assertEqual(a["status"],"FAIL_PACKET_BYTE_GATE")
        self.assertEqual(a["native_rows"],18);self.assertEqual(a["synthetic_states"],32);self.assertEqual(a["packets"],200)
        self.assertEqual(a["totals"]["native"]["RAW_CHECKPOINT"]["bytes"],9018)
        self.assertEqual(a["totals"]["native"]["CONSERVATIVE_PROFILE"]["bytes"],7578)
        self.assertEqual(a["totals"]["native"]["RECEIPT_TRUST"]["false_positive_predicates"],27)
        raw=(ROOT/"runs/candidate/evidence/packets.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),a["packets_sha256"])
if __name__=="__main__":unittest.main()
