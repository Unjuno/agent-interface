"""Delivery-only controls; never launch the consumed producer/auditor."""
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_delivery import check_delivery


class DeliveryTests(unittest.TestCase):
    def test_retained_record(self):
        self.assertEqual(check_delivery(Path(__file__).resolve().parent)['files'], 73)

    def test_same_missing_file_in_both_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'record'
            shutil.copytree(Path(__file__).resolve().parent / 'raw', root / 'raw')
            for copy in ('native', 'export'):
                (root / 'raw' / copy / 'original_fault/native-stdout.jsonl').unlink()
            with self.assertRaisesRegex(ValueError, 'inventory'):
                check_delivery(root)

    def test_modified_audit_anchor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'record'
            shutil.copytree(Path(__file__).resolve().parent / 'raw', root / 'raw')
            with (root / 'raw/audit/AUDIT.json').open('ab') as handle:
                handle.write(b' ')
            with self.assertRaisesRegex(ValueError, 'audit anchor'):
                check_delivery(root)

    def test_modified_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'record'
            shutil.copytree(Path(__file__).resolve().parent / 'raw', root / 'raw')
            with (root / 'raw/native-container-inspect.json').open('ab') as handle:
                handle.write(b' ')
            with self.assertRaisesRegex(ValueError, 'receipt anchor'):
                check_delivery(root)
