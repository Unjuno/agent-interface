import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class ProtocolTests(unittest.TestCase):
    def test_frozen_three_arm_discriminator(self):
        raw = candidate.run(SPEC)
        self.assertEqual(audit.audit(SPEC, raw), [])
        a, b, c = (raw["arms"][x] for x in SPEC["arms"])
        self.assertEqual(a["local_ticks_total"], 12)
        self.assertEqual(b["local_ticks_total"], 6)
        self.assertEqual(c["local_ticks_total"], 11)
        self.assertEqual((a["verified_by_horizon"], b["verified_by_horizon"], c["verified_by_horizon"]), (5, 3, 5))
        self.assertEqual((a["verification_jobs_enqueued"], b["verification_jobs_enqueued"], c["verification_jobs_enqueued"]), (6, 12, 7))

    def test_all_offers_and_safety_events_are_retained(self):
        raw = candidate.run(SPEC)
        expected_ids = [x["id"] for x in SPEC["tasks"]]
        for arm in raw["arms"].values():
            self.assertEqual(arm["offered_task_ids"], expected_ids)
            self.assertEqual(len(arm["mandatory_safety_events"]), 3)
            self.assertTrue(all(x["served"] for x in arm["mandatory_safety_events"]))

    def test_all_five_corruptions_rejected(self):
        raw = candidate.run(SPEC)
        rejected = {name: audit.audit(SPEC, m) for name, m in audit.corruptions(raw).items()}
        self.assertEqual(set(rejected), {"drop_offer", "route_label", "suppress_verifier_work", "safety_miss", "forge_completion"})
        self.assertTrue(all(errors for errors in rejected.values()))


if __name__ == "__main__":
    unittest.main()
