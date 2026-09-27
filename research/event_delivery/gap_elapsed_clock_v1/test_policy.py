import unittest
from gap_policy import GapPolicy, BUDGET_NS

class PolicyTests(unittest.TestCase):
    def test_count_third_and_sticky(self):
        p=GapPolicy('OBS_COUNT_3'); key=[4,5,'E5']
        self.assertEqual([p.observe(key,i)['status'] for i in range(3)],
                         ['EVENT_PREDECESSOR_MISSING']*2+['RESYNC_REQUIRED'])
        before=p.observe(key,3); after=p.observe(key,1_000_000)
        self.assertEqual(before,after)
    def test_elapsed_boundary(self):
        p=GapPolicy('ELAPSED_80MS'); key=[4,5,'E5']
        self.assertEqual(p.observe(key,10)['status'],'EVENT_PREDECESSOR_MISSING')
        self.assertEqual(p.observe(key,10+BUDGET_NS-1)['status'],'EVENT_PREDECESSOR_MISSING')
        self.assertEqual(p.observe(key,10+BUDGET_NS)['status'],'RESYNC_REQUIRED')
    def test_fast_poll_does_not_advance_time(self):
        p=GapPolicy('ELAPSED_80MS')
        for i in range(100): self.assertEqual(p.observe([4,5,'E5'],i)['status'],'EVENT_PREDECESSOR_MISSING')
    def test_first_observation_after_pause(self):
        p=GapPolicy('ELAPSED_80MS'); p.observe([4,5,'E5'],0)
        self.assertEqual(p.observe([4,5,'E5'],140_000_000)['status'],'RESYNC_REQUIRED')
    def test_new_identity_resets(self):
        for policy in ('OBS_COUNT_3','ELAPSED_80MS'):
            p=GapPolicy(policy)
            for t in (0,40_000_000,100_000_000):p.observe([4,5,'E5'],t)
            r=p.observe([6,7,'E7'],120_000_000)
            self.assertEqual(r['status'],'EVENT_PREDECESSOR_MISSING'); self.assertEqual(r['state']['count'],1)
            self.assertEqual(r['state']['first_ns'],120_000_000)
    def test_clear_resets(self):
        p=GapPolicy('ELAPSED_80MS');p.observe([4,5,'E5'],0);p.clear()
        self.assertEqual(p.observe([4,5,'E5'],200_000_000)['status'],'EVENT_PREDECESSOR_MISSING')
    def test_clock_reject(self):
        p=GapPolicy('ELAPSED_80MS');p.observe([4,5,'E5'],10)
        for value in (True, -1,9):
            with self.assertRaises(ValueError):p.observe([4,5,'E5'],value)
    def test_no_authority(self):
        p=GapPolicy('ELAPSED_80MS');p.observe([4,5,'E5'],0)
        self.assertIs(p.observe([4,5,'E5'],BUDGET_NS)['state']['receipt']['authority'],False)

if __name__=='__main__':unittest.main(verbosity=2)
