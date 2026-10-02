import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import auditor
import candidate

FROZEN_INPUTS = {
    "primary.json": "6b46db2d58a4ecfdd6214bcb9779e6447d34fe448b6dc58706b7579a0a806f0d",
    "selection_trap.json": "e74130346924f40d7b51bcb80731e9c8cb0cb49df1e4d6caf407a8a73481a067",
}


class IndependentAuditTests(unittest.TestCase):
    def read_fixture(self, name):
        raw = (ROOT / "fixtures" / name).read_bytes()
        return raw, json.loads(raw)

    def result_bytes(self, fixture):
        return json.dumps(candidate.evaluate(fixture), sort_keys=True, separators=(",", ":")).encode()

    def test_raw_only_reconstruction_accepts_both_frozen_controls(self):
        for name in FROZEN_INPUTS:
            with self.subTest(name=name):
                raw, fixture = self.read_fixture(name)
                audit = auditor.audit(raw, self.result_bytes(fixture), FROZEN_INPUTS[name])
                self.assertEqual(audit["status"], "PASS_METHOD_ONLY")
                self.assertEqual(audit["errors"], [])

    def test_auditor_rejects_hidden_scheduled_offer(self):
        raw, fixture = self.read_fixture("selection_trap.json")
        del fixture["offers"][-1]
        audit = auditor.audit(json.dumps(fixture, sort_keys=True).encode(), self.result_bytes(json.loads(raw)), FROZEN_INPUTS["selection_trap.json"])
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertIn("INPUT_SHA256_MISMATCH", audit["errors"])

    def test_auditor_rejects_mutated_source_generation(self):
        raw, fixture = self.read_fixture("primary.json")
        fixture["arms"]["adaptive"]["benefit-01"]["source_generation"] = "unfrozen-generation"
        audit = auditor.audit(json.dumps(fixture, sort_keys=True).encode(), self.result_bytes(json.loads(raw)), FROZEN_INPUTS["primary.json"])
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertIn("INPUT_SHA256_MISMATCH", audit["errors"])

    def test_auditor_rejects_mutated_release_label(self):
        raw, fixture = self.read_fixture("primary.json")
        fixture["arms"]["adaptive"]["unsafe-01"]["release"]["verified_neutral"] = True
        audit = auditor.audit(json.dumps(fixture, sort_keys=True).encode(), self.result_bytes(json.loads(raw)), FROZEN_INPUTS["primary.json"])
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertIn("INPUT_SHA256_MISMATCH", audit["errors"])

    def test_auditor_rejects_candidate_summary_mutation(self):
        raw, fixture = self.read_fixture("selection_trap.json")
        result = json.loads(self.result_bytes(fixture))
        result["arms"]["adaptive"]["verified_successes"] = 4
        audit = auditor.audit(raw, json.dumps(result, sort_keys=True).encode(), FROZEN_INPUTS["selection_trap.json"])
        self.assertEqual(audit["status"], "FAIL_AUDIT")
        self.assertIn("CANDIDATE_SUMMARY_MISMATCH", audit["errors"])


if __name__ == "__main__":
    unittest.main()
