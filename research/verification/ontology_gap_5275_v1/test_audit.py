"""Mutation controls for the raw-only auditor; only deep-copied raw is altered."""
import base64
import contextlib
import copy
import io
import json
import os
import unittest
from audit_t0 import audit

FROZEN_RAW = json.loads(base64.b64decode(os.environ["AGENT_INTERFACE_FORMAL_RAW_B64"]).decode("utf-8"))

def check(candidate):
    output=io.StringIO()
    with contextlib.redirect_stdout(output):
        code=audit(candidate)
    return code, json.loads(output.getvalue())

class AuditorMutationTests(unittest.TestCase):
    def test_frozen_raw_baseline_is_accepted(self):
        code,result=check(copy.deepcopy(FROZEN_RAW))
        self.assertEqual(code,0)
        self.assertEqual(result["errors"],[])
    def test_rejects_row_prediction_mutation(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["rows"][0]["predicted"]="UNKNOWN_CHECK_REQUIRED"
        self.assertNotEqual(check(raw)[0],0)
    def test_rejects_missing_case(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["rows"].pop()
        self.assertNotEqual(check(raw)[0],0)
    def test_rejects_source_identity_mutation(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["source_identity"]["registry_git_blob_sha"]="0"*40
        self.assertNotEqual(check(raw)[0],0)
    def test_rejects_dispatch_mutation(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["side_effects"]["dispatches"]=1
        self.assertNotEqual(check(raw)[0],0)
    def test_rejects_count_mutation(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["counts"]["mismatches"]=0
        self.assertNotEqual(check(raw)[0],0)
    def test_rejects_scientific_disposition_relabel(self):
        raw=copy.deepcopy(FROZEN_RAW); raw["disposition"]="PASS_DETERMINISTIC_GAP_T0_SCOPED"
        self.assertNotEqual(check(raw)[0],0)

if __name__ == "__main__":
    unittest.main()
