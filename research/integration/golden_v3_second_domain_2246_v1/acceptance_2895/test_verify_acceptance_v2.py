import hashlib, json, tempfile, unittest
from pathlib import Path
from .verify_acceptance_v2 import verify, CASES
class AcceptanceV2Tests(unittest.TestCase):
    def test_raw_event_manifest_is_sufficient_for_event_presence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); files=[]; rows=[]
            for name in ("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure"):
                p=root/name/"events.jsonl"; p.parent.mkdir(); p.write_text('{"event":"x"}\n')
                rel=f"{name}/events.jsonl"; files.append({"path":rel,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
            for case in CASES:
                rows.append({"formal_receipt":{"case":case,"input_ledger":[],"cleanup":{}}})
            summary={"rows":rows,"scorer_matches":True,"formal_receipt_order_ok":True}
            self.assertEqual(verify(summary,{"files":files},root)["decision"],"PASS_FORMAL_2606_ACCEPTANCE")
if __name__=="__main__": unittest.main()
