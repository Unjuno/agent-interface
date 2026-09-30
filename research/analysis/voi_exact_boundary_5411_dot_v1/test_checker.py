import unittest
from fractions import Fraction as Q
from checker import exact_values, decisions, predicate_types_valid

class ExactConstructionTests(unittest.TestCase):
    def test_predicate_boolean_is_not_an_integer(self):
        v=decisions(exact_values(Q(1,2),Q(1),Q(1),Q(0),Q(0)),Q(0))
        self.assertTrue(predicate_types_valid(v))
        v['premium_dominated_wait']=0
        self.assertFalse(predicate_types_valid(v))

    def test_perfect_observation_with_zero_action_value(self):
        v=exact_values(Q(1,2),Q(1),Q(1),Q(0),Q(0))
        self.assertEqual(v['action_value'],0)
        self.assertEqual(v['net_voi'],Q(1,2))
        self.assertEqual(decisions(v,Q(0))['voi_decision'],'CONTINUE')

    def test_exact_value_tie_is_stop_despite_positive_premium(self):
        v=exact_values(Q(19,20),Q(1),Q(1),Q(0),Q(1,20))
        self.assertEqual(v['net_voi'],0)
        for eps in (Q(0),Q(1,10**12)):
            d=decisions(v,eps)
            self.assertEqual(d['voi_decision'],'STOP')
            self.assertEqual(d['premium_decision'],'CONTINUE')
            self.assertFalse(d['premium_dominated_wait'])

    def test_declared_tolerance_is_distinct_from_strict_zero(self):
        v=exact_values(Q(1,2),Q(1),Q(1),Q(0),Q(1,2)-Q(1,10**13))
        self.assertEqual(decisions(v,Q(0))['voi_decision'],'CONTINUE')
        self.assertEqual(decisions(v,Q(1,10**12))['voi_decision'],'STOP')

if __name__=='__main__':unittest.main()
