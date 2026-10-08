"""Fixture-free validation of the documented mount-point buffer layout."""
import struct
import unittest

from runner import IO_REPARSE_TAG_MOUNT_POINT, build_mount_payload


class MountPointBufferTests(unittest.TestCase):
    def test_tag_offsets_lengths_and_terminators(self):
        target = r"C:\temp\fixture\repo\internal"
        payload = build_mount_payload(target)
        tag, data_len, reserved, sub_off, sub_len, print_off, print_len = struct.unpack_from("<IHHHHHH", payload)
        sub = ("\\??\\" + target).encode("utf-16-le")
        printable = target.encode("utf-16-le")
        self.assertEqual(tag, IO_REPARSE_TAG_MOUNT_POINT)
        self.assertEqual(reserved, 0)
        self.assertEqual(data_len, len(payload) - 8)
        self.assertEqual(sub_off, 0)
        self.assertEqual(sub_len, len(sub))
        self.assertEqual(print_off, len(sub) + 2)
        self.assertEqual(print_len, len(printable))
        self.assertEqual(payload[16:16 + sub_len], sub)
        self.assertEqual(payload[16 + sub_len:18 + sub_len], b"\0\0")
        self.assertEqual(payload[16 + print_off:16 + print_off + print_len], printable)
        self.assertEqual(payload[16 + print_off + print_len:], b"\0\0")


if __name__ == "__main__":
    unittest.main()
