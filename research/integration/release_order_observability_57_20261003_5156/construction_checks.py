"""Literal construction checks; does not invoke the primary matrix CLI."""
from copy import deepcopy
import unittest
import audit
import candidate

def case(press,release,order='time'):
    events=[{'kind':'press','ns':press,'key':'A'},{'kind':'release','ns':release,'key':'A'}]
    if press!=release:events.sort(key=lambda e:e['ns'])
    elif order=='release-press':events.reverse()
    return {'case_id':'literal','ended_ns':700,'press_ns':press,'release_ns':release,
        'tie_order':order,'events':[dict(seq=i+1,**e) for i,e in enumerate([{'kind':'start','ns':100},*events,{'kind':'end','ns':700}])]}

class ConstructionTests(unittest.TestCase):
    def test_literal_projection_collision_preserves_opposite_states(self):
        safe=candidate.row(case(200,400));unsafe=candidate.row(case(600,400))
        self.assertTrue(audit.equal_json(safe['projection'],unsafe['projection']))
        self.assertEqual(safe['terminal_keys_down'],[]);self.assertEqual(unsafe['terminal_keys_down'],['A'])
        self.assertTrue(safe['kernel_outcome']['release_verified']);self.assertTrue(unsafe['kernel_outcome']['release_verified'])
    def test_end_floor_refuses_safe_bookkeeping_tail(self):
        row=candidate.row(case(200,400))
        self.assertFalse(row['comparators']['end_floor']);self.assertTrue(row['comparators']['ordered_witness'])
    def test_equal_timestamp_explicit_orders_remain_distinct(self):
        a=audit.reduce_events(case(400,400,'press-release')['events'])
        b=audit.reduce_events(case(400,400,'release-press')['events'])
        self.assertEqual(a['terminal_keys_down'],[]);self.assertEqual(b['terminal_keys_down'],['A'])
    def test_reducer_rejects_type_sequence_and_missing_events(self):
        original=case(200,400)['events']
        for name in ('bool-seq','float-time','missing'):
            with self.subTest(name=name):
                events=deepcopy(original)
                if name=='bool-seq':events[0]['seq']=True
                elif name=='float-time':events[0]['ns']=100.0
                else:events.pop()
                with self.assertRaises(ValueError):audit.reduce_events(events)
    def test_signature_distinguishes_json_scalar_types(self):
        self.assertFalse(audit.equal_json({'n':1},{'n':True}))
        self.assertFalse(audit.equal_json({'n':1},{'n':1.0}))
        self.assertTrue(audit.equal_json({'a':1,'b':False},{'b':False,'a':1}))

if __name__=='__main__':unittest.main()
