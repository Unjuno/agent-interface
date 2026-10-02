from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicationByteIdentity(unittest.TestCase):
    def test_all_frozen_source_and_reference_bytes_match(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
        for name, digest in freeze["sources"].items():
            with self.subTest(kind="source", name=name):
                self.assertEqual(sha(ROOT / name), digest)
        for name, relative_path in freeze["reference_sources"].items():
            with self.subTest(kind="reference", name=name):
                self.assertEqual(
                    sha(REPO / relative_path),
                    freeze["reference_sources_sha256"][name],
                )

    def test_frozen_candidate_readme_is_preserved_byte_for_byte(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
        self.assertEqual(sha(ROOT / "README.md"), freeze["sources"]["README.md"])

    def test_formal_denominator_and_append_only_correction_are_explicit(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
        treatment = freeze["treatment"]
        total = treatment["blocks"] * treatment["requests_per_arm_per_block"] * 2
        self.assertEqual(total, 30000)
        report = (ROOT / "PUBLICATION_REPAIR.md").read_text(encoding="utf-8")
        self.assertIn("15,000 per arm", report)
        self.assertIn("30,000", report)
        # Historical README and freeze are source evidence: leave them intact.
        self.assertEqual(sha(ROOT / "README.md"), freeze["sources"]["README.md"])

    def test_raw_formal_blob_identity_is_retained(self):
        raw = ROOT / "results/formal-04/raw.json"
        data = raw.read_bytes()
        # Git may normalize JSON line endings in a Windows worktree. Compare
        # the committed blob representation, not a platform checkout length.
        data = data.replace(b"\r\n", b"\n")
        self.assertEqual(len(data), 316541)
        self.assertEqual(
            hashlib.sha256(data).hexdigest(),
            "9e9a0ef349a08f69d01b7e97756b3e02d6691e835c024380f1b8da876524ab65",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
