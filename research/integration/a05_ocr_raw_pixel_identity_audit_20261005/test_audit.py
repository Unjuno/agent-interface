"""Regression tests for pinned A05 crop-audit inputs."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

AUDIT_PATH = Path(__file__).with_name("audit.py")
SPEC = importlib.util.spec_from_file_location("a05_crop_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CropAuditInputTests(unittest.TestCase):
    def test_rejects_manifest_missing_expected_crop_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps({
                "source_revision": "58bcbb4c45501880db8782158ddd3add3b765984",
                "entries": [],
            }), encoding="utf-8")
            with (
                patch.object(audit, "MANIFEST_PATH", manifest_path),
                patch.object(audit, "EXPECTED_CROP_MANIFEST_SHA256",
                             audit.sha256(manifest_path.read_bytes())),
            ):
                with self.assertRaisesRegex(ValueError, "expected crop entries"):
                    audit.main()

    def test_rejects_modified_manifest_even_when_entry_set_is_complete(self):
        manifest = json.loads(audit.MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["audit_note"] = "modified after freeze"
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(audit, "MANIFEST_PATH", manifest_path):
                with self.assertRaisesRegex(ValueError, "unexpected crop manifest hash"):
                    audit.main()

    def test_rejects_reencoded_archived_ocr_input_with_same_pixels(self):
        ocr_path = audit.A05 / (
            "formal-output/block-1/C/client/ocr-124.png"
        )
        original_read_bytes = Path.read_bytes

        def reencoded_read_bytes(path):
            data = original_read_bytes(path)
            if path != ocr_path:
                return data
            from PIL import Image
            image = Image.open(io.BytesIO(data))
            encoded = io.BytesIO()
            image.save(encoded, format="PNG")
            self.assertNotEqual(encoded.getvalue(), data)
            return encoded.getvalue()

        with patch.object(Path, "read_bytes", reencoded_read_bytes):
            with self.assertRaisesRegex(ValueError, "archived OCR input hash mismatch"):
                audit.main()


if __name__ == "__main__":
    unittest.main()
