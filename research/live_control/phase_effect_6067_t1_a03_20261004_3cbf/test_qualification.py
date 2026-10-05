import base64
import copy
import struct
import unittest
from qualification import qualify

def records(start=20, end=30):
    raw = struct.pack('<1024I', 1, *([0xFF0000] * 1023))
    return ({'events': [{'id': 1, 'color': 0xFF0000, 'draw_start_ns': 10,
                        'draw_end_ns': 20, 'clear_start_ns': 30, 'clear_end_ns': 40}]},
            {'frames': [{'start_ns': start, 'native_return_ns': end,
                         'pixels_b64': base64.b64encode(raw).decode(),
                         'decoded': None}]})

class Qualification(unittest.TestCase):
    def test_stable_closed_interval_uses_pixels_not_decode(self):
        self.assertEqual(qualify(*records()), {'stable_ids': [1], 'boundary_hits': 0, 'unknown_frames': 0})
    def test_boundary_is_not_stable(self):
        self.assertEqual(qualify(*records(19, 29)), {'stable_ids': [], 'boundary_hits': 1, 'unknown_frames': 0})
        self.assertEqual(qualify(*records(21, 31)), {'stable_ids': [], 'boundary_hits': 1, 'unknown_frames': 0})
    def test_unrelated_source_rejected(self):
        with self.assertRaises(ValueError): qualify(*records(41, 42))
    def test_unknown_pixels_not_silent_absence(self):
        so, ca = records()
        ca['frames'][0]['pixels_b64'] = base64.b64encode(struct.pack('<1024I', *([7]*1024))).decode()
        self.assertEqual(qualify(so, ca), {'stable_ids': [], 'boundary_hits': 0, 'unknown_frames': 1})
    def test_timestamp_boolean_rejected(self):
        with self.assertRaises(ValueError): qualify(*records(True, 30))

if __name__ == '__main__': unittest.main()
