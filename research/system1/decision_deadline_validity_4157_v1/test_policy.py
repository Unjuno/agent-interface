import unittest
from policy import decide

BASE={'policy':'EXISTING_CURRENTNESS_ONLY','scope':'decision-deadline-v1','observation_id':'o','expected_observation_id':'o','epoch':7,'expected_epoch':7,'observation_available_ns':100,'proposal_ready_ns':150,'decision_deadline_ns':180,'lease_valid_until_ns':500,'freshness_budget_ns':400,'proposal':'TURN_LEFT'}
class T(unittest.TestCase):
    def test_currentness_admits(self): self.assertEqual(decide(dict(BASE))['decision'],'ADMIT')
    def test_deadline_on_time(self):
        p=dict(BASE,policy='EXPLICIT_DECISION_DEADLINE'); self.assertEqual(decide(p)['decision'],'ADMIT')
    def test_deadline_late(self):
        p=dict(BASE,policy='EXPLICIT_DECISION_DEADLINE',proposal_ready_ns=181); self.assertEqual(decide(p)['decision'],'REFUSE_DECISION_DEADLINE')
    def test_lease(self):
        p=dict(BASE,proposal_ready_ns=501); self.assertEqual(decide(p)['decision'],'REFUSE_LEASE')
    def test_freshness(self):
        p=dict(BASE,proposal_ready_ns=501,lease_valid_until_ns=1000); self.assertEqual(decide(p)['decision'],'REFUSE_FRESHNESS')
    def test_epoch(self):
        p=dict(BASE,epoch=8); self.assertEqual(decide(p)['decision'],'REFUSE_EPOCH')
    def test_observation(self):
        p=dict(BASE,observation_id='x'); self.assertEqual(decide(p)['decision'],'REFUSE_OBSERVATION')
    def test_bool_rejected(self):
        p=dict(BASE,epoch=True); self.assertEqual(decide(p)['decision'],'REFUSE_MALFORMED')
if __name__=='__main__': unittest.main()
