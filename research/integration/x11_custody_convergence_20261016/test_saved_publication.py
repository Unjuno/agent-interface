"""Saved-data integrity controls; never import an archived actor or backend."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('custody_publication_reader', HERE / 'read_saved.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class SavedPublicationTests(unittest.TestCase):
    def copied(self):
        temp = self.enterContext(tempfile.TemporaryDirectory())
        root = Path(temp) / 'packet'
        shutil.copytree(HERE / 'capsules', root / 'capsules')
        shutil.copytree(HERE / 'members', root / 'members')
        return root

    def test_complete_publication_keeps_omissions_and_historical_scope(self):
        report = reader.verify(HERE)
        self.assertEqual(report['public_members'], 391)
        self.assertEqual(report['explicit_omissions'], 22)
        self.assertEqual(report['native_or_actor_execution'], False)
        self.assertEqual(report['adoption'], 'HOLD')
        self.assertFalse(report['original_private_bytes_certified'])

    def test_changed_or_missing_public_member_is_rejected(self):
        for change in ('changed', 'missing'):
            with self.subTest(change=change):
                root = self.copied()
                path = root / 'members/c33c34/continuation34/RESULT.md'
                if change == 'changed':
                    path.write_bytes(path.read_bytes() + b'changed')
                else:
                    path.unlink()
                with self.assertRaises(ValueError):
                    reader.verify(root)

    def test_extra_member_or_fabricated_omission_is_rejected(self):
        for name in ('unexpected.txt', 'continuation33/COPYING'):
            with self.subTest(name=name):
                root = self.copied()
                path = root / 'members/c33c34' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'not an original omitted source')
                with self.assertRaises(ValueError):
                    reader.verify(root)

    def test_changed_and_truncated_capsules_are_rejected(self):
        for change in ('changed', 'truncated'):
            with self.subTest(change=change):
                root = self.copied()
                path = root / 'capsules/c33c34.xz'
                raw = path.read_bytes()
                path.write_bytes(raw[:-1] if change == 'truncated' else bytes([raw[0] ^ 1]) + raw[1:])
                with self.assertRaises(ValueError):
                    reader.verify(root)


if __name__ == '__main__':
    unittest.main()
