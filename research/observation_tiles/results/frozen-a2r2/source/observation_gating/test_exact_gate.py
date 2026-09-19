"""Synthetic falsification tests; these are not real-GUI evidence."""

import random
import unittest
from dataclasses import replace

from exact_gate import ExactGate, Frame, Receiver


class GateTests(unittest.TestCase):
    def test_small_changes_and_reconstruction(self):
        rng = random.Random(104729)
        raw = bytes(rng.randrange(256) for _ in range(19 * 13 * 3))
        frames = [Frame(19, 13, "RGB", raw)]
        # Every byte position, including single-channel changes at image edges.
        for i in range(len(raw)):
            changed = bytearray(raw)
            changed[i] ^= 1
            frames.extend([Frame(19, 13, "RGB", bytes(changed))] * 2)
        frames.extend([Frame(13, 19, "RGB", raw), Frame(19, 39, "L", raw)])
        for strategy in ("O0", "O1"):
            gate, receiver = ExactGate(strategy, "test"), Receiver("test")
            previous = None
            for i, frame in enumerate(frames):
                update = gate.push(frame, observed_ns=i, action_id=str(i),
                                   context=(("focus", i),))
                self.assertEqual(receiver.accept(update), frame)
                self.assertEqual(update.frame is None,
                                 strategy == "O1" and frame == previous)
                self.assertEqual(update.context, (("focus", i),))
                self.assertEqual(update.observed_ns, i)
                previous = frame

    def test_stale_and_missing_transport_base(self):
        frame = Frame(1, 1, "RGB", b"abc")
        gate = ExactGate("O1", "a")
        first = gate.push(frame, observed_ns=1, action_id="a")
        repeat = gate.push(frame, observed_ns=2, action_id="b")
        with self.assertRaises(ValueError):
            Receiver("a").accept(repeat)
        with self.assertRaises(ValueError):
            Receiver("b").accept(first)
        receiver = Receiver("a")
        receiver.accept(first)
        with self.assertRaises(ValueError):
            receiver.accept(replace(repeat, base_sequence=99))
        with self.assertRaises(ValueError):
            receiver.accept(first)
        fresh = ExactGate("O1", "new").push(frame, observed_ns=3, action_id="c")
        self.assertIsNotNone(fresh.frame)

    def test_invalid_storage_and_strategy(self):
        for args in [(0, 1, "RGB", b""), (1, 1, "RGB", b"a"),
                     (1, 1, "P", b"a")]:
            with self.assertRaises(ValueError):
                Frame(*args)
        with self.assertRaises(TypeError):
            Frame(1, 1, "L", bytearray(b"a"))
        with self.assertRaises(ValueError):
            ExactGate("perceptual", "x")


if __name__ == "__main__":
    unittest.main()
