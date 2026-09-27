import importlib.util, pathlib, unittest
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',HERE/'audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def test_direct_symbols(self):
  text='symbols[Group1]= [ q, Q, at, Greek_OMEGA ];\nsymbols[Group1]= [ less, greater, bar, dead_belowmacron ];'
  self.assertEqual(m.tokens(text),{'at','Greek_OMEGA','bar','dead_belowmacron'})
if __name__=='__main__': unittest.main()
