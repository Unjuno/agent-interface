"""Packaging-only refusal tests; no measured subject or GUI is invoked."""
import io
import lzma
from pathlib import Path
import tarfile
import tempfile
import unittest
from verify import unpack


def archive(names):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as tar:
        for name in names:
            member = tarfile.TarInfo(name)
            member.size = 1
            tar.addfile(member, io.BytesIO(b'x'))
    return lzma.compress(stream.getvalue())


class RefusalTests(unittest.TestCase):
    def test_refuses_path_escape(self):
        with tempfile.TemporaryDirectory() as p, self.assertRaises(ValueError):
            unpack(archive(['../outside']), Path(p), 1)

    def test_refuses_duplicate(self):
        with tempfile.TemporaryDirectory() as p, self.assertRaises(ValueError):
            unpack(archive(['same', 'same']), Path(p), 2)

    def test_refuses_trailing_bytes(self):
        with tempfile.TemporaryDirectory() as p, self.assertRaises(ValueError):
            unpack(archive(['ok']) + b'extra', Path(p), 1)

    def test_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as p:
            (Path(p) / 'same').write_bytes(b'original')
            with self.assertRaises(ValueError):
                unpack(archive(['same']), Path(p), 1)
            self.assertEqual((Path(p) / 'same').read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main(verbosity=2)
