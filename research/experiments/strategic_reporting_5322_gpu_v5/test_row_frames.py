import unittest
from row_frames import decode_call, encode_call


class RowFrameTests(unittest.TestCase):
    def test_six_large_synthetic_calls_round_trip(self):
        # 16 response-like rows make each synthetic call larger than a typical control event.
        rows = [{"case_id": i, "status": "REPORT", "p": 0.5,
                 "explanation": "x" * 600} for i in range(16)]
        payload = ("{\"rows\":" + __import__("json").dumps(rows, separators=(",", ":")) + "}").encode()
        for call in range(1, 7):
            frames = encode_call(call, payload)
            self.assertTrue(all(len(line) <= 78 for line in frames))
            self.assertEqual(payload, decode_call(frames, call))

    def test_rejects_missing_reordered_duplicate_corrupt_and_wrong_call(self):
        payload = b'{"rows":[{"case_id":0,"p":0.5}]}'
        frames = encode_call(1, payload)
        mutations = [
            frames[:-1],
            frames[:2] + [frames[3], frames[2]] + frames[4:],
            frames[:2] + [frames[2], frames[2]] + frames[4:],
            frames[:2] + [frames[2][:-1] + ("A" if frames[2][-1] != "A" else "B")] + frames[3:],
        ]
        for changed in mutations:
            with self.subTest(changed=changed[:3]), self.assertRaises(ValueError):
                decode_call(changed, 1)
        with self.assertRaises(ValueError):
            decode_call(frames, 2)

    def test_rejects_empty_and_oversized_input(self):
        with self.assertRaises(ValueError):
            encode_call(1, b"")
        with self.assertRaises(ValueError):
            encode_call(1, b"x" * (128 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
