import gzip
import hashlib
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).parent

class RetainedT0cTests(unittest.TestCase):
    def test_audit_failure_and_all_control_counts_are_preserved(self):
        a=json.loads((ROOT/"formal_01/AUDIT.json").read_text())
        self.assertEqual(a["status"],"METHOD_FAIL_OR_INCONCLUSIVE")
        self.assertEqual(a["errors"],[])
        self.assertEqual(a["groups"],144)
        self.assertEqual(len(a["primary_reversals"]),16)
        self.assertEqual(a["control_reversal_counts"],{"no_imitation":0,"per_principal":11,"shared_24":0})

    def test_candidate_compressed_stream_is_intact(self):
        with gzip.open(ROOT/"formal_01/RAW.json.gz","rb") as f: digest=hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(digest,"b0784f18cf07160784c97228d63d5be6c18d4211a47708f4c1db4df3573df3d5")
        self.assertEqual((ROOT/"formal_01/runner.exit_code").read_text(),"1\n")

if __name__=="__main__": unittest.main()
