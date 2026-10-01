"""Offline restoration controls, without running any retained GUI allocation."""
import copy
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import tempfile
import unittest
import unpack

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aba-restore-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.manifest = json.loads((unpack.HERE / 'CAPSULE.json').read_text())
        for name in ['CAPSULE.json'] + [p['path'] for p in self.manifest['parts']]:
            shutil.copyfile(unpack.HERE / name, self.source / name)
    def tearDown(self):
        self.temp.cleanup()
    def write_manifest(self):
        (self.source / 'CAPSULE.json').write_text(json.dumps(self.manifest))
    def altered_payload(self, edit):
        packed = b''.join((self.source / p['path']).read_bytes() for p in self.manifest['parts'])
        obj = json.loads(lzma.decompress(packed)); edit(obj)
        raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()
        compressed = lzma.compress(raw)
        parts = []
        for i, start in enumerate(range(0, len(compressed), 6000)):
            data = compressed[start:start + 6000];name=f'evidence-{i:02d}.xz.part'
            (self.source / name).write_bytes(data)
            parts.append({'path': name, 'bytes': len(data), 'sha256': unpack.digest(data)})
        self.manifest.update(parts=parts, compressed_bytes=len(compressed),
                             compressed_sha256=unpack.digest(compressed),
                             expanded_bytes=len(raw), expanded_sha256=unpack.digest(raw))
        self.write_manifest()
    def refuse(self):
        destination = self.root / 'output'
        with self.assertRaises((ValueError, KeyError, FileNotFoundError)):
            unpack.restore(self.source, destination)
        self.assertFalse(destination.exists())
    def test_positive(self):
        result = unpack.restore(self.source, self.root / 'output')
        self.assertEqual(result['files'], 209)
        self.assertEqual(unpack.digest((self.root/'output/original/AUDIT.json').read_bytes()),
                         '593b9f4a2b30e6dafcfa517ed83d5bc5f96ef913421b1d0084a5e5ab718fd393')
    def test_existing_destination(self):
        out = self.root/'output'; out.mkdir(); (out/'sentinel').write_text('keep')
        with self.assertRaises(ValueError): unpack.restore(self.source, out)
        self.assertEqual((out/'sentinel').read_text(), 'keep')
    def test_missing_part(self):
        (self.source/self.manifest['parts'][0]['path']).unlink();self.refuse()
    def test_changed_part(self):
        p=self.source/self.manifest['parts'][0]['path'];b=p.read_bytes();p.write_bytes(b[:-1]+bytes([b[-1]^1]));self.refuse()
    def test_order(self):
        self.manifest['parts'].reverse();self.write_manifest();self.refuse()
    def test_boolean_count(self):
        self.manifest['members']=True;self.write_manifest();self.refuse()
    def test_traversal_rehashed(self):
        self.altered_payload(lambda o:o['files'][0].update(path='../escape'));self.refuse()
    def test_duplicate_rehashed(self):
        self.altered_payload(lambda o:o['files'][1].update(path=o['files'][0]['path']));self.refuse()
    def test_content_rehashed(self):
        self.altered_payload(lambda o:o['files'][0].update(content=o['files'][0]['content']+'altered'));self.refuse()

if __name__=='__main__': unittest.main(verbosity=2)
