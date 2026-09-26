"""Postmeasurement publication tests. No scientific receiver is executed."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import unpack

HERE=Path(__file__).resolve().parent

class Packaging(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        for p in HERE.glob('SOURCES.*'):
            shutil.copy2(p,self.root/p.name)
        self.manifest=self.root/'SOURCES.json'
    def tearDown(self):
        self.temp.cleanup()
    def change(self,fn):
        m=json.loads(self.manifest.read_text());fn(m)
        self.manifest.write_text(json.dumps(m))
    def refuse(self):
        with self.assertRaises((ValueError,KeyError,FileNotFoundError)):
            unpack.restore(self.manifest,self.root/'new')
    def test_sources(self):
        got=unpack.restore(self.manifest,self.root/'new')
        self.assertEqual(got['files'],16)
        self.assertTrue(got['verified'])
    def test_results(self):
        got=unpack.restore(HERE/'RESULTS.json',self.root/'result')
        self.assertEqual(got['files'],10)
        self.assertTrue(got['verified'])
    def test_existing_destination(self):
        (self.root/'new').mkdir();self.refuse()
    def test_changed_part(self):
        p=self.root/'SOURCES.00.b64';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);self.refuse()
    def test_order(self):
        self.change(lambda m:m['parts'].reverse());self.refuse()
    def test_compressed_digest(self):
        self.change(lambda m:m.update(archive_sha256='0'*64));self.refuse()
    def test_expansion_bound(self):
        self.change(lambda m:m.update(plain_size=4000001));self.refuse()
    def test_members(self):
        self.change(lambda m:m['files'].pop('PLAN.md'));self.refuse()
    def test_paths(self):
        for name in ('../a','/a','a/../b','a\\b','a//b',''):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):unpack.safe(name)

if __name__=='__main__':unittest.main()
