"""Pure transition tests: no processes, X server or native input."""
import unittest
from death_gate import observe_dead
class DeathGateTests(unittest.TestCase):
    def run_gate(self,states):
        state=iter(states); t=[100]; samples=[]
        def read(): samples.append(1);return next(state)
        def clock(): return t[0]
        def sleep(ns):t[0]+=ns
        return observe_dead(123,read,clock,sleep,250,2)
    def test_live_eof_then_original_zombie(self):
        r=self.run_gate([("S",123),("R",123),("Z",123)])
        self.assertEqual(r["state"],"Z");self.assertEqual(r["at_ns"],104)
        self.assertEqual([s["state"]for s in r["samples"]],["S","R","Z"])
    def test_missing_original_after_exit(self):self.assertEqual(self.run_gate([("missing",None)])["state"],"missing")
    def test_reused_pid_refused(self):
        with self.assertRaisesRegex(ValueError,"GENERATION"):self.run_gate([("R",124)])
    def test_wrong_zombie_refused(self):
        with self.assertRaisesRegex(ValueError,"GENERATION"):self.run_gate([("Z",124)])
    def test_live_timeout_refused(self):
        with self.assertRaisesRegex(ValueError,"TIMEOUT"):self.run_gate([("S",123)]*200)
if __name__=="__main__":unittest.main()
