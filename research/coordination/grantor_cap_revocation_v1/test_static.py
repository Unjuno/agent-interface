import json,pathlib,unittest
R=pathlib.Path(__file__).parent
class T(unittest.TestCase):
 def test_schedule(self):
  p=json.loads((R/'plan.json').read_text());f=[x for c in p['chunks'] for x in c];self.assertEqual(12,len(f));self.assertEqual(12,len({x[2] for x in f}));self.assertEqual(0,p['formal_rerun_budget'])
 def test_mechanism(self):
  h=(R/'helper_exec.py').read_text();r=(R/'run_case.py').read_text();self.assertIn('alias=os.dup(cap_fd)',h);self.assertIn('os.set_inheritable(alias,True)',h);self.assertIn("if a.arm=='grantor_revoke': p_cap.close()",r);self.assertIn("begin immediate",r)
if __name__=='__main__':unittest.main()
