"""Data-only packaging regressions; no archived script is run."""
from pathlib import Path
import tempfile
import unittest
from restore import HERE, checked_name, read_members, restore

class Packaging(unittest.TestCase):
    def test_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=restore(Path(tmp)/'new')
            self.assertEqual(report['files'],91)
            self.assertFalse(report['executed_archived_code'])
    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):restore(Path(tmp))
    def test_changed_archive(self):
        blob=b''.join((HERE/f'evidence.{n:02d}.bin').read_bytes() for n in range(1,10))
        changed=bytearray(blob);changed[100]^=1
        with self.assertRaises(ValueError):read_members(bytes(changed))
    def test_truncated_archive(self):
        with self.assertRaises(ValueError):read_members(b'\xfd7zXZ')
    def test_names(self):
        for name in ('/absolute','../relative','a/../b','a//b','a/./b','a\\b',''):
            with self.subTest(name=name),self.assertRaises(ValueError):checked_name(name)
        self.assertEqual(checked_name('study/retained/original.json').as_posix(),'study/retained/original.json')
if __name__=='__main__':unittest.main()
