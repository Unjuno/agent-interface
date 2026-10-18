import json
import unittest
from pathlib import Path
from unittest.mock import patch

import audit


REPO = Path(__file__).resolve().parents[3]
PREVIEW = (
    "research/integration/compiled_comparison_57_4d74_20261004/a05/"
    "independent-readback/crop-previews/block-1-task-5-frozen.png"
)
DIAGNOSTICS = (
    "research/integration/compiled_comparison_57_4d74_20261004/a05/"
    "independent-readback/C_FAILURE_DIAGNOSTICS.json"
)


class RetainedArtifactAuditTests(unittest.TestCase):
    def test_pinned_artifacts_reconcile(self):
        result = audit.run(REPO)
        self.assertEqual(result["status"], "PASS_RETAINED_BLOB_LINKAGES")
        self.assertEqual(result["verified_local_ocr_rows"], 6)

    def test_crop_byte_mutation_is_rejected(self):
        original = audit.git_blob

        def altered(repo, ref, path):
            value = original(repo, ref, path)
            return value + b"x" if ref == audit.MAIN_REF and path == PREVIEW else value

        with patch.object(audit, "git_blob", side_effect=altered):
            with self.assertRaisesRegex(AssertionError, "crop preview hash mismatch"):
                audit.run(REPO)

    def test_historical_stdout_mutation_is_rejected(self):
        original = audit.git_blob

        def altered(repo, ref, path):
            value = original(repo, ref, path)
            if ref == audit.MAIN_REF and path == DIAGNOSTICS:
                diagnostics = json.loads(value)
                diagnostics["failures"][0]["ocr_stdout"] = "different\n"
                return json.dumps(diagnostics).encode()
            return value

        with patch.object(audit, "git_blob", side_effect=altered):
            with self.assertRaisesRegex(AssertionError, "historical stdout mismatch"):
                audit.run(REPO)


if __name__ == "__main__":
    unittest.main()
