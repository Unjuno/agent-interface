import ast,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_executor_not_scorer(self):
  tree=ast.parse((HERE/'experiment.py').read_text()); names={n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)}|{n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}; self.assertNotIn('odf',names); self.assertNotIn('odf.opendocument',names)
 def test_order(self):
  import aggregate; self.assertEqual(aggregate.ORDER,[0,12,1])
if __name__=='__main__':unittest.main()
