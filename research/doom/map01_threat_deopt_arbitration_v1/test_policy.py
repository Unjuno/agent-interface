import unittest
from policy import latest_ready, authority_guarded

class TestPolicy(unittest.TestCase):
    def setUp(self):
        self.lease = {"authority_id":"T1","resource":"locomotion","active":True,"valid_context":True,"start_tick":0,"end_tick":20}
        self.threat = {"proposal_id":"t","resource":"locomotion","source":"threat","authority_id":"T1","action":"strafe_left","proposed_at":10,"ready":True}
        self.deopt = {"proposal_id":"d","resource":"locomotion","source":"deopt","authority_id":None,"action":"turn_right_6x","proposed_at":11,"ready":True}

    def test_latest_can_override(self):
        out=latest_ready([self.threat,self.deopt],[self.lease],12)
        self.assertEqual(out['selected']['locomotion']['source'],'deopt')

    def test_guard_preserves_threat(self):
        out=authority_guarded([self.threat,self.deopt],[self.lease],12)
        self.assertEqual(out['selected']['locomotion']['source'],'threat')
        self.assertEqual(len(out['deferred']),1)

    def test_guard_holds_when_threat_command_missing(self):
        out=authority_guarded([self.deopt],[self.lease],12)
        self.assertNotIn('locomotion',out['selected'])

    def test_expired_allows_deopt(self):
        out=authority_guarded([self.deopt],[{**self.lease,"end_tick":10}],12)
        self.assertEqual(out['selected']['locomotion']['source'],'deopt')

    def test_invalid_context_allows_deopt(self):
        out=authority_guarded([self.deopt],[{**self.lease,"valid_context":False}],12)
        self.assertEqual(out['selected']['locomotion']['source'],'deopt')

    def test_nonoverlap_preserves_both(self):
        fire_lease={**self.lease,"resource":"fire"}
        fire={**self.threat,"resource":"fire","action":"fire"}
        out=authority_guarded([fire,self.deopt],[fire_lease],12)
        self.assertEqual(set(out['selected']),{'fire','locomotion'})
        self.assertEqual(out['selected']['fire']['source'],'threat')
        self.assertEqual(out['selected']['locomotion']['source'],'deopt')

if __name__=='__main__': unittest.main()
