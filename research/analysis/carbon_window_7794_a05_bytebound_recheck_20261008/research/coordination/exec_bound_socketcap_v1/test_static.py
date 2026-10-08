import json,pathlib,unittest
ROOT=pathlib.Path(__file__).parent
class StaticTests(unittest.TestCase):
    def test_schedule(self):
        p=json.loads((ROOT/'plan.json').read_text()); flat=[x for c in p['chunks'] for x in c]
        self.assertEqual(12,len(flat)); self.assertEqual(12,len({x[2] for x in flat}))
        counts={}
        for arm,sc,_ in flat: counts[(arm,sc)]=counts.get((arm,sc),0)+1
        self.assertEqual({('persistent_cap','stable'):3,('persistent_cap','B_change'):3,('cloexec_cap','stable'):3,('cloexec_cap','B_change'):3},counts)
        self.assertEqual(0,p['formal_rerun_budget'])
    def test_single_factor_markers(self):
        h=(ROOT/'helper_exec.py').read_text(); self.assertIn("os.set_inheritable(fd, arm == 'persistent_cap')",h); self.assertIn('os.execv',h)
        r=(ROOT/'run_case.py').read_text(); self.assertIn('socket.socketpair()',r); self.assertIn("setpriv','--reuid=65534",r); self.assertIn("begin immediate",r)
if __name__=='__main__': unittest.main()
