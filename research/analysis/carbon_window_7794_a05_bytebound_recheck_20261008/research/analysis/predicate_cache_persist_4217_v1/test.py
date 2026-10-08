import unittest, subprocess, json, sys, pathlib
R=pathlib.Path(__file__).parent; E=R/'experiment.py'
def call(x): return json.loads(subprocess.run([sys.executable,'-B',str(E)],input=json.dumps(x)+'\n',text=True,capture_output=True,check=True).stdout)
BASE={'form_generation':1,'required_form_generation':1,'intent_version':1,'producer_version':1,'source_generation':1,'source_current':True,'intent':'submit'}
class T(unittest.TestCase):
 def test_same_hit(self):
  a=call({'op':'prepare','state':BASE}); r=call({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':BASE}); self.assertTrue(r['reused']); self.assertTrue(r['correct'])
 def test_dep_change_miss(self):
  a=call({'op':'prepare','state':BASE}); s=dict(BASE,form_generation=2); r=call({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':s}); self.assertFalse(r['reused']); self.assertEqual(r['value'],'FALSE')
 def test_stale_unknown(self):
  a=call({'op':'prepare','state':BASE}); s=dict(BASE,source_current=False); r=call({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':s}); self.assertFalse(r['reused']); self.assertEqual(r['value'],'UNKNOWN'); self.assertFalse(r['executable'])
 def test_semantic_aba_misses(self):
  a=call({'op':'prepare','state':BASE}); s=dict(BASE,form_generation=3,required_form_generation=3); r=call({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':s}); self.assertFalse(r['reused']); self.assertEqual(r['value'],'TRUE')
if __name__=='__main__': unittest.main()
