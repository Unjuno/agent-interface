import copy
import unittest
from focus_ack import acknowledgement_errors


class AcknowledgementGateTests(unittest.TestCase):
    def setUp(self):
        self.binding = {'token':'new:row-0','pid':17,'target_id':42,
                        'ready_ns':100,'click_started_ns':200}
        self.ack = {'schema':'issue5260-a05-focus-ack-v1', 'token':'new:row-0',
                    'pid':17,'target_id':42,'widget':'target',
                    'focus_get':'target','event_ns':220,'written_ns':230,
                    'sequence':3}
        self.state = {'token':'new:row-0','pid':17,'target_id':42,
                      'widget':'target','sequence':3,'event_ns':220}

    def errors(self, ack=None, state=None, now=240):
        return acknowledgement_errors(self.ack if ack is None else ack,
            self.state if state is None else state, self.binding, now, 50)

    def test_valid_fresh_ack(self):
        self.assertEqual(self.errors(), [])

    def test_identity_adversaries(self):
        for field, value in [('token','old:row-0'),('pid',18),('target_id',43),
                             ('widget','decoy'),('focus_get','decoy'),
                             ('schema','wrong')]:
            ack=copy.deepcopy(self.ack); ack[field]=value
            with self.subTest(field=field): self.assertTrue(self.errors(ack))

    def test_preclick_future_and_expired_ack(self):
        for field,value in [('event_ns',199),('written_ns',219),
                            ('written_ns',241),('event_ns',True),
                            ('sequence',True)]:
            ack=copy.deepcopy(self.ack); ack[field]=value
            with self.subTest(field=field,value=value): self.assertTrue(self.errors(ack))
        self.assertTrue(self.errors(now=50_000_231))

    def test_focus_out_or_newer_state_invalidates_ack(self):
        for field,value in [('widget','decoy'),('sequence',4),
                            ('event_ns',221),('pid',18),('target_id',43),
                            ('token','old:row-0')]:
            state=copy.deepcopy(self.state); state[field]=value
            with self.subTest(field=field): self.assertTrue(self.errors(state=state))

    def test_missing_or_malformed_receipts_fail_closed(self):
        for value in ({},None,[],{'sequence':True}):
            self.assertTrue(acknowledgement_errors(value,self.state,self.binding,240,50))
            self.assertTrue(acknowledgement_errors(self.ack,value,self.binding,240,50))

    def test_boolean_clock_binding_not_accepted(self):
        for name in ('pid','target_id','ready_ns','click_started_ns'):
            binding=copy.deepcopy(self.binding); binding[name]=True
            self.assertTrue(acknowledgement_errors(self.ack,self.state,binding,240,50))


if __name__ == '__main__': unittest.main()
