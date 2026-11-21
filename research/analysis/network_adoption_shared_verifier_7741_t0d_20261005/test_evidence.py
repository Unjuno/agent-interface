import gzip
import hashlib
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).parent
PREDECESSOR=ROOT.parent/"network_adoption_shared_verifier_7741_t0c_20261005"

class RetainedT0dProvenanceTests(unittest.TestCase):
    def test_t0c_failure_is_preserved_and_hash_bound(self):
        a=json.loads((PREDECESSOR/"formal_01/AUDIT.json").read_text())
        self.assertEqual(a["status"],"METHOD_FAIL_OR_INCONCLUSIVE")
        self.assertEqual(a["errors"],[])
        self.assertEqual(a["groups"],144)
        self.assertEqual(len(a["primary_reversals"]),16)
        self.assertEqual(a["control_reversal_counts"],{"no_imitation":0,"per_principal":11,"shared_24":0})
        freeze=json.loads((PREDECESSOR/"FREEZE.json").read_text())
        for name,digest in freeze["frozen_sha256"].items():
            self.assertEqual(hashlib.sha256((PREDECESSOR/name).read_bytes()).hexdigest(),digest)

    def test_t0c_candidate_compressed_stream_is_intact(self):
        with gzip.open(PREDECESSOR/"formal_01/RAW.json.gz","rb") as f: digest=hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(digest,"b0784f18cf07160784c97228d63d5be6c18d4211a47708f4c1db4df3573df3d5")
        self.assertEqual((PREDECESSOR/"formal_01/runner.exit_code").read_text(),"1\n")

if __name__=="__main__": unittest.main()
