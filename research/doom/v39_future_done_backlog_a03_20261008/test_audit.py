import copy
import json
import unittest
from pathlib import Path

from .audit import validate

HERE = Path(__file__).resolve().parent


class BacklogAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = [json.loads(line) for line in
                   (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_retained_current_main_cases(self):
        self.assertTrue(validate(self.result, self.raw, self.freeze))

    def test_ready_admission_claim_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][0]["result"]["admission"]["status"] = "READY_FOR_FRESH_EXECUTOR_ADMISSION"
        raw = [{"case": c["path"], **e} for c in result["cases"] for e in c["events"]]
        with self.assertRaisesRegex(ValueError, "gained admission"):
            validate(result, raw, self.freeze)

    def test_cancel_must_precede_interrupt_and_terminal(self):
        result = copy.deepcopy(self.result)
        events = result["cases"][1]["events"]
        i = next(i for i, e in enumerate(events) if e["event"] == "executor_cancel_write")
        j = next(i for i, e in enumerate(events) if e["event"] == "terminal_dequeued")
        events[i], events[j] = events[j], events[i]
        raw = [{"case": c["path"], **e} for c in result["cases"] for e in c["events"]]
        with self.assertRaisesRegex(ValueError, "order/status mismatch"):
            validate(result, raw, self.freeze)

    def test_missing_invalidation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][0]["events"] = [
            e for e in result["cases"][0]["events"] if e["event"] != "monitor_invalidated"]
        raw = [{"case": c["path"], **e} for c in result["cases"] for e in c["events"]]
        with self.assertRaisesRegex(ValueError, "missing invalidation"):
            validate(result, raw, self.freeze)

    def test_nonempty_terminal_release_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][0]["result"]["current_terminal"]["release"]["keys_down"] = ["fire"]
        raw = [{"case": c["path"], **e} for c in result["cases"] for e in c["events"]]
        with self.assertRaisesRegex(ValueError, "empty release"):
            validate(result, raw, self.freeze)


if __name__ == "__main__":
    unittest.main(verbosity=2)
