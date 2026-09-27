import copy
import json
import unittest
from pathlib import Path

from audit_task_effect import audit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = Path("/out")
BASE = json.loads((OUT / "session_cli_result.json").read_text())
EVENTS = [json.loads(line) for line in (OUT / "session" / "events.jsonl").read_text().splitlines() if line]

class TaskEffectAuditTests(unittest.TestCase):
    def audit_events(self, events, submitted=None):
        return audit(BASE, ROOT, OUT, events_override=events, submitted_bytes_override=submitted)

    def test_retained_one_shot_result_passes(self):
        self.assertEqual(audit(BASE, ROOT, OUT)["errors"], [])

    def test_wrong_ready_token_is_rejected(self):
        events = copy.deepcopy(EVENTS)
        ready = next(e for e in events if e.get("event") == "ready")
        ready["goal"]["token"] = "t000000"
        self.assertIn("ready_token", self.audit_events(events)["errors"])

    def test_unverified_key_release_is_rejected(self):
        events = copy.deepcopy(EVENTS)
        terminal = next(e for e in events if e.get("event") == "terminal")
        terminal["release"]["verified"] = False
        receipt = self.audit_events(events)\n        self.assertIn("release_verified", receipt["errors"])\n        self.assertEqual(receipt["verdict"], "STOP_CHROMIUM_FIXTURE_TASK_EFFECT")

    def test_missing_saved_render_is_rejected(self):
        events = copy.deepcopy(EVENTS)
        for event in events:
            if event.get("event") == "observation":
                event["context"] = {"windows": "about:blank - Chromium"}
        self.assertIn("saved_page_rendered", self.audit_events(events)["errors"])

    def test_wrong_independent_evaluator_value_is_rejected(self):
        events = copy.deepcopy(EVENTS)
        evaluation = next(e for e in events if e.get("event") == "independent_evaluation")
        evaluation["actual"] = {"value": ["wrong"]}
        receipt = self.audit_events(events)\n        self.assertIn("evaluator_exact_value", receipt["errors"])\n        self.assertEqual(receipt["verdict"], "FAIL_CHROMIUM_FIXTURE_TASK_EFFECT")

    def test_second_program_is_rejected(self):
        events = copy.deepcopy(EVENTS)
        submit = next(e for e in events if e.get("event") == "command" and e.get("command", {}).get("op") == "submit")
        events.append(copy.deepcopy(submit))
        errors = self.audit_events(events)["errors"]
        self.assertIn("one_submission", errors)
        self.assertIn("exact_nine_steps", errors)

    def test_mismatched_submitted_bytes_are_rejected(self):
        self.assertIn("submitted_bytes_exact_token",
                      self.audit_events(copy.deepcopy(EVENTS), b"value=t000000")["errors"])

if __name__ == "__main__":
    unittest.main()
