"""Evaluate the actual fresh runner's entry/save branch predicates with fault receipts."""
import ast,unittest
from pathlib import Path

def test_expr(message):
 tree=ast.parse(Path(__file__).with_name('runner-successor.py').read_text(encoding='utf-8-sig'))
 nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(s,ast.Raise) and isinstance(s.exc,ast.Call) and s.exc.args and isinstance(s.exc.args[0],ast.Constant) and s.exc.args[0].value==message for s in n.body)]
 if len(nodes)!=1: raise AssertionError(f'expected one {message} guard, found {len(nodes)}')
 return compile(ast.Expression(nodes[0].test),'<actual-runner-guard>','eval')

class ReleaseContract(unittest.TestCase):
 def test_fault_receipts_are_rejected_for_entry_and_save(self):
  cases=[('missing',{'status':'completed'}),('empty',{'status':'completed','execution':{'releases':[]}}),('unknown',{'status':'completed','execution':{'releases':[{'verified':None,'keys_down':[],'buttons_down':[]}]}}),('missing-key-state',{'status':'completed','execution':{'releases':[{'verified':True,'buttons_down':[]}]}}),('held-key',{'status':'completed','execution':{'releases':[{'verified':True,'keys_down':['a'],'buttons_down':[]}]}}),('failed-status',{'status':'refused','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}})]
  for message,name in [('fresh entry failed','first'),('fresh save failed','save_result')]:
   expr=test_expr(message)
   for label,row in cases:
    with self.subTest(branch=message,case=label):self.assertTrue(eval(expr,{}, {name:row}),f'{message}: {label} must stop')
 def test_verified_neutral_release_is_accepted(self):
  row={'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
  for message,name in [('fresh entry failed','first'),('fresh save failed','save_result')]:
   with self.subTest(branch=message):self.assertFalse(eval(test_expr(message),{}, {name:row}))
if __name__=='__main__':unittest.main()
