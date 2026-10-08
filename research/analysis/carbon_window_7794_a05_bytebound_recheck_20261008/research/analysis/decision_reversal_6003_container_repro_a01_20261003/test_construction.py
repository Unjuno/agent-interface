"""Non-executing construction checks; does not consume candidate/auditor runs."""
import ast
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FrozenPackageConstruction(unittest.TestCase):
    def test_predecessor_fixture_is_byte_identical(self):
        self.assertEqual(
            sha256((ROOT / "FREEZE.json").read_bytes()),
            "8ff6c4d5d1594ab4623c52483b0f033a8aa6b5ede7f74ea71809461a9469352b",
        )

    def test_fixture_retains_mandatory_sentinel_and_all_controls(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertTrue(freeze["hard_sentinel"]["mandatory"])
        self.assertEqual(freeze["budget"], 4)
        self.assertEqual(
            {row["id"] for row in freeze["selector_fixture"]["experiments"]},
            {"A-cheap-irrelevant", "B-robust-reversal", "C-prior-sensitive"},
        )
        for experiment in freeze["selector_fixture"]["experiments"]:
            for rows in experiment["outcomes"].values():
                self.assertAlmostEqual(sum(row["p"] for row in rows), 1.0)

    def test_candidate_and_auditor_are_syntactically_valid_without_execution(self):
        for name in ("select.py", "audit.py"):
            ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)

    def test_candidate_diff_is_only_scope_metadata(self):
        source = (ROOT / "select.py").read_bytes()
        adapted = source.replace(
            b"OrbStack container CPU reproduction of the frozen synthetic table; no model, GPU, or empirical observations",
            b"host-only CPU synthetic table; no container, model, GPU, or empirical observations",
        )
        self.assertNotEqual(adapted, source)
        self.assertEqual(
            sha256(adapted),
            "f23ce27bed6d9c6de6e29b5715e667783d552ecbd73b049a80fc3e2955e3a316",
        )

    def test_auditor_diff_is_only_output_metadata(self):
        source = (ROOT / "audit.py").read_bytes()
        adapted = source.replace(
            b"PASS_CONTAINER_REPRODUCTION_METHOD",
            b"PASS_HOST_ONLY_CONSTRUCTION",
        ).replace(
            b"independent method audit executed in isolated OrbStack container; synthetic selector only",
            b"does not satisfy the frozen disposable-container condition",
        )
        self.assertNotEqual(adapted, source)
        self.assertEqual(
            sha256(adapted),
            "e1bf0aca36389439bcbf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2",
        )


if __name__ == "__main__":
    unittest.main()
