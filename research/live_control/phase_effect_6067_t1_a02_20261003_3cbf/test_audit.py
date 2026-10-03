"""Hand-authored persistent record; independent corruption expectations."""
import base64
import copy
import hashlib
import struct
import unittest

from audit import audit_cell


def control():
    epoch = 2_000_000_000
    raw = struct.pack("<1024I", 1, *([0xFF0000] * 1023))
    frames = [{"index": i, "due_ns": epoch + ms * 1_000_000,
               "start_ns": epoch + ms * 1_000_000 + 1000,
               "native_return_ns": epoch + ms * 1_000_000 + 2000,
               "extracted_ns": epoch + ms * 1_000_000 + 3000,
               "pixel_sha256": hashlib.sha256(raw).hexdigest(),
               "pixels_b64": base64.b64encode(raw).decode(),
               "decoded": {"id": 1, "color": 0xFF0000}}
              for i, ms in enumerate([5, 125, 245, 365, 485, 605, 725, 845])]
    spec = {"id": "control", "kind": "persistent", "offsets": [0, 0, 0, 0]}
    source = {"pid": 10, "window": 42, "epoch_ns": epoch, "final_pixels": [0] * 1024,
              "final_keymap": "00" * 32, "events": [{"id": 1, "color": 0xFF0000,
              "onset_ns": epoch - 20_000_000, "due_clear_ns": epoch + 1_000_000_000,
              "draw_start_ns": epoch - 19_999_000, "draw_end_ns": epoch - 19_998_000,
              "clear_start_ns": epoch + 1_000_001_000, "clear_end_ns": epoch + 1_000_002_000}]}
    capture = {"pid": 11, "window": 42, "epoch_ns": epoch, "frames": frames,
               "initial_keymap": "00" * 32, "final_keymap": "00" * 32}
    life = {"fixture_pid": 10, "observer_pid": 11, "fixture_exit": 0,
            "observer_exit": 0, "xvfb_pid": 12, "xvfb_exit": 0}
    return spec, source, capture, life


class AuditTests(unittest.TestCase):
    def test_persistent_control_is_reconstructed(self):
        result = audit_cell(*control())
        self.assertEqual(result["seen_ids"], [1])
        self.assertEqual(result["misses"], 0)

    def test_six_effective_corruptions_are_refused(self):
        cases = []
        v = list(control()); v[2]["frames"][0]["start_ns"] = True; cases.append(v)
        v = list(control()); v[2]["frames"].pop(); cases.append(v)
        v = list(control()); v[2]["frames"][0]["pixel_sha256"] = "0" * 64; cases.append(v)
        v = list(control()); v[2]["frames"][0]["decoded"]["id"] = 2; cases.append(v)
        v = list(control()); v[3]["observer_exit"] = 1; cases.append(v)
        v = list(control()); v[1]["events"][0]["clear_start_ns"] = 1; cases.append(v)
        for i, record in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(ValueError):
                    audit_cell(*record)


if __name__ == "__main__":
    unittest.main()
