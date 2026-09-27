import copy,unittest
from policy import decide
class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.expected={'session':'opaque','surface':11,'target':13,'geometry':{'x':1,'y':2,'width':30,'height':10}}
        self.receipt=dict(self.expected,sequence=1,captured_ns=42,hit=13,focus=13)
    def test_clear_positives(self):
        for p in ('CLICK_THEN_TYPE','POST_FOCUS','HIT_AND_FOCUS'):
            for phase in ('click','type'):self.assertTrue(decide(p,phase,self.expected,self.receipt)['allow'])
    def test_hit_then_focus(self):
        r=dict(self.receipt,hit=17,focus=19)
        self.assertFalse(decide('HIT_AND_FOCUS','click',self.expected,r)['allow'])
        self.assertTrue(decide('POST_FOCUS','click',self.expected,r)['allow'])
        for p in ('POST_FOCUS','HIT_AND_FOCUS'):self.assertFalse(decide(p,'type',self.expected,r)['allow'])
    def test_changed_session(self):
        self.assertFalse(decide('HIT_AND_FOCUS','click',self.expected,dict(self.receipt,session='foreign'))['allow'])
    def test_no_scenario_input(self):
        self.assertFalse(decide('HIT_AND_FOCUS','click',self.expected,dict(self.receipt,scenario='CLEAR'))['allow'])
    def test_bool_ids(self):
        for key in ('target','surface','sequence','captured_ns'):
            self.assertFalse(decide('HIT_AND_FOCUS','click',self.expected,dict(self.receipt,**{key:True}))['allow'])
    def test_bool_hit_focus(self):
        self.assertFalse(decide('HIT_AND_FOCUS','click',self.expected,dict(self.receipt,hit=True))['allow'])
        self.assertFalse(decide('HIT_AND_FOCUS','type',self.expected,dict(self.receipt,focus=True))['allow'])
    def test_control(self):
        for phase in ('click','type'):self.assertFalse(decide('NO_TASK_INPUT',phase,self.expected,self.receipt)['allow'])
if __name__=='__main__':unittest.main()
