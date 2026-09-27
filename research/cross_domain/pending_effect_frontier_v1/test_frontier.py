import itertools
import unittest
from frontier import Effects, Frontier, matching_commit

F = frozenset
EMPTY = Effects(F(), F())


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.f = Frontier('epoch', 1, {'a':'A','alias':'A','b':'B','c':'C'})
    def advice(self, candidate, pending, **kw):
        args = dict(epoch='epoch', catalogue_version=1, physical_empty=True); args.update(kw)
        return self.f.advise(candidate, pending, **args)
    def test_independent_writes(self):
        self.assertTrue(self.advice(Effects(F(),F(['b'])), {'A':Effects(F(),F(['a']))})['eligible'])
    def test_read_after_write_blocked(self):
        self.assertFalse(self.advice(Effects(F(['a']),F()), {'A':Effects(F(),F(['a']))})['eligible'])
    def test_write_after_read_blocked(self):
        self.assertFalse(self.advice(Effects(F(),F(['a'])), {'A':Effects(F(['a']),F())})['eligible'])
    def test_write_write_blocked(self):
        self.assertFalse(self.advice(Effects(F(),F(['a'])), {'A':Effects(F(),F(['a']))})['eligible'])
    def test_read_read_allowed(self):
        self.assertTrue(self.advice(Effects(F(['a']),F()), {'A':Effects(F(['a']),F())})['eligible'])
    def test_alias_requires_canonical_identity(self):
        candidate, pending = Effects(F(['alias']),F()), {'A':Effects(F(),F(['a']))}
        self.assertFalse(self.advice(candidate,pending)['eligible'])
        self.assertTrue(self.advice(candidate,pending,raw_names=True)['eligible'])
    def test_unknown_pending_blocks_all(self):
        self.assertFalse(self.advice(EMPTY, {'A':Effects(None,None)})['eligible'])
    def test_unknown_candidate_blocked(self):
        self.assertFalse(self.advice(Effects(None,None), {'A':EMPTY})['eligible'])
    def test_unresolved_identity_blocked(self):
        self.assertFalse(self.advice(Effects(F(['missing']),F()), {'A':EMPTY})['eligible'])
    def test_no_pending_allows_serial_unknown(self):
        self.assertTrue(self.advice(Effects(None,None), {})['eligible'])
    def test_epoch_change_fails(self):
        self.assertFalse(self.advice(EMPTY, {}, epoch='new')['eligible'])
    def test_catalogue_revision_change_fails(self):
        self.assertFalse(self.advice(EMPTY, {}, catalogue_version=2)['eligible'])
    def test_bool_revision_not_an_integer_version(self):
        self.assertFalse(self.advice(EMPTY, {}, catalogue_version=True)['eligible'])
    def test_nonempty_input_blocks_even_independent(self):
        self.assertFalse(self.advice(EMPTY, {}, physical_empty=False)['eligible'])
    def test_truthy_input_flag_not_accepted(self):
        self.assertFalse(self.advice(EMPTY, {}, physical_empty=1)['eligible'])
    def test_advice_never_grants_authority(self):
        self.assertIs(self.advice(EMPTY,{})['grants_input_authority'],False)
    def test_malformed_effects(self):
        with self.assertRaises(ValueError): Effects(['a'],F())
    def test_empty_identity_rejected(self):
        with self.assertRaises(ValueError): Frontier('epoch',1,{'a':''})
    def test_all_4096_effect_pairs(self):
        names = ('a','b','c')
        subsets = [F(n for n,b in zip(names,bits) if b) for bits in itertools.product((0,1),repeat=3)]
        effects = [Effects(r,w) for r,w in itertools.product(subsets,repeat=2)]
        checked=0; commuting=0
        def apply(state,e,constant):
            value=sum(state[n] for n in e.reads)+constant
            updated=dict(state)
            for n in e.writes: updated[n]=value
            return updated,value
        for p,c in itertools.product(effects,repeat=2):
            checked+=1
            allowed=not ((p.writes & (c.reads|c.writes)) or (c.writes & (p.reads|p.writes)))
            self.assertIs(self.advice(c,{'p':p})['eligible'],allowed)
            if allowed:
                state={'a':2,'b':3,'c':5}
                t,pv=apply(state,p,7);t,cv=apply(t,c,11)
                u,cv2=apply(state,c,11);u,pv2=apply(u,p,7)
                self.assertEqual((t,pv,cv),(u,pv2,cv2));commuting+=1
        self.assertEqual(checked,4096)
        self.assertGreater(commuting,0)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.row=dict(epoch='e',operation='A',payload_sha256='h',kind='ack',status='COMMITTED',
                      durable_ns=20,published_ns=25,effect_rowid=1)
    def ok(self):
        return matching_commit(self.row,epoch='e',operation='A',payload_hash='h',issued_ns=10,observed_ns=30)
    def test_valid_ack(self): self.assertTrue(self.ok())
    def test_valid_lookup(self): self.row['kind']='lookup'; self.assertTrue(self.ok())
    def test_lookup_absence_is_not_no_effect(self): self.row['status']='UNKNOWN'; self.assertFalse(self.ok())
    def test_foreign_epoch(self): self.row['epoch']='x'; self.assertFalse(self.ok())
    def test_foreign_operation(self): self.row['operation']='B'; self.assertFalse(self.ok())
    def test_wrong_payload(self): self.row['payload_sha256']='wrong'; self.assertFalse(self.ok())
    def test_future_receipt(self): self.row['published_ns']=31; self.assertFalse(self.ok())
    def test_predates_request(self): self.row['durable_ns']=9; self.assertFalse(self.ok())
    def test_bool_effect_identity(self): self.row['effect_rowid']=True; self.assertFalse(self.ok())
    def test_untrusted_receipt_kind(self): self.row['kind']='guess'; self.assertFalse(self.ok())
    def test_inverted_commit_publish(self): self.row['durable_ns']=26; self.assertFalse(self.ok())


if __name__=='__main__': unittest.main(verbosity=2)
