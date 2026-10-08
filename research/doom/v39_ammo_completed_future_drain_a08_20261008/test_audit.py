import copy
import json
import unittest
from pathlib import Path
from .audit import validate_result

HERE = Path(__file__).resolve().parent


class CompletedFutureDrainAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
        cls.events = [json.loads(line) for line in (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_baseline(self):
        self.assertTrue(validate_result(self.result, self.events))

    def test_duplicate_case_substitution_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][1]["case"] = result["cases"][0]["case"]
        with self.assertRaisesRegex(ValueError, "case set"):
            validate_result(result, self.events)

    def test_raw_event_divergence_rejected(self):
        events = copy.deepcopy(self.events)
        events[0]["event"] = "tampered"
        with self.assertRaisesRegex(ValueError, "raw event stream"):
            validate_result(self.result, events)

    def test_embedded_event_mutation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][1]["events"][-1]["status"] = "READY_FOR_ACTION_VALIDITY"
        with self.assertRaisesRegex(ValueError, "raw event stream"):
            validate_result(result, self.events)

    def test_ammo_invalidation_reason_mutation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][1]["invalidation_reason"] = "health:below_hard_minimum"
        with self.assertRaisesRegex(ValueError, "case outcome"):
            validate_result(result, self.events)

    def test_final_admission_mutation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][1]["final_admission"]["input_authority_admitted"] = True
        with self.assertRaisesRegex(ValueError, "case outcome"):
            validate_result(result, self.events)

    def test_nonempty_terminal_mutation_rejected(self):
        result = copy.deepcopy(self.result)
        result["cases"][0]["terminal"]["release"]["keys_down"] = ["space"]
        with self.assertRaisesRegex(ValueError, "terminal release"):
            validate_result(result, self.events)


if __name__ == "__main__":
    unittest.main(verbosity=2)
