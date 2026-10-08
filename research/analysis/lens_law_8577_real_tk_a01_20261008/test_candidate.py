"""Construction tests for the disposable real-Tk route; never write formal outputs."""

import importlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class RealTkCandidateTests(unittest.TestCase):
    def test_laws_check_actual_widget_events_and_abstain_at_unresolved_boundaries(self):
        spec = importlib.util.find_spec("candidate")
        self.assertIsNotNone(spec, "candidate module is not implemented yet")
        candidate = importlib.import_module("candidate")
        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))

        result = candidate.run(fixture)
        rows = {row["id"]: row for row in result["rows"]}

        self.assertEqual("PASS", rows["valid_text"]["status"])
        self.assertEqual("PASS", rows["valid_checked"]["status"])
        self.assertEqual("PASS", rows["idempotent_noop"]["status"])
        self.assertEqual("bravo", rows["duplicate_callback"]["final"]["value"])
        self.assertEqual("Duplicate callback", rows["duplicate_callback"]["raw"]["status_label"])
        self.assertEqual("VIOLATION", rows["duplicate_callback"]["status"])
        self.assertTrue(rows["duplicate_callback"]["baselines"]["final_label_only"])
        self.assertTrue(rows["duplicate_callback"]["baselines"]["replay_consistency"])
        duplicate_calls = [
            event for event in rows["duplicate_callback"]["raw"]["event_log"]
            if event.get("kind") == "key_callback" and event.get("delivery") == 2
        ]
        self.assertEqual(6, len(duplicate_calls))
        self.assertFalse(rows["first_write_wins"]["laws"]["put_put"])
        self.assertEqual("UNKNOWN", rows["stale_epoch"]["status"])
        self.assertEqual("UNKNOWN", rows["delayed_pending"]["status"])
        self.assertEqual("PASS", rows["delayed_completed"]["status"])
        self.assertEqual("UNKNOWN", rows["focus_decoy"]["status"])
        self.assertEqual("NOT_APPLICABLE", rows["non_idempotent"]["status"])

        # These are event-loop/readback assertions, not source-text checks.
        self.assertTrue(any(
            event.get("kind") == "key_queued" and event.get("keysym") == "a"
            for event in rows["valid_text"]["raw"]["event_log"]
        ))
        self.assertTrue(any(
            event.get("kind") == "key_callback" and event.get("effect") == "applied"
            for event in rows["valid_text"]["raw"]["event_log"]
        ))
        self.assertTrue(any(
            event.get("kind") == "checkbutton_command"
            for event in rows["valid_checked"]["raw"]["event_log"]
        ))
        self.assertFalse(any(
            event.get("kind") == "non_idempotent_command"
            for event in rows["non_idempotent"]["raw"]["event_log"]
        ))


if __name__ == "__main__":
    unittest.main()
