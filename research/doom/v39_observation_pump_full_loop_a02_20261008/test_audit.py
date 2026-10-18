import copy
import json
import unittest
from pathlib import Path

from .audit import validate

HERE = Path(__file__).resolve().parent


class FullLoopAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = [json.loads(line) for line in
                   (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_retained_full_loop_evidence(self):
        self.assertTrue(validate(self.result, self.raw, self.freeze))

    def test_future_completion_without_terminal_rejects_extra_renewal(self):
        result = copy.deepcopy(self.result)
        healthy = result["cases"][0]
        healthy["submitted"].append("cover-after-completion")
        with self.assertRaisesRegex(ValueError, "renewal lifecycle"):
            validate(result, self.raw, self.freeze)

    def test_invalidation_before_cancel_is_required(self):
        result = copy.deepcopy(self.result)
        events = result["cases"][1]["events"]
        cancel = next(i for i, row in enumerate(events)
                      if row["event"] == "executor_cancel_write")
        invalid = next(i for i, row in enumerate(events)
                       if row["event"] == "monitor_invalidated")
        events[cancel], events[invalid] = events[invalid], events[cancel]
        raw = [{"case": c["case"], **row}
               for c in result["cases"] for row in c["events"]]
        with self.assertRaisesRegex(ValueError, "order mismatch"):
            validate(result, raw, self.freeze)

    def test_nonempty_release_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][1]["terminal"]["release"]["keys_down"] = ["fire"]
        raw = [{"case": c["case"], **row}
               for c in result["cases"] for row in c["events"]]
        with self.assertRaisesRegex(ValueError, "verify empty release"):
            validate(result, raw, self.freeze)

    def test_renewal_after_future_completion_rejected(self):
        result = copy.deepcopy(self.result)
        events = result["cases"][0]["events"]
        done = max(i for i, row in enumerate(events)
                   if row["event"] == "planner_future_poll" and row["done"])
        events.insert(done + 1, {"event": "cover_renewed", "id": "late"})
        raw = [{"case": c["case"], **row}
               for c in result["cases"] for row in c["events"]]
        with self.assertRaisesRegex(ValueError, "completion did not bound"):
            validate(result, raw, self.freeze)

    def test_missing_pending_observation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][0]["events"] = [
            row for row in result["cases"][0]["events"]
            if not (row["event"] == "monitor_received" and row["sequence"] == 3)]
        raw = [{"case": c["case"], **row}
               for c in result["cases"] for row in c["events"]]
        with self.assertRaisesRegex(ValueError, "delivery mismatch"):
            validate(result, raw, self.freeze)


if __name__ == "__main__":
    unittest.main(verbosity=2)
