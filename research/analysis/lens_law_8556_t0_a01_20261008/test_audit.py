import copy
import json
import unittest
from pathlib import Path

from audit import audit, canonical_digest
from candidate import run


ROOT = Path(__file__).parent


def frozen_inputs():
    fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
    truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
    return fixture, truth


class IndependentLensLawAuditTests(unittest.TestCase):
    def test_auditor_reconstructs_frozen_candidate_rows_and_mutation_controls(self):
        fixture, truth = frozen_inputs()
        report = audit(fixture, run(fixture), canonical_digest(fixture), truth)
        self.assertEqual(report["status"], "PASS_LENS_LAW_METHOD_SCOPED")
        self.assertEqual(report["rows"], 12)
        self.assertEqual(report["mutations_rejected"], 4)

    def test_auditor_rejects_a_fabricated_put_put_pass(self):
        fixture, truth = frozen_inputs()
        raw = run(fixture)
        raw["rows"][5]["laws"]["put_put"] = True
        with self.assertRaises(ValueError):
            audit(fixture, raw, canonical_digest(fixture), truth)

    def test_auditor_rejects_a_missing_case_row(self):
        fixture, truth = frozen_inputs()
        raw = run(fixture)
        raw["rows"].pop()
        with self.assertRaises(ValueError):
            audit(fixture, raw, canonical_digest(fixture), truth)

    def test_auditor_rejects_a_changed_fixture_under_the_old_digest(self):
        fixture, truth = frozen_inputs()
        old_digest = canonical_digest(fixture)
        changed = copy.deepcopy(fixture)
        changed["cases"][0]["requested_view"]["value"] = "C"
        with self.assertRaises(ValueError):
            audit(changed, run(changed), old_digest, truth)


if __name__ == "__main__":
    unittest.main()
