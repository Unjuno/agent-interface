import copy
import json
from pathlib import Path
import unittest

from audit import audit
from candidate import classify

RAW = json.loads((Path(__file__).parent / "predecessor_raw.json").read_text(encoding="utf-8"))
PRIOR = json.loads((Path(__file__).parent / "predecessor_audit.json").read_text(encoding="utf-8"))


class IndependentAuditTests(unittest.TestCase):
    def test_independent_audit_accepts_null_only_on_matching_cleanup(self):
        result = audit(RAW, classify(copy.deepcopy(RAW)), PRIOR)
        self.assertEqual("PASS_AUDIT_OWNER_BOUNDARY_SCOPED", result["status"])
        self.assertTrue(result["checks"]["cleanup_nullable_key_identity"])

    def test_rejects_candidate_pass_when_raw_explicit_up_key_is_null(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[0]["key"] = None
        candidate = classify(copy.deepcopy(RAW))
        result = audit(raw, candidate, PRIOR)
        self.assertEqual("FAIL_AUDIT", result["status"])

    def test_rejects_forged_candidate_check_vector(self):
        candidate = classify(copy.deepcopy(RAW))
        candidate["checks"]["cleanup_null_key_bound_to_keycode_owner_intent"] = False
        self.assertEqual("FAIL_AUDIT", audit(RAW, candidate, PRIOR)["status"])

    def test_rejects_non_boolean_candidate_check_claim(self):
        candidate = classify(copy.deepcopy(RAW))
        candidate["checks"]["cleanup_null_key_bound_to_keycode_owner_intent"] = "yes"
        self.assertEqual("FAIL_AUDIT", audit(RAW, candidate, PRIOR)["status"])

    def test_rejects_cleanup_for_different_keycode(self):
        raw = copy.deepcopy(RAW)
        rows = [row for row in raw["owner_records"] if row.get("event") == "owner_key_release_bracket"]
        rows[1]["keycode"] = 26
        self.assertEqual("FAIL_AUDIT", audit(raw, classify(raw), PRIOR)["status"])

    def test_rejects_unpinned_owner_source_identity(self):
        raw = copy.deepcopy(RAW)
        raw["owner_source_sha256"] = "0" * 64
        self.assertEqual("FAIL_AUDIT", audit(raw, classify(raw), PRIOR)["status"])


if __name__ == "__main__":
    unittest.main()
