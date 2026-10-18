import copy
import json
import unittest
from pathlib import Path

from .audit import validate

HERE = Path(__file__).resolve().parent


class LateObservationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = [json.loads(line) for line in
                   (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_retained_queue_snapshot_interleaving(self):
        self.assertTrue(validate(self.result, self.raw, self.freeze))

    def test_no_executor_authority_is_claimed(self):
        result = copy.deepcopy(self.result)
        result["action_admission"]["input_authority_admitted"] = True
        raw = result["events"]
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            validate(result, raw, self.freeze)

    def test_late_sample_must_follow_action_readiness(self):
        result = copy.deepcopy(self.result)
        events = result["events"]
        i = next(i for i, row in enumerate(events)
                 if row["event"] == "action_admission_evaluated")
        j = next(i for i, row in enumerate(events)
                 if row["event"] == "monitor_received")
        events[i], events[j] = events[j], events[i]
        with self.assertRaisesRegex(ValueError, "ordering mismatch"):
            validate(result, events, self.freeze)

    def test_stale_sample_claim_is_required(self):
        result = copy.deepcopy(self.result)
        result["latest_used_for_action_admission"]["health"] = 70
        with self.assertRaisesRegex(ValueError, "late invalidation claim"):
            validate(result, result["events"], self.freeze)

    def test_executor_submission_is_out_of_scope(self):
        result = copy.deepcopy(self.result)
        result["events"].append({"event": "executor_submit"})
        with self.assertRaisesRegex(ValueError, "must not submit"):
            validate(result, result["events"], self.freeze)


if __name__ == "__main__":
    unittest.main(verbosity=2)
