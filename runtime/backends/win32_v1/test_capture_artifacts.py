import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

from runtime.backends.win32_v1.backend import Win32Backend
from runtime.backends.win32_v1.capture_artifacts import CaptureArtifacts


class Win32CaptureArtifactTests(unittest.TestCase):
    def backend(self, raw):
        backend = object.__new__(Win32Backend)
        backend.targets = {"fixture": 1234}
        backend.capture_pixels = Mock(return_value=raw)
        backend.capture_artifacts = None
        return backend

    def test_capture_artifact_is_png_of_exact_bgrx_capture(self):
        # Top-down pixels: opaque red then green, in GetDIBits BGRX order.
        raw = bytes((0, 0, 255, 0, 0, 255, 0, 0))
        backend = self.backend(raw)
        with tempfile.TemporaryDirectory() as directory:
            backend.configure_capture_artifacts(directory)
            row = backend.capture("fixture", "window_client", 3, 4, 2, 1)
            artifact = row["artifact"]
            path = Path(artifact["path"])
            data = path.read_bytes()
            self.assertEqual(artifact["mime_type"], "image/png")
            self.assertEqual(artifact["source_raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(artifact["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(artifact["bytes"], len(data))
            self.assertEqual((artifact["width"], artifact["height"]), (2, 1))
            with Image.open(path) as image:
                self.assertEqual(image.mode, "RGB")
                self.assertEqual(list(image.getdata()), [(255, 0, 0), (0, 255, 0)])
            self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(row["native_window_id"], 1234)
            self.assertEqual(row["region"], [3, 4, 2, 1])

    def test_artifact_failure_preserves_raw_capture_metadata(self):
        raw = bytes((0, 0, 0, 0) * 2)
        backend = self.backend(raw)

        class FailedArtifacts:
            def write(self, *_args):
                raise OSError("injected PNG write failure")

        backend.capture_artifacts = FailedArtifacts()
        row = backend.capture("fixture", "screen_physical_px", 0, 0, 2, 1)
        self.assertEqual(row["bytes"], len(raw))
        self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn("injected PNG write failure", row["artifact_error"])

    def test_artifact_manager_rejects_invalid_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = CaptureArtifacts(directory)
            with self.assertRaisesRegex(ValueError, "dimensions mismatch"):
                artifacts.write(b"short", 2, 1)

    def test_rgb_handoff_is_explicitly_unsupported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "do not retain RGB"):
                CaptureArtifacts(directory, retain_rgb=True)


if __name__ == "__main__":
    unittest.main()
