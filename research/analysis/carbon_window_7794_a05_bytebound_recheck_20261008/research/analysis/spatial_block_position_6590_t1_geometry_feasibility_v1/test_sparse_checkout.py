from __future__ import annotations

import json
from pathlib import Path
import unittest


class SparseAnalysisCheckoutTests(unittest.TestCase):
    def test_freezes_bind_root_workflow_without_requiring_sparse_checkout_file(self):
        root = Path(__file__).parent
        specifications = (
            (root / "FREEZE.json", "../../../.github/workflows/analysis-index.yml"),
            (root / "recovery_02" / "FREEZE.json", "../../../../.github/workflows/analysis-index.yml"),
        )
        for freeze_path, source_path in specifications:
            with self.subTest(freeze=freeze_path.parent.name):
                freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
                self.assertIn(source_path, freeze["source_sha256"])
                self.assertEqual(len(freeze["source_sha256"][source_path]), 64)


if __name__ == "__main__":
    unittest.main()
