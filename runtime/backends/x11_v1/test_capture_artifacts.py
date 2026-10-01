import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from PIL import Image
from runtime.backends.x11_v1.capture_artifacts import CaptureArtifacts


class CaptureArtifactTests(unittest.TestCase):
    def test_read_only_capture_calls_no_input_or_focus_methods(self):
        from runtime.backends.x11_v1.backend import X11Backend
        backend = object.__new__(X11Backend)
        backend.capture = mock.Mock(return_value={"sha256": "capture"})
        backend.focus = mock.Mock()
        backend.release_all = mock.Mock()
        backend.execute = mock.Mock()
        self.assertEqual(backend.observe_read_only("fixture", "window_client", [0, 0, 2, 2]),
                         {"sha256": "capture"})
        backend.capture.assert_called_once_with("fixture", "window_client", 0, 0, 2, 2)
        backend.focus.assert_not_called()
        backend.release_all.assert_not_called()
        backend.execute.assert_not_called()

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

    def test_stage_brackets_retain_exact_artifact_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = CaptureArtifacts(tmp)
            raw = bytes([0, 0, 255, 0])
            with mock.patch("runtime.backends.x11_v1.capture_artifacts.time.monotonic_ns",
                            side_effect=[10, 20, 40, 70, 80]):
                row = sink.write(raw, 1, 1, depth=24, bits_per_pixel=32,
                    scanline_pad=32, byte_order=0,
                    masks=(0xff0000, 0xff00, 0xff), true_color=True)
            self.assertEqual(row['timing_ns'], {'started': 10, 'converted': 20,
                'encoded': 40, 'written': 70, 'hashed': 80})
            data = Path(row['path']).read_bytes()
            self.assertEqual(row['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(row['source_raw_sha256'], hashlib.sha256(raw).hexdigest())
            with Image.open(row['path']) as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))

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

    def test_rgb_handoff_matches_saved_pixels_both_orders_and_consumes_once(self):
        for order, raw in ((0, bytes([3, 2, 1, 0, 6, 5, 4, 0])),
                           (1, bytes([0, 1, 2, 3, 0, 4, 5, 6]))):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as tmp:
                sink = CaptureArtifacts(tmp, retain_rgb=True)
                row = sink.write(raw, 2, 1, depth=24, bits_per_pixel=32,
                    scanline_pad=32, byte_order=order, masks=(0xff0000, 0xff00, 0xff), true_color=True)
                rgb = sink.take_rgb(row)
                with Image.open(row['path']) as saved:
                    self.assertEqual(rgb.tobytes(), saved.convert('RGB').tobytes())
                self.assertEqual(rgb.mode, 'RGB')
                self.assertEqual(rgb.size, (2, 1))
                with self.assertRaises(ValueError):
                    sink.take_rgb(row)

    def test_rgb_handoff_refuses_old_or_modified_identity_and_does_not_leak_after_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = CaptureArtifacts(tmp, retain_rgb=True)
            def write(raw):
                return sink.write(raw, 1, 1, depth=24, bits_per_pixel=32,
                    scanline_pad=32, byte_order=0, masks=(0xff0000, 0xff00, 0xff), true_color=True)
            first = write(bytes([3,2,1,0]))
            second = write(bytes([6,5,4,0]))
            with self.assertRaises(ValueError):
                sink.take_rgb(first)
            with self.assertRaises(ValueError):
                sink.take_rgb(second)
            third = write(bytes([9,8,7,0]))
            altered = dict(third, sha256='0'*64)
            with self.assertRaises(ValueError):
                sink.take_rgb(altered)
            fourth = write(bytes([12,11,10,0]))
            with mock.patch('PIL.Image.Image.save', side_effect=OSError('encode failed')):
                with self.assertRaises(OSError):
                    write(bytes([15,14,13,0]))
            with self.assertRaises(ValueError):
                sink.take_rgb(fourth)

    def test_rgb_handoff_disabled_by_default_and_requires_bool(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = CaptureArtifacts(tmp)
            row = sink.write(bytes([3,2,1,0]), 1, 1, depth=24, bits_per_pixel=32,
                scanline_pad=32, byte_order=0, masks=(0xff0000,0xff00,0xff), true_color=True)
            with self.assertRaises(ValueError):
                sink.take_rgb(row)
            for bad in (1, 'yes', None):
                with self.assertRaises(ValueError):
                    CaptureArtifacts(tmp, retain_rgb=bad)

    def test_bridge_uses_current_rgb_after_png_verification_and_rejects_corruption(self):
        from runtime.guarded_x11_v1.bridge import NativeHandleBridge
        for corruption in (None, 'png', 'raw_link'):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                sink = CaptureArtifacts(Path(tmp)/'images', retain_rgb=True)
                bridge = object.__new__(NativeHandleBridge)
                bridge.out = Path(tmp)
                bridge.target = 'fixture'
                bridge.sequence = 0
                bridge.binding_revision = 0
                bridge.history = {}
                bridge._binding = lambda: {'focus':42,'surface':42,'geometry':[0,0,2,1]}
                def reader(target, frame, region):
                    raw = bytes([3,2,1,0,6,5,4,0])
                    artifact = sink.write(raw, 2, 1, depth=24, bits_per_pixel=32,
                        scanline_pad=32, byte_order=0, masks=(0xff0000,0xff00,0xff), true_color=True)
                    row = {'artifact':artifact,'sha256':hashlib.sha256(raw).hexdigest(),'capture_started_ns':1}
                    if corruption == 'png':
                        Path(artifact['path']).write_bytes(b'changed')
                    elif corruption == 'raw_link':
                        artifact['source_raw_sha256'] = '0'*64
                    return row
                take = mock.Mock(side_effect=sink.take_rgb)
                backend = SimpleNamespace(observe_read_only=reader,take_capture_rgb=take,
                    d=SimpleNamespace(screen=lambda:SimpleNamespace(width_in_pixels=2,height_in_pixels=1)))
                bridge.backend = backend
                bridge.session = SimpleNamespace(backend=backend)
                if corruption:
                    with self.assertRaisesRegex(Exception, 'artifact identity mismatch'):
                        bridge.observe()
                    take.assert_not_called()
                    self.assertEqual(bridge.sequence,0)
                    self.assertEqual(bridge.history,{})
                else:
                    with mock.patch('PIL.Image.open',side_effect=AssertionError('PNG decoder must not run')):
                        observed = bridge.observe()
                    take.assert_called_once()
                    self.assertEqual(observed['image_source'],'exact_capture_rgb_handoff')
                    self.assertEqual(list(bridge.history[1][1].getdata()),[(1,2,3),(4,5,6)])


if __name__ == '__main__':
    unittest.main()
