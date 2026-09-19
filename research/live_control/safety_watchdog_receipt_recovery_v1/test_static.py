import json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_plan(self):
  p=json.loads((ROOT/'plan.json').read_text()); self.assertEqual(len(p['formal_cases']),8); self.assertEqual(sum(a=='pipe_only' for _,a in p['formal_cases']),4); self.assertEqual(p['formal_rerun_budget'],0)
 def test_watchdog_release_before_journal_source(self):
  s=(ROOT/'watchdog.py').read_text(); self.assertLess(s.index("xtest.fake_input(d,X.KeyRelease"),s.index("if arm=='watchdog_journal'"))
 def test_runner_recovers_only_journal_arm(self):
  s=(ROOT/'run_case.py').read_text(); self.assertIn("if a.arm=='watchdog_journal' and len(journal_rows)==1",s)
if __name__=='__main__': unittest.main()
