from __future__ import annotations

import unittest
import hashlib
import json
from pathlib import Path

from audit import f32, reconstruct


class ReconstructionTests(unittest.TestCase):
    def test_full_git_sha_format(self) -> None:
        current_main = "6473562399159d8913839c0b6fa2da3df68c0bc3"
        self.assertEqual(len(current_main), 40)
        self.assertTrue(all(char in "0123456789abcdef" for char in current_main))

    def test_float32_round_trip_is_explicit(self) -> None:
        self.assertEqual(f32(1.0 / 3.0), 0.3333333432674408)

    def test_role_a_uses_direct_encoder_and_head(self) -> None:
        tensors = {"A": {
            "enc.0.weight": [[1.0]], "enc.0.bias": [0.0],
            "head.weight": [[1.0], [-1.0]], "head.bias": [0.0, 0.0],
        }}
        self.assertEqual(reconstruct(tensors, "A", [1.0]), 0)
        self.assertEqual(reconstruct(tensors, "A", [-1.0]), 1)

    def test_role_b_applies_rank_two_adapter_after_core_head(self) -> None:
        tensors = {"B": {
            "core.enc.0.weight": [[1.0]], "core.enc.0.bias": [0.0],
            "core.head.weight": [[1.0], [0.0]], "core.head.bias": [0.0, 0.0],
            "a": [[1.0, 0.0]], "b": [[0.0, 4.0], [0.0, 0.0]],
        }}
        self.assertEqual(reconstruct(tensors, "B", [1.0]), 1)

    def test_all_retained_fixture_predictions_reconstruct(self) -> None:
        root = Path(__file__).resolve().parents[3]
        seed = root / "research" / "needle_role_skill_reload_3780_v1" / "formal" / "seed-3788" / "builder"
        skill_bytes = (seed / "skill.json").read_bytes()
        expected_bytes = (seed / "expected.json").read_bytes()
        self.assertEqual(hashlib.sha256(skill_bytes).hexdigest(),
                         "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
        self.assertEqual(hashlib.sha256(expected_bytes).hexdigest(),
                         "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61")
        tensors = json.loads(skill_bytes)["tensors"]
        fixtures = json.loads(expected_bytes)["roles"]
        for role in ("A", "B", "C"):
            self.assertEqual(len(fixtures[role]["inputs"]), 4096)
            for index, row in enumerate(fixtures[role]["inputs"]):
                self.assertEqual(reconstruct(tensors, role, row), fixtures[role]["pred"][index],
                                 f"role={role} index={index}")


if __name__ == "__main__":
    unittest.main()
