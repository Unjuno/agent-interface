import json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_fresh_ids(self):
  p=json.loads((ROOT/'plan_a2.json').read_text()); self.assertEqual(len(p['formal_cases']),8); self.assertTrue(all(cid.startswith('a2-') for cid,_ in p['formal_cases'])); self.assertEqual(p['formal_rerun_budget'],0)
 def test_wrapper_single_replace(self):
  a=(ROOT/'run_case.py').read_text(); w=(ROOT/'run_case_a2.py').read_text(); old="wd_out,wd_err=wd.communicate(timeout=2); wd_debug=json.loads(wd_out.strip())"; new="wd_out,wd_err=wd.communicate(timeout=2); wd_lines=[x for x in wd_out.splitlines() if x.strip()]; wd_debug=json.loads(wd_lines[-1])"; self.assertEqual(a.count(old),1); self.assertIn("s.replace(old,new)",w); self.assertIn(old,w); self.assertIn(new,w)
 def test_science_unchanged(self):
  p=json.loads((ROOT/'plan_a2.json').read_text()); self.assertEqual(p['kill_after_press_ms'],75); self.assertEqual(p['data_recovery_after_press_ms'],250); self.assertEqual(sum(a=='pipe_only' for _,a in p['formal_cases']),4)
if __name__=='__main__': unittest.main()
