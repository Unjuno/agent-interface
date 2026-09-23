"""Integration with unchanged Decoder and real PNG publication; no GUI/input."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from candidate import ConditionalEncoder, Encoder, Decoder, Frame, ROOT
from image_artifact import ImageArtifactSink

spec = importlib.util.spec_from_file_location('prior_candidate',
    ROOT/'research/conditional_optimization/transport-revisit-v1/candidate.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def f(array, mode='RGB'):
    return Frame(array.shape[1], array.shape[0], mode, array.tobytes())


class Integration(unittest.TestCase):
    def test_v1_v2_wire_identity_across_modes_edges_and_routes(self):
        rng = np.random.default_rng(20260915)
        for mode, channels in [('L', 1), ('RGB', 3), ('RGBA', 4)]:
            for size in [1, 7, 16, 64, 128]:
                a = rng.integers(0, 256, (71, 83, channels), dtype=np.uint8)
                old, new, dec = prior.ConditionalEncoder('x', size), ConditionalEncoder('x', size), Decoder('x')
                for i in range(12):
                    if i % 3 == 1:
                        a[i, i, 0] ^= 255
                    elif i % 3 == 2:
                        a = rng.integers(0, 256, a.shape, dtype=np.uint8)
                    frame = f(a, mode)
                    kw = dict(action_id=str(i), observed_ns=i, context=('surface', i))
                    before = old.encode(frame, **kw)
                    after = new.encode(frame, **kw)
                    self.assertEqual(before, after)
                    self.assertEqual(dec.accept(after), frame)
                    self.assertEqual(dec.metadata['context'], ['surface', i])

    def test_cold_repeat_matches_O1(self):
        a = Frame(16, 16, 'L', bytes(256))
        baseline, new = Encoder('x', 'O1'), ConditionalEncoder('x')
        for i in range(3):
            kw = dict(action_id=str(i), observed_ns=i)
            self.assertEqual(baseline.encode(a, **kw), new.encode(a, **kw))

    def test_real_png_reuse_keeps_new_action_and_context(self):
        with tempfile.TemporaryDirectory() as td:
            enc, dec, sink = ConditionalEncoder('x'), Decoder('x'), ImageArtifactSink(td)
            paths = []
            for i in range(3):
                frame = Frame(65, 67, 'RGB', bytes(bytearray(65*67*3)))
                wire = enc.encode(frame, action_id=f'a{i}', observed_ns=100+i, context=('focus', i))
                got = dec.accept(wire)
                artifact = sink.publish(got)
                paths.append(artifact['image'])
                self.assertEqual(artifact['image_reused'], i > 0)
                self.assertEqual(dec.metadata['action_id'], f'a{i}')
                self.assertEqual(dec.metadata['observed_ns'], 100+i)
                self.assertEqual(dec.metadata['context'], ['focus', i])
                with Image.open(artifact['image']) as image:
                    self.assertEqual(image.tobytes(), frame.pixels)
            self.assertEqual(len(set(paths)), 1)
            self.assertEqual(dec.sequence, 3)
            self.assertEqual(len(list(Path(td).glob('*.png'))), 1)

    def test_missing_png_recreated_without_old_path_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            sink = ImageArtifactSink(td)
            frame = Frame(2, 2, 'L', b'abcd')
            first = sink.publish(frame)
            Path(first['image']).unlink()
            second = sink.publish(frame)
            self.assertFalse(second['image_reused'])
            self.assertNotEqual(first['image'], second['image'])
            with Image.open(second['image']) as image:
                self.assertEqual(image.tobytes(), b'abcd')

    def test_geometry_and_mode_change_requires_full(self):
        frames = [Frame(4, 4, 'L', bytes(16)), Frame(8, 2, 'L', bytes(16)),
                  Frame(2, 2, 'RGBA', bytes(16)), Frame(2, 2, 'RGB', bytes(12))]
        with tempfile.TemporaryDirectory() as td:
            enc, dec, sink = ConditionalEncoder('x'), Decoder('x'), ImageArtifactSink(td)
            for i, frame in enumerate(frames):
                got = dec.accept(enc.encode(frame, action_id=str(i), observed_ns=i))
                self.assertEqual(dec.metadata['kind'], 'full')
                result = sink.publish(got)
                self.assertFalse(result['image_reused'])
                with Image.open(result['image']) as image:
                    self.assertEqual((image.size, image.mode, image.tobytes()),
                        ((frame.width, frame.height), frame.mode, frame.pixels))

    def test_encoder_rollback_all_serialization_routes(self):
        a = Frame(128, 128, 'L', bytes(16384))
        b = Frame(128, 128, 'L', b'1'+bytes(16383))
        c = Frame(128, 128, 'L', bytes([255])*16384)
        for prefix, target in [(None, a), (a, a), (a, b), (a, c)]:
            enc = ConditionalEncoder('x')
            if prefix is not None:
                enc.encode(prefix, action_id='prefix', observed_ns=0)
            state = (enc.sequence, enc.previous, enc.last.copy())
            with patch('candidate.packet', side_effect=OSError('controlled serialization failure')):
                with self.assertRaises(OSError):
                    enc.encode(target, action_id='test', observed_ns=1)
            self.assertEqual((enc.sequence, enc.previous, enc.last), state)

    def test_metadata_serialization_error_rolls_back(self):
        enc = ConditionalEncoder('x')
        with self.assertRaises(TypeError):
            enc.encode(Frame(1, 1, 'L', b'x'), action_id='a', observed_ns=1, context={object()})
        self.assertEqual((enc.sequence, enc.previous, enc.last), (0, None, {}))

    def test_drop_reorder_and_wrong_stream_are_atomic(self):
        frame = Frame(8, 8, 'L', bytes(64))
        enc, dec = ConditionalEncoder('x'), Decoder('x')
        wires = [enc.encode(frame, action_id=str(i), observed_ns=i) for i in range(3)]
        dec.accept(wires[0])
        state = (dec.sequence, dec.frame, dec.metadata.copy())
        for bad in [wires[0], wires[2], wires[1][:-1], wires[1]+b'trailing']:
            with self.assertRaises(ValueError):
                dec.accept(bad)
            self.assertEqual((dec.sequence, dec.frame, dec.metadata), state)
        with self.assertRaises(ValueError):
            Decoder('other').accept(wires[0])
        self.assertEqual(dec.accept(wires[1]), frame)

    def test_reconnect_uses_new_stream_and_full_base(self):
        frame = Frame(8, 8, 'L', bytes(64))
        enc = ConditionalEncoder('x')
        enc.encode(frame, action_id='0', observed_ns=0)
        late = enc.encode(frame, action_id='1', observed_ns=1)
        with self.assertRaises(ValueError):
            Decoder('x').accept(late)
        fresh, dec = ConditionalEncoder('new'), Decoder('new')
        self.assertEqual(dec.accept(fresh.encode(frame, action_id='2', observed_ns=2)), frame)
        self.assertEqual(dec.metadata['kind'], 'full')

    def test_png_collision_is_not_replayed_or_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'001.png'
            path.write_bytes(b'retained sentinel')
            enc, dec, sink = ConditionalEncoder('x'), Decoder('x'), ImageArtifactSink(td)
            frame = Frame(2, 2, 'L', b'abcd')
            got = dec.accept(enc.encode(frame, action_id='a', observed_ns=0))
            with self.assertRaises(FileExistsError):
                sink.publish(got)
            self.assertEqual(path.read_bytes(), b'retained sentinel')
            self.assertEqual((enc.sequence, dec.sequence), (1, 1))
            self.assertIsNone(sink.previous)
            # Publication failure is not permission to replay a transport packet.
            self.assertIsNone(sink.path)

    def test_sparse_count_is_not_a_minimum_wire_size_guarantee(self):
        a, b = Frame(8, 8, 'L', bytes(64)), Frame(8, 8, 'L', bytes([1])*16+bytes(48))
        candidate, reference = ConditionalEncoder('x', 1), Encoder('x', 'O2', 1)
        for encoder in [candidate, reference]:
            encoder.encode(a, action_id='0', observed_ns=0)
        cw = candidate.encode(b, action_id='1', observed_ns=1)
        rw = reference.encode(b, action_id='1', observed_ns=1)
        self.assertEqual(candidate.last['route'], 'sparse_tiles')
        self.assertGreater(len(cw), len(rw))

    def test_reject_invalid_tile_configuration(self):
        for size in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                ConditionalEncoder('x', size)


if __name__ == '__main__':
    unittest.main(verbosity=2)
