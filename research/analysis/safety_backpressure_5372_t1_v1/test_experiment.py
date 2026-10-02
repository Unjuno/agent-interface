import importlib.util
import json
import unittest
from pathlib import Path

import audit


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("candidate_simulator", HERE / "simulate.py")
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = candidate.all_records()

    def test_16_conditions_and_independent_audit(self):
        self.assertEqual(len([r for r in self.records if r["type"] == "summary"]), 16)
        self.assertEqual(audit.audit(self.records), [])

    def test_safety_deletion_mutation_rejected(self):
        changed = [dict(r) for r in self.records]
        index = next(i for i, r in enumerate(changed) if r["type"] == "safety_done")
        changed.pop(index)
        for row in changed[index:]:
            if row.get("scenario_id") == changed[index - 1].get("scenario_id"):
                row["seq"] -= 1
        self.assertTrue(audit.audit(changed))

    def test_unsafe_stale_effect_mutation_rejected(self):
        changed = [dict(r) for r in self.records]
        target = next(r for r in changed if r["type"] == "verify_done" and r["status"] == "stale")
        target["status"] = "verified"
        target["effect"] = True
        self.assertTrue(audit.audit(changed))

    def test_duplicate_success_mutation_rejected(self):
        changed = [dict(r) for r in self.records]
        target = next(r for r in changed if r["type"] == "verify_done" and r["status"] == "verified")
        duplicate = dict(target)
        duplicate["seq"] = target["seq"] + 1
        changed.insert(changed.index(target) + 1, duplicate)
        sid = target["scenario_id"]
        for row in changed:
            if row.get("scenario_id") == sid and row["seq"] > target["seq"] + 1:
                row["seq"] += 1
        self.assertTrue(audit.audit(changed))


if __name__ == "__main__":
    unittest.main()
