import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


class SelectionFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(Path("fixtures.json").read_text())
        self.records = candidate.run(self.fixture)

    def run_audit(self, records):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "candidate.jsonl"
            raw.write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in records))
            return audit.audit(self.fixture, raw)

    def test_frozen_world_dispositions(self):
        result = self.run_audit(self.records)
        self.assertEqual(result["status"], "PASS_SELECTION_FEEDBACK_GATE_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["attempt_count"], 192)
        self.assertEqual(result["world_count"], 4)

    def test_auditor_rejects_dropped_attempt(self):
        result = self.run_audit(self.records[:-5])
        self.assertIn("attempt_inventory_mismatch", result["errors"])

    def test_auditor_rejects_relabelled_sealed_attempt(self):
        mutated = [dict(x) for x in self.records]
        target = next(x for x in mutated if x.get("record_type") == "attempt" and x["split"] == "sealed")
        target["split"] = "selection"
        result = self.run_audit(mutated)
        self.assertTrue(any(e.startswith("attempt_inventory_mismatch") or e.startswith("attempt_payload_mismatch") for e in result["errors"]))

    def test_auditor_rejects_changed_stratum(self):
        mutated = [dict(x) for x in self.records]
        target = next(x for x in mutated if x.get("record_type") == "attempt")
        target["stratum"] = "unregistered"
        result = self.run_audit(mutated)
        self.assertTrue(any(e.startswith("attempt_payload_mismatch") for e in result["errors"]))

    def test_auditor_rejects_boolean_integer_substitution(self):
        mutated = [dict(x) for x in self.records]
        target = next(x for x in mutated if x.get("record_type") == "attempt" and x["replicate"] == 1)
        target["replicate"] = True
        result = self.run_audit(mutated)
        self.assertTrue(any(e.startswith("attempt_payload_mismatch") for e in result["errors"]))

    def test_auditor_rejects_non_object_record(self):
        result = self.run_audit(self.records + [["unexpected"]])
        self.assertIn("record_not_object", result["errors"])


if __name__ == "__main__":
    unittest.main()
