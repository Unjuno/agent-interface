from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OBS = ROOT / "research" / "observation_tiles"
sys.path.insert(0, str(OBS))

import tile_transport as current

spec = importlib.util.spec_from_file_location(
    "legacy_tile_transport", HERE / "legacy_tile_transport.py"
)
legacy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(legacy)

GOLDEN = ROOT / "runtime" / "results" / "golden-desktop-app-server-v3-live-01" / "arms" / "persistent" / "runtime"

GOLDEN_PAIRS = [
    ("019.png", "020.png"),
    ("043.png", "044.png"),
    ("066.png", "067.png"),
    ("071.png", "072.png"),
    ("088.png", "089.png"),
    ("112.png", "113.png"),
    ("117.png", "118.png"),
    ("135.png", "136.png"),
]


def frame_from_array(a: np.ndarray, mode: str) -> current.Frame:
    return current.Frame(a.shape[1], a.shape[0], mode, a.tobytes())


def png_frame(path: Path) -> current.Frame:
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        return current.Frame(rgb.width, rgb.height, "RGB", rgb.tobytes())


class AdoptionEquivalence(unittest.TestCase):
    def compare_sequence(self, frames, stream):
        old = legacy.Encoder(stream, "O2", 64)
        new = current.Encoder(stream, "O2", 64)
        dec = current.Decoder(stream)
        for i, frame in enumerate(frames):
            kw = dict(
                action_id=f"a{i}",
                observed_ns=1000 + i,
                context=("surface", i),
            )
            before = old.encode(frame, **kw)
            after = new.encode(frame, **kw)
            self.assertEqual(before, after)
            self.assertEqual(dec.accept(after), frame)
            self.assertEqual(old.sequence, new.sequence)
            self.assertEqual(old.last["kind"], new.last["kind"])
            self.assertEqual(old.last["wire_bytes"], new.last["wire_bytes"])
            self.assertEqual(old.last["changed_tiles"], new.last["changed_tiles"])

    def test_modes_edges_sparse_dense_unchanged_and_resize(self):
        rng = np.random.default_rng(4139)
        for mode, channels in (("L", 1), ("RGB", 3), ("RGBA", 4)):
            a = rng.integers(0, 256, (71, 83, channels), dtype=np.uint8)
            sparse = a.copy()
            sparse[0, 0, 0] ^= 255
            sparse[-1, -1, -1] ^= 127
            dense = rng.integers(0, 256, a.shape, dtype=np.uint8)
            resized = rng.integers(0, 256, (73, 89, channels), dtype=np.uint8)
            frames = [
                frame_from_array(a, mode),
                frame_from_array(a, mode),
                frame_from_array(sparse, mode),
                frame_from_array(dense, mode),
                frame_from_array(resized, mode),
            ]
            self.compare_sequence(frames, "synthetic-" + mode)

    def test_retained_golden_v3_pairs(self):
        for index, (before_name, after_name) in enumerate(GOLDEN_PAIRS):
            before = png_frame(GOLDEN / before_name)
            after = png_frame(GOLDEN / after_name)
            self.compare_sequence([before, after], f"golden-{index}")

    def test_materialization_failure_does_not_commit_encoder_state(self):
        a = np.zeros((128, 128, 3), dtype=np.uint8)
        b = a.copy()
        b[2, 2, 0] = 1
        enc = current.Encoder("rollback", "O2", 64)
        enc.encode(frame_from_array(a, "RGB"), action_id="0", observed_ns=0)
        state = (enc.sequence, enc.previous, enc.last.copy())
        with patch.object(current.np, "ascontiguousarray", side_effect=OSError("controlled")):
            with self.assertRaises(OSError):
                enc.encode(frame_from_array(b, "RGB"), action_id="1", observed_ns=1)
        self.assertEqual((enc.sequence, enc.previous, enc.last), state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
