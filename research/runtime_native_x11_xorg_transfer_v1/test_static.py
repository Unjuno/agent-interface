import ast, pathlib, unittest
H=pathlib.Path(__file__).parent
class Static(unittest.TestCase):
 def test_runner_does_not_import_openpyxl(self):
  t=ast.parse((H/'run_arm.py').read_text());mods={n.names[0].name for n in ast.walk(t) if isinstance(n,ast.Import)}|{n.module for n in ast.walk(t) if isinstance(n,ast.ImportFrom)};self.assertNotIn('openpyxl',mods)
 def test_xorg_dummy_and_order(self):
  self.assertIn('Driver "dummy"',(H/'xorg-dummy.conf').read_text());self.assertIn("[1,12]",(H/'aggregate.py').read_text().replace(' ',''))
if __name__=='__main__':unittest.main()
