import ast,pathlib,unittest
H=pathlib.Path(__file__).parent
class Static(unittest.TestCase):
 def test_fixed_six_batch_schedule(self):
  t=(H/'run_batch.py').read_text().replace(' ','');self.assertIn("1:['busy','sleep','hybrid200']",t);self.assertIn("6:['hybrid200','busy','sleep']",t)
 def test_three_mechanisms_and_cpu_gate(self):
  t=(H/'build_mechanisms.py').read_text();self.assertIn("'sleep':SLEEP",t);self.assertIn("'busy':BUSY",t);self.assertIn("'hybrid200':HYBRID",t);self.assertIn('processCPUNS',t)
  a=(H/'aggregate.py').read_text();self.assertIn("*0.5",a.replace(' ',''));self.assertIn("eligible_sessions']==6",a)
 def test_no_scorer_import_in_orchestration(self):
  for name in ['build_mechanisms.py','run_batch.py','aggregate.py']:
   tree=ast.parse((H/name).read_text());mods={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{x.name for n in ast.walk(tree) if isinstance(n,ast.Import) for x in n.names};self.assertNotIn('openpyxl',mods)
if __name__=='__main__':unittest.main()
