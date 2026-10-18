import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import audit_core
import candidate


class A05Tests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))

    def test_candidate_stale_and_refreshed_semantics(self):
        rows = {row["id"]: row for row in candidate.run(self.model)}
        self.assertEqual(rows["pre_interference"]["label"], "UNIVERSALLY_UNIFORM")
        self.assertEqual(rows["stale_then_refreshed"]["stale"]["label"], "UNKNOWN_STALE_CERTIFICATE")
        self.assertEqual(rows["stale_then_refreshed"]["refreshed"]["final"], "001")
        self.assertEqual(rows["journal_gap"]["label"], "UNKNOWN_EVENT_CHAIN")

    def test_independent_auditor_accepts_expected_gap_fixture(self):
        fixture = {"run_id": self.model["run_id"], "cases": [
            {"id":"pre_interference","label":"UNIVERSALLY_UNIFORM","recovery":["restore_a"],"final":"000"},
            {"id":"stale_then_refreshed","stale":{"label":"UNKNOWN_STALE_CERTIFICATE","recovery":None},"refreshed":{"label":"UNIVERSALLY_UNIFORM","recovery":["clear_owned_a"],"final":"001"}},
            {"id":"journal_gap","label":"UNKNOWN_EVENT_CHAIN","recovery":None,"final":None}
        ]}
        self.assertEqual(audit_core.verify(self.model, fixture), [])

    def test_auditor_rejects_three_hostile_mutations(self):
        fixture = {"run_id": self.model["run_id"], "cases": [
            {"id":"pre_interference","label":"UNIVERSALLY_UNIFORM","recovery":["restore_a"],"final":"000"},
            {"id":"stale_then_refreshed","stale":{"label":"UNKNOWN_STALE_CERTIFICATE","recovery":None},"refreshed":{"label":"UNIVERSALLY_UNIFORM","recovery":["clear_owned_a"],"final":"001"}},
            {"id":"journal_gap","label":"UNKNOWN_EVENT_CHAIN","recovery":None,"final":None}
        ]}
        for mutate in (
            lambda d: d["cases"][1]["stale"].update(label="UNIVERSALLY_UNIFORM"),
            lambda d: d["cases"][1]["refreshed"].update(final="000"),
            lambda d: d["cases"][2].update(label="UNIVERSALLY_UNIFORM"),
        ):
            changed = copy.deepcopy(fixture)
            mutate(changed)
            self.assertTrue(audit_core.verify(self.model, changed))


if __name__ == "__main__":
    unittest.main()
