"""Regression tests for post-run event identity binding in audit-v2."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

import audit_v2


HERE = Path(__file__).resolve().parent
RAW_BYTES = (HERE / "evidence" / "RAW.json").read_bytes()
RAW = json.loads(RAW_BYTES)
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
PROBE = (HERE / "probe.py").read_bytes()
EXPECTATIONS = json.loads((HERE / "evidence" / "AUDIT_EXPECTATIONS_V2.json").read_text(encoding="utf-8"))


def check(raw):
    # Parser and digest reader receive identical, digest-recomputed bytes.
    raw_bytes = json.dumps(raw, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    report = audit_v2.audit(raw_bytes, json.loads(raw_bytes), FREEZE, PROBE, EXPECTATIONS)
    assert report["raw_sha256"] == hashlib.sha256(raw_bytes).hexdigest()
    return report


class AuditIdentityMutationTests(unittest.TestCase):
    def test_unmodified_raw_passes_with_postrun_identity_binding(self):
        result = audit_v2.audit(RAW_BYTES, RAW, FREEZE, PROBE, EXPECTATIONS)
        self.assertEqual(result["decision"], "PASS_METHOD_SCOPED_WITH_POSTRUN_IDENTITY_BINDING")
        self.assertEqual(result["errors"], [])

    def test_recomputed_digest_does_not_hide_wrong_event_keycode(self):
        mutated = copy.deepcopy(RAW)
        edge = mutated["cases"][1]["press"]
        edge["expected_keycode"] = 39
        edge["events"][0]["detail"] = 39
        result = check(mutated)
        self.assertNotEqual(result["raw_sha256"], hashlib.sha256(RAW_BYTES).hexdigest())
        self.assertEqual(result["decision"], "FAIL")
        self.assertTrue(any("frozen identity cardinality" in e for e in result["errors"]))

    def test_recomputed_digest_does_not_hide_wrong_event_window(self):
        mutated = copy.deepcopy(RAW)
        mutated["cases"][1]["press"]["events"][0]["window"] = 2097153
        result = check(mutated)
        self.assertNotEqual(result["raw_sha256"], hashlib.sha256(RAW_BYTES).hexdigest())
        self.assertEqual(result["decision"], "FAIL")
        self.assertTrue(any("frozen identity cardinality" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
