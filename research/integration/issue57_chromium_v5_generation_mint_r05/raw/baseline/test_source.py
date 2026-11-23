"""Fake-only contract check for V5 point mint across target generations."""
import copy
import hashlib
from pathlib import Path
import sys
import types
import unittest

from PIL import Image, ImageDraw

from research.live_control.executor_v3 import DecisionRequired
from research.live_control.model_point_target_v1 import OPERATION

# Import only the exact class under test. The V5 module's historical parent
# chain imports unrelated GUI/Calc dependencies, which this direct method
# contract does not need.
sys.path.insert(0, str(Path(__file__).resolve().parent))
if "session_v32" not in sys.modules:
    parent = types.ModuleType("session_v32")
    parent.Backend = object
    parent.suite = types.SimpleNamespace()
    sys.modules["session_v32"] = parent
from research.live_control.session_v33 import Backend as PointMintBackend
from runtime.guarded_x11_v1.handles import TargetHandleStore


GEN_A = "a" * 64
GEN_B = "b" * 64


def observation(sequence, capture_ns, process_generation, window_generation):
    return {
        "sequence": sequence,
        "capture_ns": capture_ns,
        "pointer_binding": {
            "focus": 17,
            "surface": 29,
            "geometry": [0, 0, 160, 120],
            "process_generation": process_generation,
            "window_generation": window_generation,
        },
    }


def textured_image():
    image = Image.new("RGB", (160, 120), (12, 24, 36))
    draw = ImageDraw.Draw(image)
    for left, colors in ((32, ((220, 40, 10), (70, 180, 30))),
                         (72, ((10, 190, 220), (220, 70, 170)))):
        for row in range(4):
            for column in range(4):
                color = colors[(row + column) % 2]
                x, y = left + column * 4, 32 + row * 4
                draw.rectangle((x, y, x + 3, y + 3), fill=color)
    return image


class Harness:
    def __init__(self, current_process_generation, current_window_generation):
        self.sequence = 1
        self.current = observation(1, 100, GEN_A, GEN_A)
        self.pixels = textured_image()
        self.point_source_history = {
            1: {"observation": copy.deepcopy(self.current), "image": self.pixels.copy()}
        }
        self.handles = TargetHandleStore("chromium-v5-fake-scope",
                                        id_factory=lambda: "private-random-id")
        self.records = []
        self.events = []
        self.current_process_generation = current_process_generation
        self.current_window_generation = current_window_generation

    def observation(self):
        return copy.deepcopy(self.current)

    def image(self):
        return self.pixels.copy()

    def snapshot(self, _identifier, _index):
        self.sequence += 1
        self.current = observation(self.sequence, 200 + self.sequence,
                                   self.current_process_generation,
                                   self.current_window_generation)
        self.records.append({"sequence": self.sequence,
                             "generation": [self.current_process_generation,
                                            self.current_window_generation]})
        return copy.deepcopy(self.current)

    def emit(self, event):
        self.events.append(copy.deepcopy(event))

    def _refuse_point_mint(self, identifier, index, reason, **details):
        self.emit({"event": "target_handle_mint_from_point_refused",
                   "id": identifier, "step": index, "reason": reason,
                   "handle_created": False,
                   "authority": "refusal only; grants no input authority",
                   **details})
        raise DecisionRequired("point-derived target " + reason)


def execute_point_mint(harness, *, alias="submit"):
    step = {
        "op": OPERATION,
        "name": alias,
        "coordinate_frame": "window_content",
        "source_sequence": 1,
        "point": [40, 40],
        "region_size": [16, 16],
        "ttl_ms": 30_000,
        "freshness_ms": 1_000,
        "search_radius": 0,
        "allowed_transformations": ["window_translation"],
    }
    return PointMintBackend.execute(harness, step, None, "attempt-1", 0)


class ChromiumV5GenerationMintGuardTests(unittest.TestCase):
    def test_point_mint_refuses_process_generation_change_with_identical_pixels(self):
        harness = Harness(GEN_B, GEN_A)
        before = hashlib.sha256(harness.pixels.tobytes()).hexdigest()
        with self.assertRaisesRegex(DecisionRequired, "process_generation_changed"):
            execute_point_mint(harness)
        self.assertEqual(hashlib.sha256(harness.pixels.tobytes()).hexdigest(), before)
        self.assertEqual(harness.sequence, 2)
        self.assertEqual(len(harness.handles._entries), 0)
        self.assertEqual(len(harness.events), 1)
        self.assertEqual(harness.events[0]["handle_created"], False)
        self.assertEqual(harness.events[0]["reason"], "process_generation_changed")

    def test_point_mint_refuses_window_generation_change_with_identical_pixels(self):
        harness = Harness(GEN_A, GEN_B)
        with self.assertRaisesRegex(DecisionRequired, "window_generation_changed"):
            execute_point_mint(harness)
        self.assertEqual(len(harness.handles._entries), 0)
        self.assertEqual(harness.events[0]["handle_created"], False)
        self.assertEqual(harness.events[0]["reason"], "window_generation_changed")

    def test_point_mint_accepts_same_generation_and_keeps_private_registry_id(self):
        harness = Harness(GEN_A, GEN_A)
        result = execute_point_mint(harness)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["handle"], "submit")
        self.assertEqual(result["reference_kind"], "session_alias")
        self.assertIs(result["private_registry_id_exposed"], False)
        self.assertEqual(result["source_sequence"], 1)
        self.assertEqual(result["fresh_sequence"], 2)
        self.assertIs(result["fresh_patch_exact"], True)
        self.assertEqual(result["source_patch_sha256"], result["fresh_patch_sha256"])
        self.assertEqual(set(harness.handles._entries), {"private-random-id"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
