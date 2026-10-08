from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parent
PARENT_AUDIT = ROOT.parent / "AUDIT.json"


class PublicationCorrectionTests(unittest.TestCase):
    def test_corrected_copy_is_strict_json_with_original_fields(self):
        value = json.loads((ROOT / "AUDIT_CORRECTED.json").read_text(encoding="utf-8"))
        self.assertEqual(value, {
            "allocation": "PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-T0-20261002-01",
            "error_count": 0,
            "errors": [],
            "independent_audit_runs": 1,
        })

    def test_parent_artifact_is_preserved_at_recorded_hash(self):
        digest = hashlib.sha256(PARENT_AUDIT.read_bytes()).hexdigest()
        self.assertEqual(digest, "da602239e384691e4a206ba460985d1461151d45e886984cdf7453f0acad1172")
        self.assertTrue(PARENT_AUDIT.read_bytes().endswith(b"}\\n"))


if __name__ == "__main__":
    unittest.main()
