import json,tempfile,unittest,shutil
from pathlib import Path
import unpack_repo
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); self.tmp=Path(self.t.name)
 def tearDown(self): self.t.cleanup()
 def stage(self):
  r=self.tmp/'pub'; r.mkdir()
  names=['ARCHIVE_PARTS_02.json','PACKAGE_02.json','unpack_repo.py']+[p['name'] for p in json.loads((ROOT/'ARCHIVE_PARTS_02.json').read_text())['parts']]
  for n in names: shutil.copy2(ROOT/n,r/n)
  return r
 def test_roundtrip(self):
  r=self.stage(); out=self.tmp/'out'; got=unpack_repo.unpack(r,out); self.assertEqual({'members':39,'bytes':434651},got)
 def test_corrupt_part(self):
  r=self.stage(); p=next(r.glob('EVIDENCE_*.part00')); b=bytearray(p.read_bytes()); b[10]^=1; p.write_bytes(b); self.assertRaises(ValueError,unpack_repo.unpack,r,self.tmp/'out')
 def test_missing_part(self):
  r=self.stage(); next(r.glob('EVIDENCE_*.part01')).unlink(); self.assertRaises(FileNotFoundError,unpack_repo.unpack,r,self.tmp/'out')
 def test_reordered_manifest(self):
  r=self.stage(); p=r/'ARCHIVE_PARTS_02.json'; m=json.loads(p.read_text()); m['parts'][0],m['parts'][1]=m['parts'][1],m['parts'][0]; p.write_text(json.dumps(m)); self.assertRaises(ValueError,unpack_repo.unpack,r,self.tmp/'out')
 def test_existing_dest(self):
  r=self.stage(); out=self.tmp/'out'; out.mkdir(); self.assertRaises(ValueError,unpack_repo.unpack,r,out)
if __name__=='__main__': unittest.main()
