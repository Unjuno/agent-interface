"""Construction only; formal corpus is not executed by this test."""
import unittest
from model import simulate

class ContractTests(unittest.TestCase):
    def test_two_independent_equivalent_producers_are_one_effect(self):
        p=dict(session='s', producer='a', retry_intent='ra', attempt='a1', common_work_id='w', revision=1, generation=1, target='save', incarnation=1, operation='click', opportunity='save-once', params={'value':1}, deadline=10, authorized=True, identity='exact')
        q=dict(p,producer='b',retry_intent='rb',attempt='b1')
        events=[dict(kind='proposal',now=1,proposal=p),dict(kind='proposal',now=1,proposal=q)]
        r=simulate('SEMANTIC',events)
        self.assertEqual(sum(x['effect'] for x in r['decisions']),1)
        self.assertEqual(r['neutral'],True)
        self.assertEqual(r['authority_created'],0)

if __name__ == '__main__': unittest.main()
