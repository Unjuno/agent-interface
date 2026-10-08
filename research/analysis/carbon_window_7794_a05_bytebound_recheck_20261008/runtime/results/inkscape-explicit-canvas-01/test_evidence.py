import unittest,pathlib,tempfile,shutil,json
import verify
class Tests(unittest.TestCase):
 def test_original(self):self.assertEqual(verify.verify()['task_successes'],1)
 def mutate(self,name,change):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'case';shutil.copytree(verify.ROOT,p,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'));f=p/name;j=json.loads(f.read_text());change(j);f.write_text(json.dumps(j))
   with self.assertRaises(ValueError):verify.verify(p)
 def test_false_release(self):self.mutate('canvas/replies/006.json',lambda j:j['reply']['release'].update(verified=False))
 def test_missing_effect(self):self.mutate('canvas/method-trace.json',lambda j:j[1]['predicates'].update(moved_shape=False))
 def test_false_independent_score(self):self.mutate('canvas/evaluation.json',lambda j:j.update(success=False))
 def test_wrong_geometry(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'case';shutil.copytree(verify.ROOT,p,ignore=shutil.ignore_patterns('home','config','cache','data','run','__pycache__'));f=p/'canvas/two-rectangles.svg';f.write_text(f.read_text().replace('x="80"','x="50"'))
   with self.assertRaises(ValueError):verify.verify(p)
if __name__=='__main__':unittest.main()
