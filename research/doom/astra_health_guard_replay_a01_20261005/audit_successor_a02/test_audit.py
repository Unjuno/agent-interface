import copy
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
SPEC = importlib.util.spec_from_file_location("astra_a02_audit", HERE / "audit.py")
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class FullSweepAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readout = json.loads((PACKAGE / "input/VISUAL_READOUT.json").read_text())
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text())
        cls.raw = json.loads((PACKAGE / "raw.json").read_text())
        cls.expected, _, _ = AUDITOR.reconstruct(cls.readout, cls.freeze)

    def test_retained_sweep_matches_full_reconstruction(self):
        AUDITOR.validate_sweep(self.raw["sweep"], self.expected)

    def test_rejects_row_mutations(self):
        mutations = (
            (0, 0, "health", 99),
            (0, 0, "phase", "LOCAL PLAN / FEEDBACK"),
            (0, 0, "status", "HARD_INVALIDATED"),
            (0, 0, "reason", "below_hard_minimum"),
            (0, 0, "hard_minimum", 98),
        )
        for threshold, row, field, value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.raw["sweep"])
                changed[threshold]["evaluated_samples"][row][field] = value
                with self.assertRaisesRegex(ValueError, "complete_sweep"):
                    AUDITOR.validate_sweep(changed, self.expected)

    def test_rejects_missing_reordered_and_extra_rows(self):
        for mutate in (
            lambda rows: rows[0]["evaluated_samples"].pop(),
            lambda rows: rows[0]["evaluated_samples"].reverse(),
            lambda rows: rows[0]["evaluated_samples"].append(
                copy.deepcopy(rows[0]["evaluated_samples"][-1])),
        ):
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(self.raw["sweep"])
                mutate(changed)
                with self.assertRaisesRegex(ValueError, "complete_sweep"):
                    AUDITOR.validate_sweep(changed, self.expected)


if __name__ == "__main__":
    unittest.main()
