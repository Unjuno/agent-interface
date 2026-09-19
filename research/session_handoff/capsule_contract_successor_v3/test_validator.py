import unittest
from .validator import validate

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.c={'session_id':'s1','task_id':'t1','capsule_id':'c1','uncertainty':['u'],'replay_prohibited':True,'authority_transfer':False,'authority_status':'REQUIRE_FRESH','expires_at':100,'contradictory':False,'semantic_status':'PARTIAL'}
    def check(self,key,value,reason):
        c=dict(self.c); c[key]=value; d=validate(c,session_id='s1',task_id='t1',now_epoch=10); self.assertEqual((d.usable,d.reason),(False,reason))
    def test_valid_advisory_capsule(self):
        d=validate(self.c,session_id='s1',task_id='t1',now_epoch=10); self.assertEqual((d.usable,d.reason,d.requires_fresh_authority),(True,'advisory_context_only',True))
    def test_identity_and_expiry(self):
        for x in (('session_id','s2','session_mismatch'),('task_id','t2','task_mismatch'),('expires_at',10,'expired')): self.check(*x)
    def test_authority_replay_and_contradiction(self):
        for x in (('authority_transfer',True,'authority_transfer_forbidden'),('authority_status','GRANTED','fresh_authority_required'),('replay_prohibited',False,'replay_not_prohibited'),('contradictory',True,'contradictory')): self.check(*x)
    def test_malformed_and_missing_fields(self):
        self.assertEqual(validate(None,session_id='s1',task_id='t1',now_epoch=10).reason,'malformed')
        for key,reason in (('capsule_id','missing_capsule_id'),('uncertainty','missing_uncertainty'),('expires_at','missing_expiry')):
            c=dict(self.c); c.pop(key); self.assertEqual(validate(c,session_id='s1',task_id='t1',now_epoch=10).reason,reason)
    def test_bool_expiry_is_rejected(self): self.check('expires_at',True,'missing_expiry')
    def test_invalid_semantic_status(self): self.check('semantic_status','COMPLETED','invalid_semantic_status')
    def test_authority_fields_are_never_accepted(self):
        c=dict(self.c); c['authority_token']='live-token'; d=validate(c,session_id='s1',task_id='t1',now_epoch=10); self.assertTrue(d.usable); self.assertTrue(d.requires_fresh_authority)
    def test_unknown_semantics_stay_advisory(self):
        c=dict(self.c); c['semantic_status']='UNKNOWN'; self.assertTrue(validate(c,session_id='s1',task_id='t1',now_epoch=10).usable)

if __name__ == '__main__': unittest.main()
