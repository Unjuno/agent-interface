import ast, pathlib, unittest
HERE=pathlib.Path(__file__).resolve().parent
class Static(unittest.TestCase):
 def test_executor_no_openpyxl(self):
  tree=ast.parse((HERE/'experiment.py').read_text())
  names={n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)}|{n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
  self.assertNotIn('openpyxl',names)
 def test_matrix_fixed(self):
  import run_matrix; self.assertEqual(run_matrix.ORDER,[0,12,2,8,1,4])
if __name__=='__main__': unittest.main()
