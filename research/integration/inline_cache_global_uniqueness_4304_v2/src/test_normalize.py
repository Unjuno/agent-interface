import unittest

from normalize import normalize


class NormalizeTests(unittest.TestCase):
    def test_black_zero_payload_string_round_trips(self):
        original = b"\x00" * 64
        self.assertEqual(normalize(original.decode("UTF-8")), original)

    def test_valid_multibyte_utf8_string_round_trips(self):
        original = b"ASCII\xc2\x80\x00"
        self.assertEqual(normalize(original.decode("UTF-8")), original)

    def test_binary_bytes_remain_identical(self):
        original = b"\x00\xff\x80binary"
        self.assertIs(normalize(original), original)

    def test_other_bytes_like_values_follow_bytes_contract(self):
        self.assertEqual(normalize(bytearray(b"abc")), b"abc")


if __name__ == "__main__":
    unittest.main()
