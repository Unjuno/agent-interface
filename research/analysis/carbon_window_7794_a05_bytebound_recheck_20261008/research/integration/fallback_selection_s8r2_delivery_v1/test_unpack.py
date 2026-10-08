"""Publication-only refusal controls, not additional scientific samples."""
from pathlib import Path
import copy
import json
import tempfile
import unittest
from unittest.mock import patch
import unpack

SOURCE = Path(__file__).resolve().parent


class PublicationTests(unittest.TestCase):
    def test_good_original(self):
        self.assertEqual(len(unpack.decode(SOURCE)), 633)

    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'existing destination'):
                unpack.restore(SOURCE, temp)

    def test_invalid_paths(self):
        for name in ['/absolute', '../parent', 'a/../b', 'a//b', 'a/./b', r'a\b', '']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                unpack.safe_name(name)

    def with_modified_pack(self, modifier, message):
        original = json.loads((SOURCE / 'PACK.json').read_bytes())
        altered = copy.deepcopy(original)
        modifier(altered)
        self.assertNotEqual(original, altered)
        with patch.object(unpack.json, 'loads', return_value=altered):
            with self.assertRaisesRegex(ValueError, message):
                unpack.decode(SOURCE)

    def test_oversized_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, 'PACK.json').write_bytes(b' ' * 16385)
            with self.assertRaisesRegex(ValueError, 'pack size'):
                unpack.decode(temp)

    def test_symlink_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, 'PACK.json').symlink_to(SOURCE / 'PACK.json')
            with self.assertRaisesRegex(ValueError, 'not regular pack'):
                unpack.decode(temp)

    def test_wrong_file_count(self):
        self.with_modified_pack(lambda p: p.update(file_count=632), 'file_count')

    def test_boolean_size(self):
        self.with_modified_pack(lambda p: p.update(tar_bytes=True), 'tar_bytes')

    def test_part_reorder(self):
        self.with_modified_pack(lambda p: p['parts'].reverse(), 'part order')

    def test_wrong_archive_digest(self):
        self.with_modified_pack(lambda p: p.update(archive_sha256='0' * 64), 'pack identity')

    def test_changed_part_bytes(self):
        real = unpack.read_bounded
        def changed(path, size):
            value = real(path, size)
            return bytes([value[0] ^ 1]) + value[1:] if path.name == 'part-01.bin' else value
        with patch.object(unpack, 'read_bounded', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'part digest'):
                unpack.decode(SOURCE)

    def test_symlink_part(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'link'
            path.symlink_to(SOURCE / 'part-01.bin')
            with self.assertRaisesRegex(ValueError, 'not regular'):
                unpack.read_bounded(path, 8192)


if __name__ == '__main__':
    unittest.main()
