import unittest
from model import Policy, Observation, Context, decide

class Tests(unittest.TestCase):
    def base(self):
        o=Observation('book',7,3,10,1000)
        c=Context(7,3,10,10,1050,100)
        return o,c
    def test_fresh(self):
        o,c=self.base(); d=decide(Policy.BOUND_PREFIX,'bookkeeper',o,c); self.assertTrue(d.accepted); self.assertEqual(d.text,'keeper')
    def test_content_only_ignores_binding(self):
        o,c=self.base(); c=Context(8,4,99,88,999999,100); self.assertTrue(decide(Policy.CONTENT_ONLY,'bookkeeper',o,c).accepted)
    def test_stale_sequence(self):
        o,c=self.base(); c=Context(8,3,10,10,1050,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'stale_sequence')
    def test_stale_binding(self):
        o,c=self.base(); c=Context(7,4,10,10,1050,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'stale_binding')
    def test_wrong_target(self):
        o,c=self.base(); c=Context(7,3,11,11,1050,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'wrong_target')
    def test_expired_age(self):
        o,c=self.base(); c=Context(7,3,10,10,1200,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'stale_age')
    def test_future_observation_refused(self):
        o,c=self.base(); c=Context(7,3,10,10,900,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'stale_age')
    def test_focus(self):
        o,c=self.base(); c=Context(7,3,10,11,1050,100); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'focus_mismatch')
    def test_nonprefix_first(self):
        o,c=self.base(); o=Observation('boox',7,3,10,1000); self.assertEqual(decide(Policy.BOUND_PREFIX,'bookkeeper',o,c).reason,'observed_not_prefix')

if __name__=='__main__': unittest.main()
