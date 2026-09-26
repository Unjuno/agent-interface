import json
from pathlib import Path
import shutil
import tempfile
import unittest
from restore import restore

ROOT=Path(__file__).resolve().parent

class RestoreTests(unittest.TestCase):
    def test_intact_then_existing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out';self.assertEqual(restore(ROOT,p),79)
            with self.assertRaises(ValueError):restore(ROOT,p)

    def test_parts_and_manifest(self):
        for mutation in ('part','order','count','expanded_hash'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                p=Path(d);src=p/'src';src.mkdir()
                spec=json.loads((ROOT/'PACK.json').read_text())
                for e in spec['parts']:shutil.copyfile(ROOT/e['name'],src/e['name'])
                (src/'PACK.json').write_text(json.dumps(spec))
                self.assertEqual(restore(src,p/'control'),79)
                if mutation=='part':
                    f=src/spec['parts'][0]['name'];b=f.read_bytes();f.write_bytes(bytes([b[0]^1])+b[1:])
                elif mutation=='order':spec['parts'].reverse()
                elif mutation=='count':spec['files']+=1
                else:spec['expanded_sha256']='0'*64
                (src/'PACK.json').write_text(json.dumps(spec))
                with self.assertRaises(ValueError):restore(src,p/'bad')

if __name__=='__main__':unittest.main()
