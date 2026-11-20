import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('saved_verify',HERE/'verify.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Packaging(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)
        for f in HERE.glob('evidence.part*.b64'):shutil.copy2(f,self.p/f.name)
        shutil.copy2(HERE/'EVIDENCE_PARTS.json',self.p/'EVIDENCE_PARTS.json')
    def tearDown(self):self.t.cleanup()
    def test_original_exact_members(self):self.assertEqual(len(m.payload(self.p)),255)
    def test_missing_part_refuses(self):
        (self.p/'evidence.part0.b64').unlink()
        with self.assertRaises(FileNotFoundError):m.payload(self.p)
    def test_corrupt_part_refuses(self):
        f=self.p/'evidence.part0.b64';b=f.read_bytes();f.write_bytes(b'A'+b[1:])
        with self.assertRaisesRegex(ValueError,'PART_DIGEST'):m.payload(self.p)
    def test_duplicate_part_refuses(self):
        f=self.p/'EVIDENCE_PARTS.json';d=json.loads(f.read_text());d['parts'][1]=d['parts'][0];f.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'ARCHIVE_IDENTITY'):m.payload(self.p)
    def test_parent_part_refuses(self):
        f=self.p/'EVIDENCE_PARTS.json';d=json.loads(f.read_text());d['parts'][0]['file']='../evidence.part0.b64';f.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'BAD_PART_PATH'):m.payload(self.p)
if __name__=='__main__':unittest.main()
