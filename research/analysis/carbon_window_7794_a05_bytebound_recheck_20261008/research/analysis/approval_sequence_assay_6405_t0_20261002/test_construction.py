import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "candidate.py"
FIXTURE = HERE / "fixtures" / "sequence.json"
REQUIRED = ("principal", "target", "recipient", "effect", "scope", "expiry",
            "consequence")


class ApprovalSequenceConstructionTests(unittest.TestCase):
    def candidate_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "rendered.json"
            proc = subprocess.run(
                [sys.executable, str(CANDIDATE), "--input", str(FIXTURE),
                 "--output", str(output)], capture_output=True, text=True,
                check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(output.is_file())
            return json.loads(output.read_text(encoding="utf-8"))

    def test_every_arm_keeps_all_effect_fields_visible(self):
        raw = self.candidate_output()
        requests = {row["request_id"]: row for row in raw["requests"]}
        for arm_name, arm in raw["arms"].items():
            items = arm["items"] if arm_name != "bounded_batch" else [
                item for batch in arm["batches"] for item in batch["items"]]
            for item in items:
                truth = requests[item["request_id"]]
                self.assertEqual(item["visible_fields"], list(REQUIRED))
                self.assertEqual(item["fields"], {key: truth[key] for key in REQUIRED})

    def test_changed_field_arm_marks_only_actual_semantic_differences(self):
        raw = self.candidate_output()
        salience = raw["arms"]["changed_fields"]
        self.assertEqual(salience["items"][2]["highlighted_fields"],
                         ["recipient", "effect"])
        self.assertEqual(salience["items"][4]["highlighted_fields"], ["scope"])

    def test_batch_arm_groups_only_nonconsequential_items_without_merging_scope(self):
        raw = self.candidate_output()
        batches = raw["arms"]["bounded_batch"]["batches"]
        self.assertEqual([[item["request_id"] for item in batch["items"]]
                          for batch in batches], [["r1", "r2"], ["r3"], ["r4"], ["r5"]])
        self.assertTrue(all(item["scope"] and item["expiry"] is not None
                            for batch in batches for item in batch["items"]))
        self.assertTrue(all(batch["decision_controls"] == ["approve", "deny", "cancel"]
                            for batch in batches))

    def test_receipt_for_old_digest_does_not_authorize_changed_effect(self):
        raw = self.candidate_output()
        check = raw["authority_checks"][0]
        self.assertEqual((check["receipt_request_id"], check["attempt_request_id"],
                          check["decision"]),
                         ("r1", "r3", "REFUSE_DIGEST_MISMATCH"))
        self.assertNotEqual(check["receipt_digest"], check["attempt_digest"])

    def test_deny_and_cancel_remain_distinct_available_choices(self):
        raw = self.candidate_output()
        self.assertEqual(raw["responses"], [
            {"request_id": "r3", "choice": "deny"},
            {"request_id": "r5", "choice": "cancel"}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
