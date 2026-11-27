"""Offline checks for opt-in retention of the Xvfb integration's raw files."""
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _runtime_directory


class BlockedReleaseRetentionTests(unittest.TestCase):
    def test_default_removes_temporary_files(self):
        with _runtime_directory(None) as root:
            path = Path(root)
            (path / 'receipt.json').write_text('receipt')
        self.assertFalse(path.exists())

    def test_explicit_new_absolute_directory_preserves_raw_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'raw'
            with _runtime_directory(str(target)) as root:
                self.assertEqual(Path(root), target)
                (Path(root) / 'receipt.json').write_text('receipt')
            self.assertEqual((target / 'receipt.json').read_text(), 'receipt')
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            with self.assertRaises(FileExistsError):
                _runtime_directory(str(target))
            self.assertEqual((target / 'receipt.json').read_text(), 'receipt')

    def test_relative_directory_is_refused(self):
        with self.assertRaises(ValueError):
            _runtime_directory('relative-raw')


if __name__ == '__main__':
    unittest.main()
