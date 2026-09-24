import unittest
from actors import packet, refund_allowed

class Contract(unittest.TestCase):
    def test_absent_is_not_terminal(self):
        p=packet('test','c1','CUE');r=dict(p,state='ABSENT')
        self.assertTrue(refund_allowed('QUERY_ABSENT',p,r))
        self.assertFalse(refund_allowed('SEAL_ABSENT',p,r))
    def test_canceled(self):
        p=packet('test','c1','CUE')
        self.assertTrue(refund_allowed('SEAL_ABSENT',p,dict(p,state='CANCELED')))
    def test_received(self):
        p=packet('test','c1','CUE')
        for a in ('HOLD','QUERY_ABSENT','SEAL_ABSENT'):
            self.assertFalse(refund_allowed(a,p,dict(p,state='RECEIVED')))
    def test_no_reply(self):
        self.assertFalse(refund_allowed('SEAL_ABSENT',packet('x','c1','CUE'),None))
    def test_identity_fields(self):
        p=packet('test','c1','CUE')
        for key in p:
            r=dict(p,state='CANCELED');r[key]='other'
            self.assertFalse(refund_allowed('SEAL_ABSENT',p,r))
    def test_unknown_enum(self):
        p=packet('test','c1','CUE')
        self.assertFalse(refund_allowed('SEAL_ABSENT',p,dict(p,state='unknown')))

if __name__=='__main__':unittest.main(verbosity=2)
