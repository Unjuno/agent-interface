from __future__ import annotations

import hashlib
import os
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = (Path(os.environ["INPUTS_DIR"]) if "INPUTS_DIR" in os.environ else
          ROOT.parents[2] / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder")
REFS = (Path(os.environ["REFERENCE_ROOT"]) if "REFERENCE_ROOT" in os.environ else
        ROOT.parents[2] / "research/analysis")
sys.path.insert(0, str(REFS / "needle_role_skill_lifecycle_4916_first_rung_v2"))
from lifecycle_corrected import ROLES, build_all, expected_rows, load_artifact, predict  # noqa: E402


class WslcLifecycleConstruction(unittest.TestCase):
    def test_exact_inputs(self):
        self.assertEqual(hashlib.sha256((INPUTS / "skill.json").read_bytes()).hexdigest(),
                         "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
        self.assertEqual(hashlib.sha256((INPUTS / "expected.json").read_bytes()).hexdigest(),
                         "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61")

    def test_exact_retained_prediction_parity(self):
        artifact, _ = load_artifact(INPUTS / "skill.json")
        expected = expected_rows(INPUTS / "expected.json")
        models = build_all(artifact)
        checked = 0
        for role in ROLES:
            fixture = expected["roles"][role]
            observed = [predict(models[role], row) for row in fixture["inputs"]]
            self.assertEqual(observed, fixture["pred"], role)
            checked += len(observed)
        self.assertEqual(checked, 12_288)

    def test_frozen_schedule_balances_roles(self):
        counts = Counter(ROLES[i % len(ROLES)] for i in range(1000))
        self.assertEqual(counts, {"A": 334, "B": 333, "C": 333})
        indices = [(i * 37 + 11) % 4096 for i in range(1000)]
        self.assertTrue(all(0 <= index < 4096 for index in indices))
        self.assertEqual(len(indices), len(set(indices)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
