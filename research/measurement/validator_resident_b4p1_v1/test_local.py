import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'baseline'))
from audit import expected
spec=importlib.util.spec_from_file_location('test_validator',ROOT/'baseline/validator.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
F=json.loads((ROOT/'FIXTURES.json').read_text())
class ConstructionTests(unittest.TestCase):
    def test_source_identities(self):
        for r in json.loads((ROOT/'BASELINE.json').read_text())['files']:
            b=(ROOT/r['path']).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
            self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),r['git_blob'])
    def test_compile_sources(self):
        for p in ROOT.glob('*.py'):compile(p.read_text(),str(p),'exec')
    def test_each_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json'
            for i,f in enumerate(F):
                if f['content'] is None:p.unlink(missing_ok=True)
                else:p.write_bytes(f['content'].encode())
                self.assertEqual(v.inspect_file(p),expected(f,i))
    def test_same_path_changes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.json';results=[]
            for i in (0,1,2,3,0):
                if F[i]['content'] is None:p.unlink(missing_ok=True)
                else:p.write_text(F[i]['content'])
                results.append(v.inspect_file(p)['status'])
            self.assertEqual(results,['valid','invalid','valid','input_error','valid'])
    def worker(self,data):
        return subprocess.run([sys.executable,'-I','-S','-B',str(ROOT/'worker.py')],input=data,capture_output=True,timeout=5)
    def test_empty_stream(self):
        r=self.worker(b'');self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'',b''))
    def test_nonstring_request(self):
        r=self.worker(b'false\n');self.assertEqual((r.returncode,r.stdout,r.stderr),(3,b'',b''))
    def test_oversized_request(self):
        r=self.worker(b' '*4096+b'\n');self.assertEqual((r.returncode,r.stdout,r.stderr),(3,b'',b''))
    def test_static_not_live(self):
        r=v.inspect_program(json.loads(F[0]['content']))
        self.assertTrue(r['static_valid']);self.assertFalse(r['side_effect_authority'])
        self.assertIsNone(r['task_success']);self.assertEqual(r['runtime_admission'],'not_evaluated')
if __name__=='__main__':unittest.main()
