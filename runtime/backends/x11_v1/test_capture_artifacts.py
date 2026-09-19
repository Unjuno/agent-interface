import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from PIL import Image
from runtime.backends.x11_v1.capture_artifacts import CaptureArtifacts


class CaptureArtifactTests(unittest.TestCase):
    def test_backend_encodes_one_capture_and_retains_packaging_failure(self):
        from runtime.backends.x11_v1.backend import X11Backend
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as tmp:
                backend = object.__new__(X11Backend)
                window = mock.Mock(id=42)
                raw = bytes([0, 0, 255, 0])
                window.get_image.return_value = SimpleNamespace(data=raw, depth=24, visual=8)
                backend.targets = {"fixture": window}
                backend.capture_artifacts = CaptureArtifacts(tmp)
                visual = SimpleNamespace(visual_id=8, visual_class=4,
                                         red_mask=0xff0000, green_mask=0xff00, blue_mask=0xff)
                info = SimpleNamespace(image_byte_order=0,
                    pixmap_formats=[SimpleNamespace(depth=24, bits_per_pixel=32, scanline_pad=32)],
                    roots=[SimpleNamespace(allowed_depths=[SimpleNamespace(visuals=[visual])])])
                backend.d = SimpleNamespace(display=SimpleNamespace(info=info))
                if fail:
                    backend.capture_artifacts.write = mock.Mock(side_effect=OSError("disk failed"))
                row = backend.capture("fixture", "window_client", 0, 0, 1, 1)
                window.get_image.assert_called_once()
                self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(row["native_window_id"], 42)
                self.assertLessEqual(row["capture_started_ns"], row["capture_ended_ns"])
                if fail:
                    self.assertIn("disk failed", row["artifact_error"])
                    self.assertNotIn("artifact", row)
                else:
                    self.assertEqual(row["artifact"]["source_raw_sha256"], row["sha256"])

    def test_both_byte_orders_preserve_colors_and_source_identity(self):
        for order, raw in ((0, bytes([0, 0, 255, 0, 0, 255, 0, 0])),
                           (1, bytes([0, 255, 0, 0, 0, 0, 255, 0]))):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as tmp:
                sink = CaptureArtifacts(tmp)
                row = sink.write(raw, 2, 1, depth=24, bits_per_pixel=32,
                                 scanline_pad=32, byte_order=order,
                                 masks=(0xff0000, 0xff00, 0xff), true_color=True)
                with Image.open(row['path']) as image:
                    self.assertEqual(list(image.getdata()), [(255, 0, 0), (0, 255, 0)])
                self.assertEqual(row['source_raw_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(row['sha256'], hashlib.sha256(Path(row['path']).read_bytes()).hexdigest())

    def test_unsupported_format_writes_no_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = CaptureArtifacts(tmp)
            with self.assertRaises(ValueError):
                sink.write(b'bad', 1, 1, depth=16, bits_per_pixel=16,
                           scanline_pad=32, byte_order=0,
                           masks=(0xf800, 0x7e0, 0x1f), true_color=True)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_truncated_pixels_are_not_encoded(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                CaptureArtifacts(tmp).write(b'bad', 1, 1, depth=24, bits_per_pixel=32,
                    scanline_pad=32, byte_order=0, masks=(0xff0000, 0xff00, 0xff), true_color=True)


if __name__ == '__main__':
    unittest.main()
