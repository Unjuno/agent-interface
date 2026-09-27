#!/usr/bin/env python3
"""Publication-only restoration checks. Never run a timing experiment."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pause_restore', HERE / 'unpack.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


def packed_members(names, kind=tarfile.REGTYPE):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name in names:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = 1 if kind == tarfile.REGTYPE else 0
            info.linkname = 'outside' if kind == tarfile.SYMTYPE else ''
            archive.addfile(info, io.BytesIO(b'x') if info.size else None)
    return stream.getvalue()


class RestoreTests(unittest.TestCase):
    def test_exact_inventory(self):
        records, manifest = restore.load_records(HERE)
        self.assertEqual(len(records), 105)
        self.assertEqual(sum(len(data) for _, data in records), 371268)
        self.assertTrue(manifest['publication_is_retrospective'])

    def test_existing_destination_is_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / 'occupied'
            out.mkdir()
            sentinel = out / 'sentinel'
            sentinel.write_bytes(b'unchanged')
            p = subprocess.run([sys.executable, '-B', str(HERE / 'unpack.py'),
                                '--out', str(out)], capture_output=True, timeout=10)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(sentinel.read_bytes(), b'unchanged')
            self.assertEqual(list(out.iterdir()), [sentinel])

    def test_changed_part_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            copied = Path(root)
            shutil.copyfile(HERE / 'MANIFEST.json', copied / 'MANIFEST.json')
            data = bytearray((HERE / 'evidence.tar.xz.part00').read_bytes())
            data[100] ^= 1
            (copied / 'evidence.tar.xz.part00').write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'part integrity'):
                restore.load_records(copied)

    def test_missing_part_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            shutil.copyfile(HERE / 'MANIFEST.json', Path(root) / 'MANIFEST.json')
            with self.assertRaises(FileNotFoundError):
                restore.load_records(Path(root))

    def test_member_controls(self):
        good = 'research/live_control/scheduler_pause_coverage_316_v2/x'
        controls = [
            ([good, good], tarfile.REGTYPE, 'duplicate'),
            (['../outside'], tarfile.REGTYPE, 'invalid member path'),
            (['/absolute'], tarfile.REGTYPE, 'invalid member path'),
            (['research/live_control/unowned/x'], tarfile.REGTYPE, 'unowned'),
            ([good], tarfile.SYMTYPE, 'non-regular'),
        ]
        for names, kind, reason in controls:
            with self.subTest(reason=reason):
                expected = {'files': len(names), 'raw_bytes': len(names),
                            'inventory_sha256': 'not-an-inventory'}
                with self.assertRaisesRegex(ValueError, reason):
                    restore.validate_members(packed_members(names, kind), expected)

    def test_member_count_is_rejected(self):
        expected = {'files': 2, 'raw_bytes': 1, 'inventory_sha256': ''}
        with self.assertRaisesRegex(ValueError, 'member count'):
            restore.validate_members(packed_members([
                'research/live_control/scheduler_pause_coverage_316_v2/x']), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
