from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import audit_controls
import build_fixture
import candidate


class AuditorControlBundleTests(unittest.TestCase):
    def test_single_auditor_bundle_accepts_clean_and_rejects_all_six_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture.json"
            output = root / "candidate.json"
            fixture.write_text(json.dumps(build_fixture.make_fixture(), sort_keys=True, indent=2) + "\n")
            candidate.run(fixture, output)
            result = audit_controls.run_controls(fixture, output)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["baseline"]["independently_reconstructed"], 24)
        self.assertEqual(result["control_count"], 6)
        self.assertEqual(result["rejected_controls"], 6)


if __name__ == "__main__":
    unittest.main()
