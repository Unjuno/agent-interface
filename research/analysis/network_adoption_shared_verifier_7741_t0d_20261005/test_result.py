import gzip
import hashlib
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).parent
OUT=ROOT/"formal_01"

class FormalResultTests(unittest.TestCase):
    def test_single_clean_formal_execution_and_frozen_decision(self):
        run=json.loads((OUT/"RUN.json").read_text())
        audit=json.loads((OUT/"AUDIT.json").read_text())
        candidate=json.loads((OUT/"CANDIDATE_RECEIPT.json").read_text())
        auditor=json.loads((OUT/"AUDITOR_RECEIPT.json").read_text())
        self.assertEqual((run["candidate_invocations"],run["auditor_invocations"]),(1,1))
        self.assertEqual((candidate["exit_code"],auditor["exit_code"]),(0,0))
        self.assertEqual(audit["status"],"PASS_METHOD_SCOPED")
        self.assertEqual((audit["groups"],audit["errors"]),(256,[]))
        self.assertEqual(len(audit["primary_reversals"]),32)
        self.assertEqual(audit["control_nonzero_counts"],{"no_imitation_nonzero":0,"shared_24_nonzero":0})
        self.assertEqual(len(audit["differences"]),32)
        for d in audit["differences"]:
            self.assertGreater(d["d_shared"],0)
            self.assertGreaterEqual(d["spillover_did"],3)
            self.assertGreater(d["shared_unfinished_delta"],0)
        for top in ("ring","star"):
            for imitation in (0.08,0.2):
                cell=[d for d in audit["differences"] if d["topology"]==top and d["imitation"]==imitation]
                self.assertEqual(len(cell),8)
                self.assertGreaterEqual(sum(d["spillover_did"]>=3 and d["d_shared"]>0 and d["shared_unfinished_delta"]>0 for d in cell),6)

    def test_compressed_candidate_receipt_matches_inflated_stream(self):
        receipt=json.loads((OUT/"CANDIDATE_RECEIPT.json").read_text())
        digest=hashlib.sha256()
        with gzip.open(OUT/"RAW.json.gz","rb") as source:
            for chunk in iter(lambda:source.read(1024*1024),b""): digest.update(chunk)
        self.assertEqual(digest.hexdigest(),receipt["candidate_stdout_sha256"])

if __name__=="__main__": unittest.main()
