import binascii
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import Mock

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
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            offset = 8
            chunks = []
            while offset < len(data):
                size = struct.unpack(">I", data[offset:offset + 4])[0]
                kind = data[offset + 4:offset + 8]
                payload = data[offset + 8:offset + 8 + size]
                stored_crc = struct.unpack(">I", data[offset + 8 + size:offset + 12 + size])[0]
                self.assertEqual(stored_crc, binascii.crc32(kind + payload) & 0xffffffff)
                chunks.append((kind, payload))
                offset += size + 12
            self.assertEqual(chunks[0][0], b"IHDR")
            self.assertEqual(struct.unpack(">IIBBBBB", chunks[0][1]),
                             (2, 1, 8, 2, 0, 0, 0))
            pixels = zlib.decompress(b"".join(payload for kind, payload in chunks
                                                if kind == b"IDAT"))
            self.assertEqual(pixels, bytes((0, 255, 0, 0, 0, 255, 0)))
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
            invalid = ((b"short", 2, 1), (bytes(4), True, 1),
                       (bytes(4), 8193, 1), (b"", 8192, 8192))
            for raw, width, height in invalid:
                with self.subTest(width=width, height=height, size=len(raw)):
                    with self.assertRaisesRegex(ValueError, "dimensions mismatch"):
                        artifacts.write(raw, width, height)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_rgb_handoff_is_explicitly_unsupported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "do not retain RGB"):
                CaptureArtifacts(directory, retain_rgb=True)


if __name__ == "__main__":
    unittest.main()
