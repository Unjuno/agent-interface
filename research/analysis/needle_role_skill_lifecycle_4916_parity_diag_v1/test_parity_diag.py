from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V2 = REPO / "research/analysis/needle_role_skill_lifecycle_4916_v2"
BUILDER = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder"
sys.path.insert(0, str(V2))

from lifecycle import build_all, expected_rows, load_artifact, predict  # noqa: E402


class ParityDiagnosis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = BUILDER / "skill.json"
        cls.expected_path = BUILDER / "expected.json"
        cls.artifact, _ = load_artifact(cls.skill)
        cls.expected = expected_rows(cls.expected_path)

    def test_frozen_inputs(self):
        self.assertEqual(hashlib.sha256(self.skill.read_bytes()).hexdigest(), "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
        self.assertEqual(hashlib.sha256(self.expected_path.read_bytes()).hexdigest(), "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61")

    def test_all_retained_predictions_with_transposed_lora_output(self):
        models = build_all(self.artifact)
        total = 0
        for role in ("A", "B", "C"):
            fixture = self.expected["roles"][role]
            actual = [predict(models[role], row) for row in fixture["inputs"]]
            if role != "A":
                tensors = self.artifact["tensors"][role]
                # Recompute using the frozen dependency-free scorer with B in
                # the output-by-input orientation required by _linear.
                model = models[role]
                ew, eb, hw, hb, a, b = model
                from lifecycle import _f32, _linear
                corrected = []
                for row in fixture["inputs"]:
                    x = tuple(_f32(value) for value in row)
                    hidden = tuple(_f32(__import__("math").tanh(value)) for value in _linear(x, ew, eb))
                    logits = list(_linear(hidden, hw, hb))
                    rank = _linear(hidden, [list(col) for col in zip(*a)], [0.0, 0.0])
                    delta = _linear(rank, [list(col) for col in zip(*b)], [0.0] * 4)
                    logits = [_f32(base + _f32(change / 2.0)) for base, change in zip(logits, delta)]
                    corrected.append(max(range(4), key=logits.__getitem__))
                actual = corrected
            self.assertEqual(actual, fixture["pred"], role)
            total += len(actual)
        self.assertEqual(total, 12288)


if __name__ == "__main__":
    unittest.main(verbosity=2)
