import unittest

from PIL import Image

from doom_typed_observation_v1 import extract_typed_observation


BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 2, 2]}


class Reader:
    def __init__(self, signal_id, value):
        self.signal_id = signal_id
        self.value = value

    def read_frame(self, observation, frame):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": self.value,
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"],
                "wad_sha256": "0" * 64}


class DoomTypedObservationDomainTests(unittest.TestCase):
    def test_out_of_domain_observed_value_is_not_published(self):
        for signal_id, value in [("health", 201), ("ammo", 1000)]:
            with self.subTest(signal_id=signal_id, value=value):
                readers = {"health": Reader("health", 85),
                           "ammo": Reader("ammo", 47)}
                readers[signal_id] = Reader(signal_id, value)
                with Image.new("RGB", (2, 2)) as frame:
                    with self.assertRaises(ValueError):
                        extract_typed_observation(
                            frame,
                            {"id": 1, "step": 1, "sequence": 1,
                             "capture_ns": 1, "pointer_binding": BINDING},
                            readers,
                            clock=iter((10, 11)).__next__)


if __name__ == "__main__":
    unittest.main()
