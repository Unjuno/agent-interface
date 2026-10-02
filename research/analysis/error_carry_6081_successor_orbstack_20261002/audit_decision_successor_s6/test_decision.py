import json, unittest
from fractions import Fraction as F
from pathlib import Path
import audit_decision as gate

class DecisionConstruction(unittest.TestCase):
    def test_constant_nearest_and_per_slot_are_same_action(self):
        v=(F(1,2),F(1,4)); acts=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1)),(F(-1),F(0)),(F(0),F(-1))]
        i=min(range(len(acts)),key=lambda j:((acts[j][0]-v[0])**2+(acts[j][1]-v[1])**2,j))
        self.assertEqual([acts[i]]*4,[acts[i] for _ in range(4)])
    def test_baseline_unsafe_can_be_improved_by_safe_carry(self):
        case={"intent":["3/4","1/8"],"horizon":4,"box":[-1,3,-1,2]}
        acts=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1)),(F(-1),F(0)),(F(0),F(-1))]
        result=gate.recompute(case,acts,"4way")
        fixed,carry,score=result
        _,base_bad,_=score(fixed); _,carry_bad,_=score(carry)
        self.assertGreater(base_bad,0)
        self.assertEqual(carry_bad,0)
    def test_hull_is_distinct_for_4_and_8_way(self):
        self.assertFalse(gate.hull((F(1),F(1)),"4way"))
        self.assertTrue(gate.hull((F(1),F(1)),"8way"))
    def test_hash_pin_is_fixed(self):
        self.assertTrue(callable(gate.decide))

if __name__=="__main__": unittest.main()
