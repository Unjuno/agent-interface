import json
import unittest
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class PriorityFairnessTests(unittest.TestCase):
    def test_independent_replay_and_fixed_denominator(self):
        raw = candidate.run(SPEC)
        self.assertEqual(audit.audit(SPEC, raw), [])
        for arm in SPEC["arms"]:
            self.assertEqual(len(raw["arms"][arm]["offered"]), 24)
            self.assertEqual(raw["arms"][arm]["verified"] + raw["arms"][arm]["unknown"], 24)

    def test_pressure_gate_reduces_retry_births(self):
        raw = candidate.run(SPEC)["arms"]
        self.assertGreater(raw["PRIORITY_ONLY"]["retries_enqueued"], 0)
        self.assertGreater(raw["PRESSURE_PRIORITY"]["retries_suppressed"], 0)
        self.assertLess(raw["PRESSURE_PRIORITY"]["retries_enqueued"], raw["PRIORITY_ONLY"]["retries_enqueued"])
        self.assertLessEqual(raw["PRESSURE_PRIORITY"]["max_backlog"], raw["PRIORITY_ONLY"]["max_backlog"])

    def test_aging_reduces_priority_starvation_and_preserves_safety(self):
        raw = candidate.run(SPEC)["arms"]
        self.assertGreater(raw["PRESSURE_AGING"]["verified_by_class"]["LOW"],
                           raw["PRESSURE_PRIORITY"]["verified_by_class"]["LOW"])
        self.assertTrue(all(len(arm["safety"]) == 4 and all(e["deadline_met"] for e in arm["safety"])
                            for arm in raw.values()))

    def test_all_frozen_corruptions_rejected(self):
        raw = candidate.run(SPEC)
        rejected = {name: audit.audit(SPEC, value) for name, value in audit.corruptions(raw).items()}
        self.assertEqual(set(rejected), {"drop_offer", "forge_suppression", "safety_miss", "freshness_label"})
        self.assertTrue(all(errors for errors in rejected.values()))


if __name__ == "__main__":
    unittest.main()

