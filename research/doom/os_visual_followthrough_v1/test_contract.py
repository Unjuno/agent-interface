import unittest,tempfile,pathlib,ast
from oracle import svg_outcome,doom_outcome
class Tests(unittest.TestCase):
 def test_svg(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a.svg';b=pathlib.Path(d)/'b.svg'
   a.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100"><rect id="guard" width="4"/><circle id="task-target" r="2"/></svg>')
   b.write_text('<svg xmlns="http://www.w3.org/2000/svg" id="svg1" width="100"><defs id="defs1"/><rect id="guard" width="4"/></svg>')
   self.assertTrue(svg_outcome(a,b)['independent_success'])
   b.write_text(b.read_text().replace('width="4"','width="5"'));self.assertFalse(svg_outcome(a,b)['independent_success'])
 def test_noop_not_success(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a.svg';a.write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle id="task-target"/></svg>')
   self.assertFalse(svg_outcome(a,a)['independent_success']);self.assertTrue(svg_outcome(a,a,True)['independent_success'])
 def test_map_gate(self):
  s=dict(forward_displacement=1200,cross_track_displacement=0,final={'POSITION_Z':-128},dead=False,timeout=False)
  self.assertTrue(doom_outcome(s)['independent_success'])
  for key,value in [('dead',True),('timeout',True),('forward_displacement',800),('cross_track_displacement',100),('forward_displacement',float('nan'))]:
   t=dict(s);t[key]=value;self.assertFalse(doom_outcome(t)['independent_success'])
 def test_no_controller_oracle_import(self):
  t=ast.parse(pathlib.Path(__file__).with_name('controller.py').read_text());imports=[]
  for node in ast.walk(t):
   if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
   if isinstance(node,ast.ImportFrom):imports.append(node.module)
  self.assertFalse(set(imports)&{'vizdoom','oracle','xml','xml.etree.ElementTree'})
if __name__=='__main__':unittest.main()
