import asyncio
import unittest
from candidate import run_case

class Construction(unittest.TestCase):
    def test_mini_direct_cascades(self):
        row=asyncio.run(run_case('direct','cancel_first',2))
        self.assertEqual([o['status'] for o in row['outcomes']],['CANCELLED','CANCELLED'])
    def test_mini_shield_preserves_other_waiter(self):
        row=asyncio.run(run_case('shield','cancel_first',2))
        self.assertEqual([o['status'] for o in row['outcomes']],['CANCELLED','DELIVERED'])
    def test_mini_owned_cleanup(self):
        row=asyncio.run(run_case('shield_refcount','cancel_all',2))
        self.assertTrue(all(s['done'] for s in row['before_cleanup']))
        self.assertTrue(all(s['done'] for s in row['after_cleanup']))
    def test_mini_local_freshness(self):
        row=asyncio.run(run_case('shield','generation_change',2))
        self.assertEqual([o['status'] for o in row['outcomes']],['STALE','STALE'])
    def test_mini_owner_error(self):
        row=asyncio.run(run_case('shield','owner_failure',2))
        self.assertEqual([o['status'] for o in row['outcomes']],['OWNER_FAILED','OWNER_FAILED'])

if __name__=='__main__':unittest.main()
