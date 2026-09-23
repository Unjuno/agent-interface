import ast, pathlib, unittest
HERE=pathlib.Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_executor_does_not_import_scorers(self):
  tree=ast.parse((HERE/'executor.py').read_text());mods=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods += [a.name for a in n.names]
   elif isinstance(n,ast.ImportFrom) and n.module:mods.append(n.module)
  self.assertFalse(any(x.startswith('openpyxl') or x in {'zipfile','xml.etree.ElementTree'} for x in mods))
 def test_fixed_apps(self):
  s=(HERE/'run_matrix.py').read_text();self.assertIn("('writer',':101')",s);self.assertIn("('calc',':102')",s)
if __name__=='__main__':unittest.main()
