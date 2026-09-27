"""Packaging tests only: no effect/issuer processes are started."""
import hashlib
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from verify import canonical, unpack

PUB = Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pub = self.root/'pub'; self.pub.mkdir()
        for p in PUB.glob('evidence-*.bin'): shutil.copy2(p, self.pub/p.name)
        shutil.copy2(PUB/'CAPSULE.json', self.pub/'CAPSULE.json')
    def tearDown(self): self.tmp.cleanup()
    def load(self): return json.loads((self.pub/'CAPSULE.json').read_text())
    def save(self, m): (self.pub/'CAPSULE.json').write_text(json.dumps(m))
    def reject(self):
        with self.assertRaises((ValueError, FileNotFoundError)): unpack(self.pub, self.root/'out')
    def test_valid(self): self.assertEqual(unpack(self.pub,self.root/'out')['member_count'],310)
    def test_existing(self):
        (self.root/'out').mkdir(); self.reject()
    def test_missing_part(self): (self.pub/'evidence-00.bin').unlink(); self.reject()
    def test_corrupt_part(self):
        p=self.pub/'evidence-00.bin'; b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);self.reject()
    def test_wrong_part_order(self):
        m=self.load();m['parts'][0],m['parts'][1]=m['parts'][1],m['parts'][0];self.save(m);self.reject()
    def test_wrong_archive(self):
        m=self.load();m['archive_sha256']='0'*64;self.save(m);self.reject()
    def test_member_count(self):
        m=self.load();m['member_count']+=1;self.save(m);self.reject()
    def test_manifest_hash(self):
        m=self.load();m['inner_manifest_sha256']='0'*64;self.save(m);self.reject()
    def test_path_rules(self):
        for name in ('../x','/x','x/../y','a//b','a/./b','a\\b','C:/a',''):
            self.assertFalse(canonical(name))
        self.assertTrue(canonical('source/audit.py'))
    def test_expansion_limit(self):
        m=self.load();m['tar_bytes']=1;self.save(m);self.reject()
if __name__=='__main__': unittest.main(verbosity=2)
