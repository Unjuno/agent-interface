import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.result = candidate.run(cls.fixture)

    def test_independent_schedule_and_card_oracle(self):
        self.assertEqual(auditor.audit(self.fixture, self.result)["status"], "METHOD_PASS_SCOPED")

    def test_all_five_planted_corruptions_rejected(self):
        self.assertEqual(auditor.corruption_controls(self.fixture, self.result), 5)

    def test_changed_card_never_replays_old_version(self):
        for row in self.result["rows"].values():
            self.assertFalse(any(r["id"] == "C" and r["version"] == 1 for r in row["receipts"]))

    def test_urgent_release_bypasses_every_policy(self):
        for row in self.result["rows"].values():
            self.assertEqual(row["urgent"][0]["start"], 0)
            self.assertEqual(row["urgent"][0]["end"], 1)


if __name__ == "__main__":
    unittest.main()

