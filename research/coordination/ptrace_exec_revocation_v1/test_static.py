import json,pathlib,unittest
ROOT=pathlib.Path(__file__).parent
class StaticTests(unittest.TestCase):
    def test_schedule(self):
        p=json.loads((ROOT/'plan.json').read_text()); flat=[x for c in p['chunks'] for x in c]
        self.assertEqual(12,len(flat)); self.assertEqual(12,len({x[2] for x in flat})); self.assertEqual(0,p['formal_rerun_budget'])
        counts={}
        for arm,sc,_ in flat: counts[(arm,sc)]=counts.get((arm,sc),0)+1
        self.assertEqual({('no_observer','stable'):3,('no_observer','B_change'):3,('ptrace_exec_revoke','stable'):3,('ptrace_exec_revoke','B_change'):3},counts)
    def test_mechanism_markers(self):
        s=(ROOT/'supervisor.py').read_text(); h=(ROOT/'helper_exec.py').read_text(); r=(ROOT/'run_case.py').read_text()
        self.assertIn('PTRACE_O_TRACEEXEC=0x10',s); self.assertIn('PTRACE_EVENT_EXEC=4',s); self.assertIn("ctrl.sendall(b'EXEC\\n')",s)
        self.assertIn('alias=os.dup(cap)',h); self.assertNotIn('BOUNDARY',h); self.assertIn("if a.arm=='ptrace_exec_revoke':",r); self.assertIn('p_cap.close();revoked=True',r); self.assertIn("begin immediate",r)
if __name__=='__main__': unittest.main()
