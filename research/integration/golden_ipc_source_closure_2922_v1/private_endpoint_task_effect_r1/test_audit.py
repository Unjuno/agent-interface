import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit import audit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RAW = HERE / "raw"


def load_result():
    return json.loads((RAW / "session_cli_result.json").read_text())


class TaskEffectAuditTests(unittest.TestCase):
    def test_retained_allocation_passes(self):
        self.assertEqual(audit(load_result(), REPO, RAW)["errors"], [])

    def test_rejects_wrong_candidate_disposition(self):
        row = load_result()
        row["disposition"] = "PASS_ANYTHING"
        self.assertFalse(audit(row, REPO, RAW)["checks"]["candidate_pass"])

    def test_rejects_unverified_release(self):
        row = load_result()
        row["executor_terminal"]["release"]["verified"] = False
        self.assertFalse(audit(row, REPO, RAW)["checks"]["release_verified"])

    def test_rejects_evaluator_disagreement(self):
        row = load_result()
        row["independent_evaluation"]["success"] = False
        self.assertFalse(audit(row, REPO, RAW)["checks"]["evaluator_exact_success"])

    def test_rejects_extra_executor_program(self):
        row = load_result()
        row["executor_program_submissions"] = 2
        self.assertFalse(audit(row, REPO, RAW)["checks"]["one_executor_program"])

    def test_rejects_model_or_broker_call(self):
        row = load_result()
        row["model_calls"] = 1
        self.assertFalse(audit(row, REPO, RAW)["checks"]["no_model_or_broker"])

    def test_rejects_changed_saved_output(self):
        row = load_result()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            copied = base / "raw"
            shutil.copytree(RAW, copied)
            shutil.copy2(HERE / "SHA256SUMS", base / "SHA256SUMS")
            (copied / "submitted.txt").write_text("value=wrong")
            self.assertFalse(audit(row, REPO, copied)["checks"]["raw_saved_output_exact"])

    def test_rejects_changed_saved_page_claim(self):
        row = load_result()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            copied = base / "raw"
            shutil.copytree(RAW, copied)
            shutil.copy2(HERE / "SHA256SUMS", base / "SHA256SUMS")
            path = copied / "session/events.jsonl"
            events = [json.loads(line) for line in path.read_text().splitlines()]
            for event in events:
                if event.get("event") == "observation":
                    event["context"] = "fixture page not saved"
            path.write_text("".join(json.dumps(e) + "\n" for e in events))
            self.assertFalse(audit(row, REPO, copied)["checks"]["saved_page_observed"])


if __name__ == "__main__":
    unittest.main()
