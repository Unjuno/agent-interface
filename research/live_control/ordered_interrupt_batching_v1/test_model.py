import unittest
from model import *
from cases import E,directed_cases

class TestModel(unittest.TestCase):
    def test_flatten_identity(self):
        for xs in directed_cases().values():
            self.assertEqual(flatten(ordered_batch(xs)),[e.to_dict() for e in xs])
    def test_batch_boundary(self):
        bs=ordered_batch(directed_cases()['batch_boundary'])
        self.assertEqual([len(b['events']) for b in bs],[4,1])
    def test_metadata(self):
        b=ordered_batch(directed_cases()['metadata'])[0]
        self.assertEqual(b['highest_priority'],3)
        self.assertEqual((b['first_arrival'],b['last_arrival']),(10,18))
        self.assertEqual(b['sessions'],['A','B'])
        self.assertFalse(b['input_authority']); self.assertFalse(b['semantic_authority']); self.assertIsNone(b['resolution_claim'])
    def test_priority_negative_reverses(self):
        for name in ['causal_pair','critical_pair','goal_terminal']:
            xs=directed_cases()[name]
            got=[x['record_id'] for x in flatten(priority_sorted_batch(xs))]
            ref=[e.record_id for e in xs]
            self.assertNotEqual(got,ref)
    def test_session_projection(self):
        xs=directed_cases()['mixed_sessions']; got=flatten(ordered_batch(xs))
        for s in ['A','B']:
            self.assertEqual([e.record_id for e in xs if e.session==s],[e['record_id'] for e in got if e['session']==s])
    def test_duplicate_rejected(self):
        x=E(0,'A','PROGRESS'); self.assertRaisesRegex(ValueError,'duplicate',ordered_batch,[x,x])
    def test_nonmonotonic_rejected(self):
        a=E(0,'A','PROGRESS'); b=Event('r1','A',0,1,'PROGRESS',1,'ev1')
        self.assertRaisesRegex(ValueError,'nonmonotonic',ordered_batch,[a,b])
    def test_bad_priority_rejected(self):
        x=Event('r0','A',0,0,'PROGRESS',4,'ev0'); self.assertRaisesRegex(ValueError,'priority',ordered_batch,[x])
    def test_bad_kind_rejected(self):
        x=Event('r0','A',0,0,'BOGUS',1,'ev0'); self.assertRaisesRegex(ValueError,'kind',ordered_batch,[x])
    def test_bad_batch_size_rejected(self):
        self.assertRaisesRegex(ValueError,'batch_size',ordered_batch,[],0)

if __name__=='__main__': unittest.main()
