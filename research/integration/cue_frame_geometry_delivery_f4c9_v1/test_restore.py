"""Publication-only refusal controls. No GUI/scientific workers are launched."""
import copy
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from restore import restore, relative_name, digest, HERE


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='geometry4323-pack-')
        self.root = Path(self.temp.name)
        self.pub = self.root / 'publication'
        self.pub.mkdir()
        shutil.copy2(HERE / 'CAPSULE.json', self.pub / 'CAPSULE.json')
        shutil.copytree(HERE / 'capsule', self.pub / 'capsule')

    def tearDown(self):
        self.temp.cleanup()

    def meta(self):
        return json.loads((self.pub / 'CAPSULE.json').read_bytes())

    def save(self, value):
        (self.pub / 'CAPSULE.json').write_text(json.dumps(value))

    def rejected(self):
        with self.assertRaises((ValueError, FileNotFoundError, lzma.LZMAError)):
            restore(self.root / 'out', self.pub)
        self.assertFalse((self.root / 'out').exists())

    def test_exact_restore(self):
        result = restore(self.root / 'out', self.pub)
        self.assertEqual(result['files'], 472)
        self.assertEqual(result['member_bytes'], 22571258)

    def test_no_overwrite(self):
        out = self.root / 'out'
        out.mkdir()
        sentinel = out / 'keep'
        sentinel.write_bytes(b'unchanged')
        with self.assertRaises(FileExistsError):
            restore(out, self.pub)
        self.assertEqual(sentinel.read_bytes(), b'unchanged')

    def test_part_changed(self):
        file = self.pub / self.meta()['parts'][0]['path']
        data = bytearray(file.read_bytes())
        data[100] ^= 1
        file.write_bytes(data)
        self.rejected()

    def test_part_missing(self):
        (self.pub / self.meta()['parts'][0]['path']).unlink()
        self.rejected()

    def test_part_reordered(self):
        meta = self.meta()
        meta['parts'][0], meta['parts'][1] = meta['parts'][1], meta['parts'][0]
        self.save(meta)
        self.rejected()

    def test_denominator(self):
        meta = self.meta()
        meta['files'] -= 1
        self.save(meta)
        self.rejected()

    def test_bounded_expansion(self):
        meta = self.meta()
        meta['tar_bytes'] = 1024
        self.save(meta)
        self.rejected()

    def test_original_manifest(self):
        meta = self.meta()
        meta['original_manifest_sha256'] = '0' * 64
        self.save(meta)
        self.rejected()

    def test_path_contract(self):
        for name in ('../escape', '/absolute', 'a/../b', 'a//b', 'a/./b', 'a\\b', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                relative_name(name)

    def test_nonregular_archive(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w') as archive:
            info = tarfile.TarInfo('alias')
            info.type = tarfile.SYMTYPE
            info.linkname = 'not-used'
            archive.addfile(info)
        packed = lzma.compress(raw.getvalue())
        file = self.pub / 'capsule' / 'test.xzpart'
        file.write_bytes(packed)
        meta = self.meta()
        meta.update(parts=[{'path': 'capsule/test.xzpart', 'bytes': len(packed), 'sha256': digest(packed)}],
                    archive_bytes=len(packed), archive_sha256=digest(packed), tar_bytes=len(raw.getvalue()))
        self.save(meta)
        self.rejected()


if __name__ == '__main__':
    unittest.main(verbosity=2)
